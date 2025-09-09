#!/usr/bin/env python3
"""
Telegram Print Bot

A modern Telegram bot that receives files and prints them wirelessly to network printers.
Supports PDF, images, Office documents with optional LibreOffice conversion, quiet hours,
and comprehensive queue management.

Author: Your Name
License: MIT
Repository: https://github.com/lewkoo/telegram-printer-bot
"""

import asyncio
import logging
import os
import json
import threading
from datetime import datetime, time
from pathlib import Path
from typing import Dict, List, Optional
import pytz

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None
from dataclasses import dataclass

from telegram import Update, constants
from telegram.ext import Application, MessageHandler, CommandHandler, ContextTypes, filters

import printing

# Localization system
MESSAGES = {
    "en": {
        # Access control
        "access_denied": "❌ Access denied",
        "access_denied_config": "❌ Access denied. Configure ALLOWED_USER_IDS.",
        
        # Queue management
        "queue_empty": "📋 Queue is empty",
        "queue_title": "📋 **Print Queue** ({count} jobs):",
        "queue_item": "{num}. `{filename}` (added {time})",
        "queue_processed": "✅ Processed {success} jobs\n❌ Errors: {errors}\n📋 Queue cleared",
        "quiet_hours_active": "🌙 Currently quiet hours. Queue will be processed automatically.",
        
        # Printing
        "printing": "🖨️ Printing…",
        "print_success": "✅ Sent to printer.",
        "print_error": "❌ Print error: {error}",
        "quiet_hours_queued": "🌙 Quiet hours ({start}-{end})\n📋 Job added to queue. Will print at {end_time}.",
        
        # File validation
        "file_too_large": "File too large (> {max_mb} MB).",
        "unsupported_file_type": "Unsupported file type: {mime}. Send PDF or image.",
        "office_conversion_failed": "Failed to convert document to PDF.",
        "office_files_disabled": "Office files not enabled. Send PDF or image, or enable LibreOffice in settings.",
        
        # Status
        "queue_status": "QUEUE={count} jobs",
        "error_message": "❌ {reason}",
        
        # Start command
        "welcome_message": "Hello! Send me a **PDF** or **image** (jpg/png/gif/tiff/webp) and I'll print it.\n\nAdmins can use /status to check printer settings.",
        
        # Status messages
        "quiet_hours_status": "🌙 QUIET HOURS",
        "active_status": "🔊 ACTIVE",
        
        # Log processing
        "bot_starting": "Starting bot (polling)…",
        "bot_stopping": "Stopping bot...",
        "queue_processed_log": "Processed {success_count} queued print jobs",
    },
    "uk": {
        # Access control
        "access_denied": "❌ Доступ заборонено",
        "access_denied_config": "❌ Доступ заборонено. Налаштуйте ALLOWED_USER_IDS.",
        
        # Queue management
        "queue_empty": "📋 Черга порожня",
        "queue_title": "📋 **Черга друку** ({count} завдань):",
        "queue_item": "{num}. `{filename}` (додано {time})",
        "queue_processed": "✅ Оброблено {success} завдань\n❌ Помилок: {errors}\n📋 Черга очищена",
        "quiet_hours_active": "🌙 Зараз тиші години. Черга буде оброблена автоматично.",
        
        # Printing
        "printing": "🖨️ Друкую…",
        "print_success": "✅ Відправлено на принтер.",
        "print_error": "❌ Помилка друку: {error}",
        "quiet_hours_queued": "🌙 Тихі годинни ({start}-{end})\n📋 Завдання додано до черги. Буде надруковано о {end_time}.",
        
        # File validation
        "file_too_large": "Файл занадто великий (> {max_mb} МБ).",
        "unsupported_file_type": "Непідтримуваний тип файлу: {mime}. Надішліть PDF або зображення.",
        "office_conversion_failed": "Не вдалося конвертувати документ у PDF.",
        "office_files_disabled": "Офісні файли не увімкнено. Надішліть PDF або зображення, або увімкніть LibreOffice в налаштуваннях.",
        
        # Status
        "queue_status": "QUEUE={count} завдань",
        "error_message": "❌ {reason}",
        
        # Start command
        "welcome_message": "Привіт! Надішліть мені **PDF** або **зображення** (jpg/png/gif/tiff/webp) і я надрукую це.\n\nАдміни можуть використати /status для перевірки налаштувань принтера.",
        
        # Status messages  
        "quiet_hours_status": "🌙 ТИХІ ГОДИНИ",
        "active_status": "🔊 АКТИВНИЙ",
        
        # Log processing
        "bot_starting": "Запуск бота (polling)…",
        "bot_stopping": "Зупинка бота...",
        "queue_processed_log": "Оброблено {success_count} завдань з черги друку"
    }
}


