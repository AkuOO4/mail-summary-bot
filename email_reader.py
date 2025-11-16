"""
Email reader module for fetching and parsing emails via IMAP.
"""

import imaplib
import email
from email.header import decode_header
from bs4 import BeautifulSoup


def fetch_unseen_from(imap_server, user, password, from_address):
    """
    Fetch unread emails from a specific sender using IMAP.
    
    Args:
        imap_server: IMAP server address (e.g., imap.gmail.com)
        user: Email username
        password: Email password or app-password
        from_address: Sender address to filter by
    
    Returns:
        List of tuples: (message_id, email.message.Message)
    """
    mail = imaplib.IMAP4_SSL(imap_server)
    mail.login(user, password)
    mail.select("inbox")

    # search unseen mails from a specific address
    status, data = mail.search(None, f'(UNSEEN FROM "{from_address}")')
    if status != 'OK':
        print("IMAP search failed", status)
        mail.logout()
        return []

    ids = data[0].split()
    messages = []
    for num in ids:
        status, msg_data = mail.fetch(num, '(RFC822)')
        if status != 'OK':
            continue
        raw = msg_data[0][1]
        msg = email.message_from_bytes(raw)
        messages.append((num.decode(), msg))

    mail.logout()
    return messages


def extract_email_parts(msg):
    """
    Parse email message into structured parts (subject, from, text, html).
    
    Args:
        msg: email.message.Message object
    
    Returns:
        Dictionary with keys: subject, from, text, html
    """
    subject, encoding = decode_header(msg.get('Subject', ''))[0]
    if isinstance(subject, bytes):
        try:
            subject = subject.decode(encoding or 'utf-8')
        except:
            subject = subject.decode('utf-8', errors='ignore')

    from_ = msg.get('From')
    text_parts = []
    html_part = None

    if msg.is_multipart():
        for part in msg.walk():
            ctype = part.get_content_type()
            disp = str(part.get('Content-Disposition'))
            if ctype == 'text/plain' and 'attachment' not in disp:
                payload = part.get_payload(decode=True)
                if payload:
                    text_parts.append(payload.decode(part.get_content_charset() or 'utf-8', errors='ignore'))
            elif ctype == 'text/html' and 'attachment' not in disp:
                payload = part.get_payload(decode=True)
                if payload:
                    html_part = payload.decode(part.get_content_charset() or 'utf-8', errors='ignore')
    else:
        ctype = msg.get_content_type()
        payload = msg.get_payload(decode=True)
        if ctype == 'text/plain':
            text_parts.append(payload.decode(msg.get_content_charset() or 'utf-8', errors='ignore'))
        elif ctype == 'text/html':
            html_part = payload.decode(msg.get_content_charset() or 'utf-8', errors='ignore')

    text = "\n\n".join(text_parts).strip()
    # if no plain text, try to strip text from HTML
    if not text and html_part:
        soup = BeautifulSoup(html_part, 'lxml')
        text = soup.get_text('\n')

    return {
        'subject': subject,
        'from': from_,
        'text': text,
        'html': html_part
    }

