use serde::{Deserialize, Serialize};
use sqlx::types::chrono;
use sqlx::{postgres::PgPoolOptions, Pool, Postgres};
use std::collections::HashMap;
use std::sync::Arc;
use tokio::sync::{mpsc, RwLock};
use warp::ws::{Message, WebSocket};
use warp::Filter;
use futures_util::{SinkExt, StreamExt};
use log::{error, info, warn};
use std::error::Error;

#[derive(Debug, Deserialize)]
struct InitMessage {
    cmd: String,
    token: String,
}

#[derive(Debug, Serialize)]
struct ResponseMessage {
    cmd: String,
    code: String,
    session_id: Option<String>,
    #[serde(flatten)]
    extra: HashMap<String, serde_json::Value>,
}

#[derive(Debug, Deserialize)]
struct IncomingMessage {
    cmd: String,
    #[serde(flatten)]
    extra: HashMap<String, serde_json::Value>,
}

type Rooms = Arc<RwLock<HashMap<String, Room>>>;

struct Room {
    clients: HashMap<String, mpsc::UnboundedSender<Result<Message, warp::Error>>>,
    session_id: String,
}

#[tokio::main]
async fn main() {
    if std::env::var("RUST_LOG").is_err() {
        std::env::set_var("RUST_LOG", "error,websocket_server=debug");
    }

    env_logger::init();

    let database_url = std::env::var("DATABASE_URL")
        .expect("DATABASE_URL must be set");

    let pool = PgPoolOptions::new()
        .connect(&database_url)
        .await
        .expect("Failed to connect to the database");

    let rooms: Rooms = Arc::new(RwLock::new(HashMap::new()));

    let ws_route = warp::path("websocket")
        .and(warp::ws())
        .and(with_db(pool.clone()))
        .and(with_rooms(rooms.clone()))
        .map(|ws: warp::ws::Ws, db, rooms| {
            ws.on_upgrade(move |socket| handle_connection(socket, db, rooms))
        });

    log::info!("Starting server on 0.0.0.0:8765");
    warp::serve(ws_route)
        .run(([0, 0, 0, 0], 8765))
        .await;
}

// Warp filter to pass database connection pool to the request handler
fn with_db(
    pool: Pool<Postgres>,
) -> impl Filter<Extract = (Pool<Postgres>,), Error = std::convert::Infallible> + Clone {
    warp::any().map(move || pool.clone())
}

// Warp filter to pass rooms state to the request handler
fn with_rooms(
    rooms: Rooms,
) -> impl Filter<Extract = (Rooms,), Error = std::convert::Infallible> + Clone {
    warp::any().map(move || rooms.clone())
}

// Handles a new websocket connection
async fn handle_connection(ws: WebSocket, db: Pool<Postgres>, rooms: Rooms) {
    // rx->client_tx->client_rx->tx
    let (mut tx, mut rx) = ws.split();
    let (client_tx, mut client_rx) = mpsc::unbounded_channel();
    let established = Arc::new(RwLock::new(true));


    // Spawn a task to send messages to the client
    let estab = established.clone();
    tokio::task::spawn(async move {
        let mut interval = tokio::time::interval(tokio::time::Duration::from_secs(20));
        loop {
            tokio::select! {
                Some(Ok(msg)) = client_rx.recv() => {
                    info!("Sending message: {:?}", msg);
                    if let Err(e) = tx.send(msg).await {
                        error!("Failed to send message to client: {}", e);
                    }
                }
                _ = interval.tick() => {
                    let heartbeat = ResponseMessage {
                        cmd: "Heartbeat".to_string(),
                        code: "1".to_string(),
                        session_id: None,
                        extra: HashMap::new(),
                    };
                    let heartbeat_json = serde_json::to_string(&heartbeat).unwrap();
                    info!("Sending heartbeat: {}", heartbeat_json);
                    if let Err(e) = tx.send(Message::text(heartbeat_json)).await {
                        warn!("Failed to send heartbeat to client: {}", e);
                    }
                }
                v = estab.read() => {
                    if !*v {
                        info!("Connection disconnected");
                        break;
                    }
                }
            }
        }
        info!("Connection disconnected, receiving task exited");
    });

    let mut client_id = String::new();
    let mut room_name = String::new();

    // Process incoming messages from the client
    while let Some(result) = rx.next().await {
        match result {
            Ok(message) => {
                if let Ok(text) = message.to_str() {
                    info!("Received message: {}", text);
                    if client_id.is_empty() {
                        // Handle the initial message to set up the connection
                        match handle_initial_message(text, &db, &client_tx, &rooms).await {
                            Ok((token, new_client_id, session_id)) => {
                                client_id = new_client_id;
                                room_name = token;
                                send_init_response(&client_tx, session_id).await;
                            }
                            Err(e) => {
                                error!("Error initializing connection: {}", e);
                                break;
                            }
                        }
                    } else {
                        // Handle subsequent messages
                        handle_incoming_message(text, &client_id, &room_name, &rooms).await;
                    }
                }
            }
            Err(e) => {
                error!("Error receiving message: {}", e);
                break;
            }
        }
    }

    // Clean up client from room when the connection is closed
    remove_client_from_room(&client_id, &room_name, &rooms).await;
    let mut established_write = established.write().await;
    *established_write = false;
}