def get_message(key: str, language: str = "uk", **kwargs) -> str:
    """
    Get localized message by key.
    
    Args:
        key: Message key from MESSAGES dictionary
        language: Language code ('en' or 'uk')
        **kwargs: Format arguments for the message
        
    Returns:
        Formatted message string
    """
    # Fallback to Ukrainian if language not supported
    if language not in MESSAGES:
        language = "uk"
    
    # Fallback to key if message not found
    message = MESSAGES[language].get(key, key)
    
    # Format message with provided arguments
    try:
        return message.format(**kwargs)
    except (KeyError, ValueError):
        return message


import printing
from telegram.ext import (
    Application,
    MessageHandler,
    CommandHandler,
    filters,
    ContextTypes,
)

from printing import IMAGE_MIMES, PDF_MIME, OFFICE_MIMES, print_file, convert_office_to_pdf

# Configure logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "WARNING"),
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger("telegram-print-bot")


@dataclass
class Settings:
    """
    Configuration settings for the Telegram Print Bot.
    
    All settings are loaded from environment variables with sensible defaults.
    """
    bot_token: str                    # Telegram bot token (required)
    printer_name: Optional[str]       # CUPS printer name
    allowed_ids: Optional[set[int]]   # Allowed Telegram user IDs
    max_file_mb: int                  # Maximum file size in MB
    default_media: str                # Paper size (A4, Letter, etc.)
    duplex: str                       # Duplex printing mode
    fit_to_page: bool                 # Fit content to page
    save_dir: Path                    # Directory for saving files
    enable_libreoffice: bool          # Enable Office document conversion
    quiet_start: str                  # Quiet hours start time (HH:MM)
    quiet_end: str                    # Quiet hours end time (HH:MM)
    timezone: str                     # Timezone for quiet hours
    language: str                     # Interface language ('en' or 'uk')


@dataclass
class QueuedJob:
    """
    Represents a print job in the queue.
    
    Jobs are queued during quiet hours and processed automatically
    when quiet hours end or manually via admin commands.
    """
    file_path: Path      # Path to the file to print
    chat_id: int         # Telegram chat ID for status updates
    message_id: int      # Original message ID for reference
    printer_name: str    # Target printer name
    media: str           # Paper size/media type
    duplex: str          # Duplex mode
    fit_to_page: bool    # Fit to page setting
    queued_at: str       # ISO timestamp when job was queued


def parse_settings() -> Settings:
    """
    Parse configuration settings from environment variables.
    
    Loads settings from .env file if python-dotenv is available,
    then reads from environment variables with sensible defaults.
    
    Returns:
        Settings: Parsed configuration object
        
    Raises:
        KeyError: If required BOT_TOKEN environment variable is missing
    """
    # Load .env file if dotenv is available
    env_file = os.getenv("ENV_FILE", ".env")
    if load_dotenv:
        load_dotenv(env_file)

    # Parse allowed user IDs from comma-separated string
    allowed_ids_raw = os.getenv("ALLOWED_USER_IDS", "").strip()
    allowed_ids = None
    if allowed_ids_raw:
        parts = [p.strip() for p in allowed_ids_raw.split(",") if p.strip()]
        ids = set()
        for p in parts:
            # Skip comments starting with #
            if p.startswith("#"):
                continue
            # Add numeric IDs only
            if p.isdigit():
                ids.add(int(p))
        if ids:
            allowed_ids = ids

    return Settings(
        bot_token=os.environ["BOT_TOKEN"],  # Required - will raise KeyError if missing
        printer_name=os.getenv("PRINTER_NAME") or "MyPrinter",
        allowed_ids=allowed_ids,
        max_file_mb=int(os.getenv("MAX_FILE_MB", "20")),
        default_media=os.getenv("DEFAULT_MEDIA", "A4"),
        duplex=os.getenv("DUPLEX", "one-sided"),
        fit_to_page=os.getenv("FIT_TO_PAGE", "true").lower() in ("1", "true", "yes", "on"),
        save_dir=Path(os.getenv("SAVE_DIR", "/data/incoming")),
        enable_libreoffice=os.getenv("ENABLE_LIBREOFFICE", "0") in ("1", "true", "yes", "on"),
        quiet_start=os.getenv("QUIET_START", "22:30"),
        quiet_end=os.getenv("QUIET_END", "09:00"),
        timezone=os.getenv("TZ", "UTC"),
        language=os.getenv("LANGUAGE_CODE", "uk").lower(),  # Default to Ukrainian for backward compatibility
    )


