# Telegram Print Bot - Deployment Guide

## Overview
A reliable Telegram bot that prints PDF files and Office documents to your network printer using CUPS/IPP with timezone-aware quiet hours support.

## Quick Start

### Prerequisites
- Docker and Docker Compose installed
- Network printer with IPP support
- Telegram bot token from [@BotFather](https://t.me/botfather)

### 1. Clone and Configure
```bash
git clone https://github.com/lewkoo/telegram-printer-bot.git
cd telegram-printer-bot
cp .env.example .env
```

Edit `.env` with your settings:
```bash
# Required
BOT_TOKEN=your_bot_token_from_botfather

# Printer configuration
PRINTER_NAME=MyPrinter
PRINTER_IP=192.168.1.100

# Security
ALLOWED_USER_IDS=123456789,987654321  # Your Telegram user IDs

# Optional features
ENABLE_LIBREOFFICE=1      # Office document support
QUIET_START=22:30         # Quiet hours start
QUIET_END=09:00           # Quiet hours end
TZ=Europe/Kiev            # Timezone for quiet hours
```

### 2. Deploy with Docker Compose
```bash
docker compose up -d
```

### 3. Verify Setup
```bash
# Check container logs
docker logs telegram-print-bot

# Test printer connection
docker exec telegram-print-bot lpstat -p
```

## Deployment Methods

### Docker Compose (Recommended)

The `docker-compose.yml` file provides a complete setup with:
- Automatic printer configuration
- Volume mounting for persistence
- Environment variable support
- Timezone configuration

```yaml
services:
  telegram-print-bot:
    build: .
    environment:
      - BOT_TOKEN=${BOT_TOKEN}
      - PRINTER_IP=${PRINTER_IP}
      - TZ=${TZ:-UTC}
    volumes:
      - ./data:/data
    restart: unless-stopped
```

### Unraid Deployment

#### Method 1: Community Applications
1. Open Unraid web interface
2. Go to **Apps** → **Community Applications**
3. Search for "Telegram Print Bot"
4. Click **Install** and configure:
   - **Bot Token**: Your Telegram bot token
   - **Printer IP**: Your printer's IP address
   - **Allowed User IDs**: Comma-separated user IDs
   - **Data Path**: `/mnt/user/appdata/telegram-print-bot`

#### Method 2: Manual Template
1. Download `unraid-template.xml` from the repository
2. Go to **Docker** → **Add Container**
3. Click **Template** and paste the template URL
4. Configure the required settings
5. Click **Apply**

## How It Works

The bot uses a proven two-step approach:

1. **Printer Setup**: `lpadmin -p MyPrinter -E -v ipp://PRINTER_IP/ipp/print -m everywhere`
2. **File Printing**: `lpr -P MyPrinter -o media=A4 -o fit-to-page <file_path>`

### Key Features
- ⚡ **Fast**: ~12ms print execution time
- 🛡️ **Safe**: No printer firmware crashes
- 🎯 **Reliable**: Uses standard CUPS/IPP protocols
- 🌍 **Localized**: Ukrainian interface support
- 🌙 **Smart**: Timezone-aware quiet hours
- 📄 **Versatile**: PDF and Office document support

## Supported Printers

Any network printer with IPP support, tested with:
- HP Neverstop Laser MFP 1200w

### Printer Requirements
- Network connectivity (WiFi or Ethernet)
- IPP protocol support (most modern printers)
- Accessible via IP address from Docker host

## Usage Examples

### Basic PDF Printing
1. Send a PDF file to the bot
2. Bot processes and prints immediately
3. Receive confirmation message

### Office Document Printing
1. Enable LibreOffice: `ENABLE_LIBREOFFICE=1`
2. Send .docx, .xlsx, .pptx files
3. Bot converts to PDF and prints

### Quiet Hours
Documents sent during quiet hours are queued and printed when quiet hours end:
- Configure: `QUIET_START=22:30` and `QUIET_END=09:00`
- Set timezone: `TZ=Europe/Kiev`
- Bot shows queue status and processes automatically

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `BOT_TOKEN` | *required* | Telegram bot token from @BotFather |
| `PRINTER_IP` | `192.168.1.100` | Network printer IP address |
| `PRINTER_NAME` | `MyPrinter` | CUPS printer name |
| `ALLOWED_USER_IDS` | *see .env* | Comma-separated Telegram user IDs |
| `MAX_FILE_MB` | `20` | Maximum file size limit (MB) |
| `DEFAULT_MEDIA` | `A4` | Paper size (A4, Letter, etc.) |
| `DUPLEX` | `one-sided` | Printing mode |
| `FIT_TO_PAGE` | `true` | Scale content to fit page |
| `QUIET_START` | `22:30` | Start of quiet hours (HH:MM) |
| `QUIET_END` | `09:00` | End of quiet hours (HH:MM) |
| `TZ` | `UTC` | Timezone for quiet hours |
| `LANGUAGE_CODE` | `uk` | Interface language (`en` or `uk`) |
| `ENABLE_LIBREOFFICE` | `0` | Enable Office document conversion |
| `LOG_LEVEL` | `WARNING` | Logging verbosity |

## Security Configuration

### User Access Control

Always configure `ALLOWED_USER_IDS` to prevent unauthorized access:

```bash
ALLOWED_USER_IDS=123456789,987654321
```

To find your Telegram user ID:
1. Message [@userinfobot](https://t.me/userinfobot)
2. Copy the numeric ID from the response

### Network Security

- Place printer on trusted network segment
- Consider firewall rules for container access
- Use VPN for remote access if needed
- Regularly update container images

## Troubleshooting

### Common Issues

#### Bot Not Responding
```bash
# Check container status
docker ps | grep telegram-print-bot

# View recent logs
docker logs --tail 50 telegram-print-bot

# Restart container
docker compose restart
```

#### Printer Not Found
```bash
# Check printer status
docker exec telegram-print-bot lpstat -p -d

# Test printer connectivity
docker exec telegram-print-bot ping -c 3 PRINTER_IP

# Manually add printer
docker exec telegram-print-bot lpadmin -p MyPrinter -E -v ipp://PRINTER_IP/ipp/print -m everywhere
```

#### Files Not Printing
```bash
# Check print queue
docker exec telegram-print-bot lpstat -o

# Clear stuck jobs
docker exec telegram-print-bot cancel -a

# Test with simple file
echo "Test print" | docker exec -i telegram-print-bot lpr -P MyPrinter
```

#### Permission Denied
- Verify `ALLOWED_USER_IDS` includes your Telegram user ID
- Check BOT_TOKEN is correct and active
- Ensure bot has necessary permissions

### Diagnostic Commands

```bash
# Container health check
docker exec telegram-print-bot ps aux

# CUPS status
docker exec telegram-print-bot systemctl status cups

# Network connectivity
docker exec telegram-print-bot netstat -tuln

# Disk space
docker exec telegram-print-bot df -h
```

### Log Analysis

```bash
# Follow live logs
docker logs -f telegram-print-bot

# Search for errors
docker logs telegram-print-bot 2>&1 | grep -i error

# Export logs for analysis
docker logs telegram-print-bot > bot-logs.txt
```

## Performance Optimization

### Memory Usage
- Default: 128MB RAM sufficient for basic operation
- With LibreOffice: Increase to 512MB for large documents
- Monitor with: `docker stats telegram-print-bot`

### Storage Management
```bash
# Clean old files (run periodically)
find /data/incoming -type f -mtime +7 -delete

# Monitor disk usage
du -sh /data/
```

### Network Optimization
- Use wired connection for printer when possible
- Consider printer queue depth for high-volume scenarios
- Monitor network latency to printer

## Maintenance

### Regular Tasks
1. **Update container**: `docker compose pull && docker compose up -d`
2. **Clean old files**: Remove processed files from `/data/incoming`
3. **Check logs**: Review for errors or unusual activity
4. **Backup config**: Save `.env` and `docker-compose.yml`

### Monitoring
```bash
# Container resource usage
docker stats telegram-print-bot

# Print queue status
docker exec telegram-print-bot lpstat -o

# Bot response time
curl -s "https://api.telegram.org/bot$BOT_TOKEN/getMe"
```

### Backup and Recovery
```bash
# Backup configuration
tar -czf telegram-print-bot-backup.tar.gz .env docker-compose.yml data/

# Restore from backup
tar -xzf telegram-print-bot-backup.tar.gz
docker compose up -d
```

## Advanced Configuration

### Custom CUPS Configuration
Mount custom configuration for specialized setups:
```yaml
volumes:
  - ./custom-cupsd.conf:/etc/cups/cupsd.conf:ro
```

### Multiple Printers
Configure multiple printers by extending the setup script:
```bash
# In docker-entrypoint.sh
lpadmin -p Printer1 -E -v ipp://192.168.1.100/ipp/print -m everywhere
lpadmin -p Printer2 -E -v ipp://192.168.1.101/ipp/print -m everywhere
```

## Getting Help

### Community Support
- GitHub Issues: Report bugs and feature requests
- Discussions: General questions and community help
- Wiki: Additional documentation and examples

### Professional Support
For enterprise deployments or custom features, consider:
- Consulting services for complex setups
- Custom development for specific requirements
- Enterprise support contracts

### Contributing
Contributions welcome! Please read `CONTRIBUTING.md` for guidelines on:
- Bug reports
- Feature requests
- Code contributions
- Documentation improvements
