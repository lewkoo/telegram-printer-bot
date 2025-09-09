# 🖨️ Telegram Print Bot

[![Docker Build](https://github.com/lewkoo/telegram-printer-bot/actions/workflows/docker.yml/badge.svg)](https://github.com/lewkoo/telegram-printer-bot/actions/workflows/docker.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Docker Pulls](https://img.shields.io/docker/pulls/lewkoo/telegram-printer-bot)](https://ghcr.io/lewkoo/telegram-printer-bot)

A modern, feature-rich Telegram bot that receives files and prints them wirelessly to your network printer. Perfect for home offices, small businesses, or anyone who wants to print from anywhere via Telegram.

## ✨ Features

- 🔗 **Wireless Printing** - Print directly to network printers via CUPS/IPP
- 📄 **Multi-format Support** - PDF, images (JPEG/PNG/GIF/TIFF/WebP), and Office documents
- 🌙 **Quiet Hours** - Automatically queue print jobs during specified hours
- 🌍 **Timezone Support** - Proper timezone handling for global deployments
- 🔒 **User Access Control** - Whitelist specific Telegram users
- 🔄 **Office Conversion** - Convert Word/Excel/PowerPoint to PDF (optional)
- � **Multilingual Interface** - English and Ukrainian language support
- 📋 **Print Queue Management** - View and manage queued print jobs
- 🐳 **Docker Ready** - Complete containerized solution
- 📦 **Unraid Compatible** - Easy deployment on Unraid systems

## 🚀 Quick Start

### 1. Create Telegram Bot

1. Message [@BotFather](https://t.me/BotFather) on Telegram
2. Send `/newbot` and follow instructions
3. Copy your bot token (format: `123456789:ABC-DEF1234ghIkl-zyx57W2v1u123ew11`)

### 2. Deploy with Docker Compose

```bash
git clone https://github.com/lewkoo/telegram-printer-bot.git
cd telegram-printer-bot
cp .env.example .env
# Edit .env with your settings
docker compose up -d
```

### 3. Configure Environment

Edit `.env` file with your settings:

```bash
# Required
BOT_TOKEN=your_bot_token_here

# Printer settings
PRINTER_IP=192.168.1.100
PRINTER_NAME=MyPrinter

# Security
ALLOWED_USER_IDS=123456789,987654321

# Optional features
ENABLE_LIBREOFFICE=1  # Enable Office document conversion
QUIET_START=22:30     # Queue jobs during quiet hours
QUIET_END=09:00
TZ=Europe/Kiev        # Your timezone
```

## 📖 Configuration Reference

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

## 🌙 Quiet Hours

The bot can queue print jobs during specified hours (e.g., overnight) and automatically process them when quiet hours end:

- **During quiet hours**: Files are queued with message "🌙 Тиша годинни"
- **After quiet hours**: Queue automatically processes and prints all jobs
- **Manual control**: Use `/process` command to manually process queue

### Commands

- `/start` - Show welcome message
- `/status` - Display bot status and settings
- `/queue` - View current print queue
- `/process` - Manually process print queue (admin only)

## 🖨️ Supported Printers

This bot works with any network printer that supports:

- **IPP (Internet Printing Protocol)** - Most modern network printers
- **CUPS compatibility** - Standard on most printers

### Tested Printers

- HP Neverstop Laser MFP 1200w ✅

## 🔧 Office Document Support

Enable LibreOffice integration to convert Office documents to PDF:

```bash
ENABLE_LIBREOFFICE=1
```

**Supported formats:**

- Microsoft Word (.doc, .docx)
- Microsoft Excel (.xls, .xlsx)  
- Microsoft PowerPoint (.ppt, .pptx)
- RTF and plain text files

> **Note**: Enabling LibreOffice increases container size significantly

## 🐳 Docker Deployment

### Docker Compose (Recommended)

```yaml
version: '3.8'
services:
  telegram-print-bot:
    image: ghcr.io/lewkoo/telegram-printer-bot:latest
    container_name: telegram-print-bot
    environment:
      BOT_TOKEN: "${BOT_TOKEN}"
      PRINTER_IP: "${PRINTER_IP:-192.168.1.100}"
      ALLOWED_USER_IDS: "${ALLOWED_USER_IDS}"
      # ... other env vars
    volumes:
      - ./data:/data
    restart: unless-stopped
```

### Docker Run

```bash
docker run -d \
  --name telegram-print-bot \
  -e BOT_TOKEN=your_token \
  -e PRINTER_IP=192.168.1.100 \
  -v $(pwd)/data:/data \
  ghcr.io/lewkoo/telegram-printer-bot:latest
```

## 📦 Unraid Deployment

1. Open Unraid Apps tab
2. Search for "Telegram Print Bot"
3. Install and configure through the UI
4. Set your bot token and printer IP
5. Start the container

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed Unraid instructions.

## 🔒 Security Considerations

- **User Whitelist**: Always set `ALLOWED_USER_IDS` to prevent unauthorized access
- **Network Security**: Ensure your printer is on a trusted network
- **File Validation**: Bot accepts only common file formats
- **No Sandboxing**: Files are printed as-is - only accept from trusted sources

## 🛠️ Development

### Local Development

```bash
git clone https://github.com/lewkoo/telegram-printer-bot.git
cd telegram-printer-bot
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate     # Windows
pip install -r src/requirements.txt
```

### Building Custom Images

```bash
# Basic image
docker build -t telegram-print-bot .

# With LibreOffice support
docker build --build-arg ENABLE_LIBREOFFICE=1 -t telegram-print-bot:libreoffice .
```

## 🐛 Troubleshooting

### Common Issues

**Bot not responding:**

```bash
docker logs telegram-print-bot
```

**Printer not found:**

```bash
docker exec telegram-print-bot lpstat -p -d
```

**Files not printing:**

- Verify printer IP and network connectivity
- Check CUPS printer configuration
- Ensure printer supports IPP

### Debug Mode

Set `LOG_LEVEL=INFO` for detailed logging:

```bash
LOG_LEVEL=INFO
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot) - Telegram Bot API wrapper
- [CUPS](https://www.cups.org/) - Print system
- [LibreOffice](https://www.libreoffice.org/) - Office document conversion

---

Made with ❤️ for the home automation community