# Initialize global settings
SETTINGS = parse_settings()
# Global configuration and queue management
SETTINGS.save_dir.mkdir(parents=True, exist_ok=True)

# Queue management globals
QUEUE_FILE = SETTINGS.save_dir / "print_queue.json"  # Persistent queue storage
queue_lock = threading.Lock()  # Thread-safe queue operations


def is_quiet_hours() -> bool:
    """
    Check if current time is within configured quiet hours.
    
    During quiet hours, print jobs are queued instead of printed immediately.
    Supports timezone-aware calculations and overnight quiet periods
    (e.g., 22:30 to 09:00).
    
    Returns:
        bool: True if currently within quiet hours, False otherwise
    """
    try:
        # Use configured timezone for accurate time calculation
        tz = pytz.timezone(SETTINGS.timezone)
        now = datetime.now(tz).time()
    except Exception:
        # Fallback to system time if timezone configuration fails
        logger.warning(f"Failed to use timezone {SETTINGS.timezone}, falling back to system time")
        now = datetime.now().time()
    
    start_time = time.fromisoformat(SETTINGS.quiet_start)
    end_time = time.fromisoformat(SETTINGS.quiet_end)
    
    if start_time <= end_time:
        # Same day quiet hours (e.g., 08:00 to 17:00)
        return start_time <= now <= end_time
    else:
        # Overnight quiet hours (e.g., 22:30 to 09:00)
        return now >= start_time or now <= end_time