// Handles the initial message to set up the connection
async fn handle_initial_message(
    text: &str,
    db: &Pool<Postgres>,
    client_tx: &mpsc::UnboundedSender<Result<Message, warp::Error>>,
    rooms: &Rooms,
) -> Result<(String, String, String), Box<dyn Error + Send + Sync>> {
    let init_message: InitMessage = serde_json::from_str(text)?;
    if init_message.cmd != "init" {
        return Err("Invalid init command".into());
    }

    let token = init_message.token;
    if !check_token_exists(&token, db).await? {
        return Err("Invalid token".into());
    }

    let client_id = uuid::Uuid::new_v4().to_string();
    let session_id;

    {
        let mut rooms_lock = rooms.write().await;
        let room = rooms_lock.entry(token.clone()).or_insert_with(|| Room {
            clients: HashMap::new(),
            session_id: uuid::Uuid::new_v4().to_string(),
        });

        session_id = room.session_id.clone();
        room.clients.insert(client_id.clone(), client_tx.clone());
    }

    Ok((token, client_id, session_id))
}

// Checks if the token exists in the database
async fn check_token_exists(token: &str, db: &Pool<Postgres>) -> Result<bool, sqlx::Error> {
    let now = chrono::Utc::now().naive_utc();
    let result: (i64,) = sqlx::query_as(r#"SELECT COUNT(*) FROM "user" WHERE token = $1 AND (expired_at IS NULL OR expired_at > $2)"#)
        .bind(token)
        .bind(now)
        .fetch_one(db)
        .await?;

    Ok(result.0 > 0)
}

// Sends the initial response message to the client
async fn send_init_response(
    client_tx: &mpsc::UnboundedSender<Result<Message, warp::Error>>,
    session_id: String,
) {
    let response = ResponseMessage {
        cmd: "init".to_string(),
        code: "1".to_string(),
        session_id: Some(session_id),
        extra: HashMap::new(),
    };

    let json_response = serde_json::to_string(&response).unwrap();
    info!("Sending init response: {}", json_response);
    send_message(client_tx, json_response).await;
}

// Handles incoming messages from the client
async fn handle_incoming_message(
    text: &str,
    client_id: &str,
    room_name: &str,
    rooms: &Rooms,
) {
    let incoming_message: IncomingMessage = serde_json::from_str(text).unwrap();
    let cmd = incoming_message.cmd.as_str();

    let mut send_data = true;
    let mut send_self = false;

    // Determine the response based on the command
    let response = match cmd {
        "Heartbeat" => {
            send_self = true;
            Some(ResponseMessage {
                cmd: "Heartbeat".to_string(),
                code: "1".to_string(),
                session_id: None,
                extra: HashMap::new(),
            })
        }
        "checkDevice" => {
            let client_num = {
                let rooms_lock = rooms.read().await;
                rooms_lock.get(room_name).map_or(0, |room| room.clients.len())
            };
            send_self = true;
            Some(ResponseMessage {
                cmd: "checkDevice".to_string(),
                code: if client_num > 1 { "1" } else { "0" }.to_string(),
                session_id: None,
                extra: HashMap::new(),
            })
        }
        "execute" => None,
        "execute_result" => {
            if !incoming_message.extra.contains_key("data") {
                send_data = false;
            }
            None
        }
        _ => None,
    };

    if send_data {
        send_message_to_clients(text, response, client_id, room_name, rooms, send_self).await;
    }
}

// Sends messages to the clients in the room
async fn send_message_to_clients(
    text: &str,
    response: Option<ResponseMessage>,
    client_id: &str,
    room_name: &str,
    rooms: &Rooms,
    send_self: bool,
) {
    let rooms_lock = rooms.read().await;
    if let Some(room) = rooms_lock.get(room_name) {
        for (cid, client) in &room.clients {
            if send_self && cid == client_id {
                if let Some(ref res) = response {
                    let json_response = serde_json::to_string(res).unwrap();
                    info!("Sending message to self: {}", json_response);
                    send_message(client, json_response).await;
                }
            } else if !send_self && cid != client_id {
                if let Some(ref res) = response {
                    let json_response = serde_json::to_string(res).unwrap();
                    info!("Sending message to other clients: {}", json_response);
                    send_message(client, json_response).await;
                } else {
                    info!("Forwarding message to other clients: {}", text);
                    send_message(client, text.to_string()).await;
                }
            }
        }
    }
}

// Sends a message to a client and logs any errors
async fn send_message(
    client: &mpsc::UnboundedSender<Result<Message, warp::Error>>,
    message: String,
) {
    if let Err(e) = client.send(Ok(Message::text(message))) {
        error!("Failed to send message: {}", e);
    }
}

// Removes a client from the room when the connection is closed
async fn remove_client_from_room(client_id: &str, room_name: &str, rooms: &Rooms) {
    let mut rooms_lock = rooms.write().await;
    if let Some(room) = rooms_lock.get_mut(room_name) {
        room.clients.remove(client_id);
        if room.clients.is_empty() {
            rooms_lock.remove(room_name);
        }
    }
}
