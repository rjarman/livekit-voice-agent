#!/bin/sh
set -e

# Static configs (no env substitution — preserves Asterisk $variables in dialplan)
for f in /etc/asterisk/static/*.conf; do
  [ -f "$f" ] || continue
  base=$(basename "$f")
  cp "$f" "/etc/asterisk/$base"
done

# Templated configs (PJSIP, RTP)
for t in /etc/asterisk/templates/*.template; do
  [ -f "$t" ] || continue
  base=$(basename "$t" .template)
  envsubst < "$t" > "/etc/asterisk/$base"
done

exec asterisk -f -vvv