def load_queue() -> List[QueuedJob]:
    """Load print queue from file."""
    try:
        if QUEUE_FILE.exists():
            with open(QUEUE_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return [QueuedJob(**job) for job in data]
    except Exception as e:
        logger.error(f"Failed to load queue: {e}")
    return []


def save_queue(jobs: List[QueuedJob]) -> None:
    """Save print queue to file."""
    try:
        with open(QUEUE_FILE, 'w', encoding='utf-8') as f:
            data = [job.__dict__ for job in jobs]
            # Convert Path objects to strings for JSON serialization
            for job_data in data:
                job_data['file_path'] = str(job_data['file_path'])
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.error(f"Failed to save queue: {e}")


def add_to_queue(job: QueuedJob) -> None:
    """Add a job to the print queue."""
    with queue_lock:
        jobs = load_queue()
        jobs.append(job)
        save_queue(jobs)


def process_queue() -> List[Dict]:
    """Process all queued jobs and return results."""
    results = []
    
    with queue_lock:
        jobs = load_queue()
        if not jobs:
            return results
            
        processed_jobs = []
        
        for job in jobs:
            try:
                # Reconstruct Path object
                job.file_path = Path(job.file_path)
                
                if job.file_path.exists():
                    print_file(
                        job.file_path,
                        job.printer_name,
                        job.media,
                        job.duplex,
                        job.fit_to_page,
                    )
                    results.append({
                        'success': True,
                        'chat_id': job.chat_id,
                        'message_id': job.message_id,
                        'file': job.file_path.name,
                        'queued_at': job.queued_at
                    })
                else:
                    results.append({
                        'success': False,
                        'chat_id': job.chat_id,
                        'message_id': job.message_id,
                        'file': job.file_path.name,
                        'error': 'File not found',
                        'queued_at': job.queued_at
                    })
                processed_jobs.append(job)
                
            except Exception as e:
                logger.error(f"Failed to process queued job {job.file_path}: {e}")
                results.append({
                    'success': False,
                    'chat_id': job.chat_id,
                    'message_id': job.message_id,
                    'file': job.file_path.name,
                    'error': str(e),
                    'queued_at': job.queued_at
                })
                processed_jobs.append(job)
        
        # Remove processed jobs from queue
        remaining_jobs = [job for job in jobs if job not in processed_jobs]
        save_queue(remaining_jobs)
        
    return results

def user_allowed(update: Update) -> bool:
    """
    Check if user is allowed to use the bot.
    
    Args:
        update: Telegram update object
        
    Returns:
        bool: True if user is allowed, False otherwise
        
    Note:
        If no ALLOWED_USER_IDS is configured, access is denied for security.
    """
    uid = update.effective_user.id if update.effective_user else None
    
    # If no allowed IDs configured, deny access for security
    if SETTINGS.allowed_ids is None:
        try:
            if update.message:
                message = get_message("access_denied_config", SETTINGS.language)
                update.message.reply_text(message)
        except Exception:
            pass
        return False
    
    # Check if user ID is in allowed list
    if uid not in SETTINGS.allowed_ids:
        try:
            if update.message:
                message = get_message("access_denied", SETTINGS.language)
                update.message.reply_text(message)
        except Exception:
            pass
        return False
    return True


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = get_message("welcome_message", SETTINGS.language)
    await update.message.reply_text(
        message,
        parse_mode=constants.ParseMode.MARKDOWN,
    )


async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not user_allowed(update):
        return
    
    # Get queue info
    with queue_lock:
        jobs = load_queue()
        queue_count = len(jobs)
    
    quiet_status = get_message("quiet_hours_status", SETTINGS.language) if is_quiet_hours() else get_message("active_status", SETTINGS.language)
    
    text = (
        f"PRINTER_NAME={SETTINGS.printer_name}\n"
        f"MEDIA={SETTINGS.default_media}\n"
        f"DUPLEX={SETTINGS.duplex}\n"
        f"FIT_TO_PAGE={SETTINGS.fit_to_page}\n"
        f"MAX_FILE_MB={SETTINGS.max_file_mb}\n"
        f"LibreOffice={'ON' if SETTINGS.enable_libreoffice else 'OFF'}\n"
        f"QUIET_HOURS={SETTINGS.quiet_start}-{SETTINGS.quiet_end}\n"
        f"STATUS={quiet_status}\n"
        f"{get_message('queue_status', SETTINGS.language, count=queue_count)}"
    )
    await update.message.reply_text(f"```\n{text}\n```", parse_mode=constants.ParseMode.MARKDOWN_V2)


async def cmd_queue(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show current print queue."""
    if not user_allowed(update):
        return
    
    with queue_lock:
        jobs = load_queue()
    
    if not jobs:
        message = get_message("queue_empty", SETTINGS.language)
        await update.message.reply_text(message)
        return
    
    queue_text = get_message("queue_title", SETTINGS.language, count=len(jobs)) + "\n\n"
    for i, job in enumerate(jobs, 1):
        file_name = Path(job.file_path).name
        queued_time = datetime.fromisoformat(job.queued_at).strftime("%H:%M")
        queue_text += get_message("queue_item", SETTINGS.language, 
                                num=i, filename=file_name, time=queued_time) + "\n"
    
    await update.message.reply_text(queue_text, parse_mode=constants.ParseMode.MARKDOWN)


async def cmd_process_queue(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Manually process the print queue (admin only)."""
    if not user_allowed(update):
        return
    
    if is_quiet_hours():
        message = get_message("quiet_hours_active", SETTINGS.language)
        await update.message.reply_text(message)
        return
    
    results = process_queue()
    
    if not results:
        message = get_message("queue_empty", SETTINGS.language)
        await update.message.reply_text(message)
        return
    
    success_count = sum(1 for r in results if r['success'])
    fail_count = len(results) - success_count
    
    message = get_message("queue_processed", SETTINGS.language, 
                         success=success_count, errors=fail_count)
    await update.message.reply_text(message)


async def reject(update: Update, reason: str) -> None:
    message = get_message("error_message", SETTINGS.language, reason=reason)
    await update.message.reply_text(message)


def within_size_limit(size_bytes: int) -> bool:
    max_bytes = SETTINGS.max_file_mb * 1024 * 1024
    return size_bytes <= max_bytes


async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not user_allowed(update):
        return

    doc = update.message.document
    if doc is None:
        return

    mime = doc.mime_type or ""
    size = doc.file_size or 0
    if not within_size_limit(size):
        reason = get_message("file_too_large", SETTINGS.language, max_mb=SETTINGS.max_file_mb)
        await reject(update, reason)
        return

    ok_types = {PDF_MIME} | IMAGE_MIMES | OFFICE_MIMES
    if mime not in ok_types:
        reason = get_message("unsupported_file_type", SETTINGS.language, mime=mime)
        await reject(update, reason)
        return

    tg_file = await context.bot.get_file(doc.file_id)
    filename = doc.file_name or f"file_{doc.file_unique_id}"
    target = SETTINGS.save_dir / filename

    await update.message.chat.send_action(constants.ChatAction.UPLOAD_DOCUMENT)
    await tg_file.download_to_drive(custom_path=str(target))

    await process_and_print(update, target, mime)


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not user_allowed(update):
        return

    photos = update.message.photo
    if not photos:
        return

    largest = photos[-1]
    tg_file = await context.bot.get_file(largest.file_id)

    filename = f"photo_{largest.file_unique_id}.jpg"
    target = SETTINGS.save_dir / filename

    await update.message.chat.send_action(constants.ChatAction.UPLOAD_PHOTO)
    await tg_file.download_to_drive(custom_path=str(target))

    await process_and_print(update, target, "image/jpeg")


async def process_and_print(update: Update, path: Path, mime: str) -> None:
    try:
        printable_path = path

        if mime in OFFICE_MIMES and SETTINGS.enable_libreoffice:
            pdf = convert_office_to_pdf(path, SETTINGS.save_dir)
            if pdf is None:
                await reject(update, get_message("office_conversion_failed", SETTINGS.language))
                return
            printable_path = pdf
        elif mime in OFFICE_MIMES and not SETTINGS.enable_libreoffice:
            await reject(update, get_message("office_files_disabled", SETTINGS.language))
            return

        # Check if it's quiet hours
        if is_quiet_hours():
            # Queue the job for later processing
            try:
                tz = pytz.timezone(SETTINGS.timezone)
                queued_time = datetime.now(tz).isoformat()
            except:
                queued_time = datetime.now().isoformat()
                
            job = QueuedJob(
                file_path=printable_path,
                chat_id=update.message.chat_id,
                message_id=update.message.message_id,
                printer_name=SETTINGS.printer_name,
                media=SETTINGS.default_media,
                duplex=SETTINGS.duplex,
                fit_to_page=SETTINGS.fit_to_page,
                queued_at=queued_time
            )
            add_to_queue(job)
            message = get_message("quiet_hours_queued", SETTINGS.language,
                                start=SETTINGS.quiet_start, 
                                end=SETTINGS.quiet_end,
                                end_time=SETTINGS.quiet_end)
            await update.message.reply_text(message)
        else:
            # Print immediately
            message = get_message("printing", SETTINGS.language)
            await update.message.reply_text(message)
            print_file(
                printable_path,
                SETTINGS.printer_name,
                SETTINGS.default_media,
                SETTINGS.duplex,
                SETTINGS.fit_to_page,
            )
            message = get_message("print_success", SETTINGS.language)
            await update.message.reply_text(message)
    except Exception as e:
        logger.exception("Printing failed")
        reason = get_message("print_error", SETTINGS.language, error=str(e))
        await reject(update, reason)


async def queue_processor_task() -> None:
    """Background task to process queue when quiet hours end."""
    while True:
        try:
            await asyncio.sleep(60)  # Check every minute
            
            if not is_quiet_hours():
                results = process_queue()
                if results:
                    success_count = sum(1 for r in results if r['success'])
                    logger.warning(get_message("queue_processed_log", SETTINGS.language, success_count=success_count))
                    
        except Exception as e:
            logger.error(f"Queue processor error: {e}")


def build_app() -> Application:
    app = Application.builder().token(SETTINGS.bot_token).build()
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("status", cmd_status))
    app.add_handler(CommandHandler("queue", cmd_queue))
    app.add_handler(CommandHandler("process", cmd_process_queue))

    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))

    return app


async def main() -> None:
    app = build_app()
    
    # Start queue processor in background
    queue_task = asyncio.create_task(queue_processor_task())
    
    logger.warning(get_message("bot_starting", SETTINGS.language))
    
    try:
        await app.initialize()
        await app.start()
        await app.updater.start_polling(allowed_updates=Update.ALL_TYPES)
        
        # Keep running until interrupted
        await asyncio.Event().wait()
        
    except KeyboardInterrupt:
        logger.warning(get_message("bot_stopping", SETTINGS.language))
    finally:
        queue_task.cancel()
        await app.stop()
        await app.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
