FROM rust:1.81.0-bookworm AS builder
WORKDIR /app
COPY . .
RUN cargo build --release

FROM debian:bookworm-slim
WORKDIR /app
COPY --from=builder /app/target/x86_64-unknown-linux-gnu/release/websocket_server .
EXPOSE 8765
CMD ["./websocket_server"]
