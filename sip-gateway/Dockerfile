# Asterisk is in Debian repos on linux/amd64 only (not arm64). Build on your x86_64 server,
# or from any host: docker compose build --platform linux/amd64 sip-gateway
FROM --platform=linux/amd64 debian:bookworm-slim

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update \
  && apt-get install -y --no-install-recommends \
    asterisk \
    gettext-base \
    ca-certificates \
  && rm -rf /var/lib/apt/lists/*

COPY docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

COPY asterisk/templates/ /etc/asterisk/templates/
COPY asterisk/static/ /etc/asterisk/static/

EXPOSE 5060/udp 5060/tcp 10000-10100/udp

ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]
