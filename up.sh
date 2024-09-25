#!/bin/bash

cd $(dirname $0)
pwd

# install docker
# Detect Linux distribution and install Docker if not already installed
if ! command -v docker &> /dev/null; then
  if [ "$(id -u)" != "0" ]; then
    echo "Must be run as root to install Docker" 1>&2
    exit 1
  fi
  if [ -f /etc/os-release ]; then
    . /etc/os-release
    case "$ID" in
      ubuntu|debian)
        apt-get update
        apt-get install -y apt-transport-https ca-certificates curl software-properties-common
        curl -fsSL https://download.docker.com/linux/$ID/gpg | apt-key add -
        add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/$ID $(lsb_release -cs) stable"
        apt-get update
        apt-get install -y docker-ce docker-ce-cli containerd.io
        ;;
      centos|rhel|fedora)
        yum install -y yum-utils
        yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
        yum install -y docker-ce docker-ce-cli containerd.io
        ;;
      *)
        echo "Unsupported distribution: $ID"
        exit 1
        ;;
    esac

    # Start and enable Docker service
    systemctl start docker
    systemctl enable docker

    # Install Docker Compose
    if ! command -v docker-compose &> /dev/null; then
      curl -L "https://github.com/docker/compose/releases/download/1.29.2/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
      chmod +x /usr/local/bin/docker-compose
    fi
  else
    echo "Cannot detect Linux distribution"
    exit 1
  fi
fi


docker compose up -d

sleep 2s

docker compose ps

docker compose logs --tail=10

echo "done"
