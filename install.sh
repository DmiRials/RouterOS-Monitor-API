#!/usr/bin/env sh
set -eu

REPOSITORY="${REPOSITORY:-DmiRials/RouterOS-Monitor-API}"
INSTALL_DIR="${INSTALL_DIR:-$(pwd)/routeros-monitor-api}"
BINARY_NAME="routeros-monitor-api"
ASSET_NAME="routeros-monitor-api-linux-amd64"
RELEASE_TAG="${RELEASE_TAG:-latest}"

fail() {
    printf 'Error: %s\n' "$1" >&2
    exit 1
}

command -v curl >/dev/null 2>&1 || fail "curl is required"

case "$(uname -s)" in
    Linux) ;;
    *) fail "this installer supports Linux only" ;;
esac

case "$(uname -m)" in
    x86_64|amd64) ;;
    *) fail "only Linux amd64/x86_64 is currently supported" ;;
esac

if [ "$RELEASE_TAG" = "latest" ]; then
    DOWNLOAD_URL="https://github.com/${REPOSITORY}/releases/latest/download/${ASSET_NAME}"
else
    DOWNLOAD_URL="https://github.com/${REPOSITORY}/releases/download/${RELEASE_TAG}/${ASSET_NAME}"
fi

mkdir -p "$INSTALL_DIR/logs"

TEMP_BINARY="${INSTALL_DIR}/.${BINARY_NAME}.download"
trap 'rm -f "$TEMP_BINARY"' EXIT INT TERM

printf 'Downloading %s...\n' "$DOWNLOAD_URL"
curl --fail --location --show-error --silent "$DOWNLOAD_URL" --output "$TEMP_BINARY"
chmod 0755 "$TEMP_BINARY"
mv "$TEMP_BINARY" "$INSTALL_DIR/$BINARY_NAME"

if [ ! -f "$INSTALL_DIR/.env" ]; then
    cat > "$INSTALL_DIR/.env" <<'EOF'
BOT_TOKEN=replace-with-telegram-bot-token
CHAT_ID=replace-with-telegram-chat-id

HOST=0.0.0.0
PORT=8000
TOKENS_FILE=tokens.conf

TELEGRAM_TIMEOUT=15
TELEGRAM_SILENT=false
TELEGRAM_MAX_RETRIES=3
TELEGRAM_RETRY_AFTER_MAX=60

QUEUE_MAX_SIZE=1000
STATUS_CACHE_MAX_SIZE=10000
MESSAGE_MAX_LENGTH=3900

LOG_DIR=logs
LOG_LEVEL=INFO

TELEGRAM_PROXY_ENABLED=false
TELEGRAM_PROXY_TYPE=socks5
TELEGRAM_PROXY_HOST=
TELEGRAM_PROXY_PORT=1080
TELEGRAM_PROXY_USER=
TELEGRAM_PROXY_PASSWORD=
EOF
    chmod 0600 "$INSTALL_DIR/.env"
fi

if [ ! -f "$INSTALL_DIR/tokens.conf" ]; then
    cat > "$INSTALL_DIR/tokens.conf" <<'EOF'
# Add one API token per line.
replace-with-api-token
EOF
    chmod 0600 "$INSTALL_DIR/tokens.conf"
fi

cat > "$INSTALL_DIR/run.sh" <<'EOF'
#!/usr/bin/env sh
set -eu
SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
cd "$SCRIPT_DIR"
exec ./routeros-monitor-api
EOF
chmod 0755 "$INSTALL_DIR/run.sh"

cat > "$INSTALL_DIR/routeros-monitor-api.service" <<EOF
[Unit]
Description=RouterOS Monitor API
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
WorkingDirectory=$INSTALL_DIR
ExecStart=$INSTALL_DIR/routeros-monitor-api
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

printf '\nInstalled in: %s\n' "$INSTALL_DIR"
printf 'Configure:    %s/.env and %s/tokens.conf\n' "$INSTALL_DIR" "$INSTALL_DIR"
printf 'Start:        %s/run.sh\n' "$INSTALL_DIR"
printf '\nOptional systemd installation:\n'
printf '  sudo cp "%s/routeros-monitor-api.service" /etc/systemd/system/\n' "$INSTALL_DIR"
printf '  sudo systemctl daemon-reload\n'
printf '  sudo systemctl enable --now routeros-monitor-api\n'
