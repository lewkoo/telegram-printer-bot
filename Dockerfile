# syntax=docker/dockerfile:1
FROM python:3.11-slim

ARG DEBIAN_FRONTEND=noninteractive
# Defaults; override at build or run time if needed
ARG PRINTER_IP=192.168.1.100
ARG PRINTER_NAME=MyPrinter

ENV PRINTER_IP=${PRINTER_IP}
ENV PRINTER_NAME=${PRINTER_NAME}
ENV LC_ALL=C.UTF-8 LANG=C.UTF-8

# System deps: CUPS daemon + filters, client tools, Ghostscript for robust PDF handling, LibreOffice for Office docs
RUN apt-get update && apt-get install -y --no-install-recommends \
      cups cups-filters cups-bsd cups-client cups-ipp-utils ghostscript \
      libreoffice-writer libreoffice-calc libreoffice-impress \
      ca-certificates curl bash procps \
 && rm -rf /var/lib/apt/lists/*

# Minimal CUPS config: only a unix socket, no sharing, quiet logs
RUN mkdir -p /etc/cups && \
    cat > /etc/cups/cupsd.conf <<'EOF'
LogLevel warn
SystemGroup lpadmin
Listen /var/run/cups/cups.sock
Browsing Off
DefaultAuthType Basic
<Location />
  Order allow,deny
  Allow localhost
</Location>
EOF

# Create app user with printing privileges
RUN useradd -m -u 1000 app && usermod -aG lp,lpadmin app

# Python deps
WORKDIR /app
COPY ./src/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# App code
COPY . /app

# Entrypoint: starts cupsd, prepares queue or falls back, fixes /data perms, runs the bot
COPY docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

USER root
ENTRYPOINT ["docker-entrypoint.sh"]
# If your code lives under /app/src/bot.py, this still works (we cd /app in entrypoint)
CMD ["python", "src/bot.py"]
