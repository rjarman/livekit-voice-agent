# Debian 12 (bookworm) does not ship an `asterisk` package in stable; use bullseye where it is still available.
# See: https://tracker.debian.org/pkg/asterisk
FROM debian:bullseye-slim

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
