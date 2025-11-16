"""
Main bot orchestration module.
Coordinates email reading, summarization, screenshot, and Telegram sending.
"""

import os
import time
import email.utils
import requests
from bs4 import BeautifulSoup
from tinydb import TinyDB, Query
from dotenv import load_dotenv

from email_reader import fetch_unseen_from, extract_email_parts
from summarizer import summarize_with_groq
from screenshot import html_to_screenshot

load_dotenv()

# Config from env
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")
IMAP_SERVER = os.getenv("IMAP_SERVER", "imap.gmail.com")
FROM_ADDRESS = os.getenv("FROM_ADDRESS")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Simple DB to remember processed message-ids
db = TinyDB("processed_messages.json")
Processed = Query()


def send_via_telegram(chat_id, token, text_summary, image_path=None):
    """
    Send message to Telegram, optionally with an image.
    
    Args:
        chat_id: Telegram chat ID
        token: Telegram bot token
        text_summary: Text message/caption
        image_path: Optional path to image file
    
    Returns:
        Telegram API response JSON
    """
    base = f"https://api.telegram.org/bot{token}"

    if image_path:
        with open(image_path, "rb") as img:
            r = requests.post(
                base + "/sendPhoto",
                data={
                    "chat_id": chat_id,
                    "caption": text_summary[:1024]  # enforce Telegram caption limit
                },
                files={"photo": img},
                timeout=60
            )
        r.raise_for_status()
        return r.json()

    else:
        r = requests.post(
            base + "/sendMessage",
            json={"chat_id": chat_id, "text": text_summary},
            timeout=30
        )
        r.raise_for_status()
        return r.json()


def already_processed(msg_id):
    """Check if a message ID has already been processed."""
    return db.search(Processed.msg_id == msg_id) != []


def mark_processed(msg_id):
    """Mark a message ID as processed."""
    db.insert({'msg_id': msg_id, 'ts': time.time()})


def process_inbox_once():
    """Main function to process inbox once."""
    if not all([EMAIL_USER, EMAIL_PASS, FROM_ADDRESS, GROQ_API_KEY, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID]):
        raise RuntimeError("One or more required environment variables are missing")

    messages = fetch_unseen_from(IMAP_SERVER, EMAIL_USER, EMAIL_PASS, FROM_ADDRESS)
    print(f"Found {len(messages)} message(s)")
    for msg_id, msg in messages:
        if already_processed(msg_id):
            print("Skipping already processed", msg_id)
            continue

        parts = extract_email_parts(msg)
        subject = parts['subject']
        text = parts['text'] or ''
        html = parts['html']

        # create screenshot
        if html:
            # sanitize a bit: wrap in basic HTML if needed
            safe_html = html
            try:
                screenshot_path = f"screenshot_{msg_id}.png"
                html_to_screenshot(safe_html, screenshot_path)
            except Exception as e:
                print("Screenshot failed:", e)
                screenshot_path = None
        else:
            # create an HTML wrapper for plaintext
            safe_html = f"<html><body><pre>{email.utils.escape(text)}</pre></body></html>"
            screenshot_path = f"screenshot_{msg_id}.png"
            html_to_screenshot(safe_html, screenshot_path)

        header_summary = f"*{subject}*\nFrom: {parts['from']}"
        print("Summarizing...")
        summary = summarize_with_groq(
            text or (BeautifulSoup(html or "", 'lxml').get_text('\n')),
            GROQ_API_KEY
        )


        # send to telegram
        print("Sending to Telegram...")
        full_text = header_summary + "\n\n" + summary

        send_via_telegram(TELEGRAM_CHAT_ID, TELEGRAM_TOKEN, full_text, image_path=screenshot_path)

        mark_processed(msg_id)
        print("Done for message", msg_id)


if __name__ == '__main__':
    # simple loop — replace with cron or scheduler in production
    try:
        process_inbox_once()
    except Exception as e:
        print("Error:", e)

