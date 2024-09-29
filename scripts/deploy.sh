#!/bin/bash
set -e

# Deprecated note
echo "Deprecated, please use containerized deployment solution, refer to docker-compose.yml"
exit 1

cd $(dirname $0)

root_dir=$(cd .. && pwd)
cd $root_dir

host=154.93.104.37
user=root

ssh_cmd="ssh -T $user@$host"
scp_cmd="scp -q"
rsync_cmd="rsync --quiet -avz"

# deploy fsdownload (python project)
cd fsdownload

$ssh_cmd "mkdir -p /root/app/fsdownload || true"
git ls-files | $rsync_cmd --files-from=- ./ "$user@$host:/root/app/fsdownload"

# install python dependencies
$ssh_cmd << EOF
  cd /root/app/fsdownload
  python3 -m venv .venv
  .venv/bin/pip3 install -r requirement.txt
EOF

cd $root_dir

cd websocketrust

cargo build --release

# check if websocket directory exists on remote server, if not create it
$ssh_cmd "mkdir -p /root/app/fsdownload/websocket || true"
$rsync_cmd target/x86_64-unknown-linux-gnu/release/websocket_server "$user@$host:/root/app/fsdownload/websocket/"

cd $root_dir

# check sqlite db file exists on remote server, if not upload from local
# Check if SQLite database file exists on remote server
if ! $ssh_cmd "test -f /root/app/fsdownload/instance/simple.db"; then
  $ssh_cmd "mkdir -p /root/app/fsdownload/instance || true"
  echo "SQLite database file not found on remote server. Uploading from local..."
  $scp_cmd -n fsdownload/instance/simple.db "$user@$host:/root/app/fsdownload/instance/simple.db"
  echo "SQLite database file uploaded successfully."
else
  echo "SQLite database file already exists on remote server."
fi


# restart app
# copy systemd service file
$scp_cmd staff/systemd/*.service "$user@$host:/etc/systemd/system"

# reload systemd and restart apps
$ssh_cmd << EOF
  systemctl daemon-reload
  systemctl restart fsdownload
  systemctl restart websocket
EOF

echo "deploy done"
