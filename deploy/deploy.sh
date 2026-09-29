#!/usr/bin/env bash
# Run ON the Oracle Cloud instance, from the project directory:   bash deploy/deploy.sh
# Idempotent - safe to re-run for every deploy.
#   1. one-time host prep (docker, firewall ports 80/443, swap on small shapes)
#   2. build + start the stack
#   3. if tryravisn.com DNS already points here -> issue Let's Encrypt cert, switch nginx to HTTPS
set -euo pipefail

DOMAIN="tryravisn.com"
DOMAINS=(-d "$DOMAIN" -d "www.$DOMAIN")
CERTBOT_EMAIL="${CERTBOT_EMAIL:-}"   # optional: expiry notices from Let's Encrypt
cd "$(dirname "$0")/.."

log() { printf '\n\033[1;32m==> %s\033[0m\n' "$*"; }

# ---------- 1. host prep ----------
if ! command -v docker >/dev/null 2>&1; then
    log "Installing Docker"
    if command -v apt-get >/dev/null 2>&1; then
        # get.docker.com can lag behind brand-new Ubuntu releases; fall back to Ubuntu's packages.
        if ! curl -fsSL https://get.docker.com | sudo sh; then
            sudo apt-get update
            sudo apt-get install -y docker.io docker-compose-v2 docker-buildx
        fi
    else  # Oracle Linux / RHEL family
        sudo dnf install -y dnf-plugins-core
        sudo dnf config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
        sudo dnf install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
    fi
    sudo systemctl enable --now docker
    sudo usermod -aG docker "$USER"
fi
DOCKER="docker"; docker info >/dev/null 2>&1 || DOCKER="sudo docker"
# `sudo` resets the environment, so hand NGINX_CONF to compose explicitly.
dc() { ${DOCKER%docker} env NGINX_CONF="$NGINX_CONF" docker compose "$@"; }

log "Opening ports 80/443 in the host firewall"
if command -v firewall-cmd >/dev/null 2>&1 && sudo firewall-cmd --state >/dev/null 2>&1; then
    sudo firewall-cmd --permanent --add-service=http --add-service=https >/dev/null
    sudo firewall-cmd --reload >/dev/null
else
    # Oracle's Ubuntu images ship an iptables REJECT-all rule; insert ACCEPTs above it.
    for p in 80 443; do
        if ! sudo iptables -C INPUT -p tcp -m state --state NEW --dport "$p" -j ACCEPT 2>/dev/null; then
            reject_at=$(sudo iptables -L INPUT --line-numbers -n | awk '/REJECT/ {print $1; exit}')
            sudo iptables -I INPUT "${reject_at:-1}" -p tcp -m state --state NEW --dport "$p" -j ACCEPT
        fi
    done
    command -v netfilter-persistent >/dev/null 2>&1 && sudo netfilter-persistent save >/dev/null 2>&1 || true
fi

mem_mb=$(awk '/MemTotal/ {print int($2/1024)}' /proc/meminfo)
if [ "$mem_mb" -lt 3000 ] && ! swapon --show | grep -q .; then
    log "Only ${mem_mb}MB RAM - adding 4G swap so image builds don't OOM"
    sudo fallocate -l 4G /swapfile && sudo chmod 600 /swapfile
    sudo mkswap /swapfile >/dev/null && sudo swapon /swapfile
    grep -q '/swapfile' /etc/fstab || echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab >/dev/null
fi

sudo mkdir -p /var/www/certbot /etc/letsencrypt
for f in .env whatsapp-qr-service/.env; do
    [ -f "$f" ] || { echo "Missing $f - copy it to the server first."; exit 1; }
done

# ---------- 2. build + start ----------
CERT="/etc/letsencrypt/live/$DOMAIN/fullchain.pem"
if sudo test -f "$CERT"; then export NGINX_CONF=nginx.conf; else export NGINX_CONF=nginx.http.conf; fi
log "Building and starting stack (nginx config: $NGINX_CONF)"
dc up -d --build --remove-orphans
# nginx resolves upstream container IPs only at startup and doesn't watch its bind-mounted
# config, so restart it after any rebuild to pick up new containers/config.
dc restart nginx-proxy

log "Waiting for backend health"
for i in $(seq 1 30); do
    curl -fsS http://127.0.0.1:8000/health && break
    sleep 3
done
echo

# ---------- 3. HTTPS ----------
if [ "$NGINX_CONF" = "nginx.http.conf" ]; then
    public_ip=$(curl -fsS -4 https://ifconfig.me || true)
    dns_ip=$(getent ahostsv4 "$DOMAIN" | awk 'NR==1 {print $1}' || true)
    if [ -n "$public_ip" ] && [ "$public_ip" = "$dns_ip" ]; then
        log "DNS for $DOMAIN -> $public_ip. Requesting Let's Encrypt certificate"
        if [ -n "$CERTBOT_EMAIL" ]; then email_args=(--email "$CERTBOT_EMAIL"); else email_args=(--register-unsafely-without-email); fi
        $DOCKER run --rm -v /etc/letsencrypt:/etc/letsencrypt -v /var/www/certbot:/var/www/certbot \
            certbot/certbot certonly --webroot -w /var/www/certbot "${DOMAINS[@]}" \
            "${email_args[@]}" --agree-tos --non-interactive
        export NGINX_CONF=nginx.conf
        dc up -d nginx-proxy
        log "HTTPS enabled: https://$DOMAIN"
    else
        log "Skipping HTTPS: $DOMAIN resolves to '${dns_ip:-nothing}', this server is '${public_ip:-unknown}'."
        echo "    Point A records for $DOMAIN and www.$DOMAIN at ${public_ip:-this server}, then re-run this script."
    fi
fi

# Twice-daily renewal; nginx reload picks up the new cert.
CRON="0 3,15 * * * $DOCKER run --rm -v /etc/letsencrypt:/etc/letsencrypt -v /var/www/certbot:/var/www/certbot certbot/certbot renew --quiet && $DOCKER compose -f $(pwd)/docker-compose.yml exec -T nginx-proxy nginx -s reload"
if sudo test -f "$CERT" && ! (crontab -l 2>/dev/null | grep -q 'certbot renew'); then
    # `|| true`: with no existing crontab, `crontab -l` exits 1 and set -e/pipefail would abort here.
    { crontab -l 2>/dev/null || true; echo "$CRON"; } | crontab -
    log "Installed certbot renewal cron"
fi

dc ps
