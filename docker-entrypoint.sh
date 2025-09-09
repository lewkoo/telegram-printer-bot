#!/usr/bin/env bash
set -euo pipefail

: "${PRINTER_IP:?PRINTER_IP must be set (e.g. 192.168.1.100)}"
: "${PRINTER_NAME:=MyPrinter}"

echo "[entrypoint] Starting cupsd…"
cupsd || true

# Setup the printer using the CONFIRMED WORKING command
echo "[entrypoint] Setting up ${PRINTER_NAME} printer..."
lpadmin -p "${PRINTER_NAME}" -E -v "ipp://${PRINTER_IP}/ipp/print" -m everywhere || true
echo "[entrypoint] ${PRINTER_NAME} printer setup complete"

# Prepare writable data dir
mkdir -p /data/incoming
chown -R app:app /data || true
chmod -R u+rwX,g+rwX /data || true

# Run app from /app as non-root
exec su -s /bin/bash -c "cd /app && exec $*" app
