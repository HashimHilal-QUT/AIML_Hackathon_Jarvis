from flask import Flask, request, Response
import os
from dotenv import load_dotenv
import sqlite3
import time
import threading
from typing import List, Tuple
from openai import OpenAI
import requests
from xml.sax.saxutils import escape as xml_escape

load_dotenv()

_rate_limit_lock = threading.Lock()
_last_request_at = {}


def get_db_path():
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), 'conversations.db')


def init_db():
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            phone TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    cur.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_messages_phone ON messages(phone)
        """
    )
    conn.commit()
    conn.close()


def _connect_db():
    return sqlite3.connect(get_db_path())


def save_message(phone: str, role: str, content: str) -> None:
    conn = _connect_db()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO messages (phone, role, content) VALUES (?, ?, ?)",
        (phone, role, content),
    )
    # Keep only last 20 rows per phone to bound DB size
    cur.execute(
        """
        DELETE FROM messages
        WHERE id NOT IN (
            SELECT id FROM messages WHERE phone = ? ORDER BY id DESC LIMIT 20
        ) AND phone = ?
        """,
        (phone, phone),
    )
    conn.commit()
    conn.close()


def get_recent_history(phone: str, limit: int = 10) -> List[Tuple[str, str]]:
    conn = _connect_db()
    cur = conn.cursor()
    cur.execute(
        "SELECT role, content FROM messages WHERE phone = ? ORDER BY id DESC LIMIT ?",
        (phone, limit),
    )
    rows = cur.fetchall()
    conn.close()
    # reverse to chronological order
    return list(reversed(rows))


def rate_limit_ok(phone: str, min_interval_seconds: float) -> bool:
    now = time.time()
    with _rate_limit_lock:
        last = _last_request_at.get(phone, 0)
        if now - last < min_interval_seconds:
            return False
        _last_request_at[phone] = now
        return True


def split_sms(text: str, segment_len: int = 320) -> List[str]:
    if not text:
        return [""]
    text = text.strip()
    if len(text) <= segment_len:
        return [text]
    segments: List[str] = []
    start = 0
    while start < len(text):
        end = min(start + segment_len, len(text))
        chunk = text[start:end]
        if end < len(text):
            # try to break at last space
            last_space = chunk.rfind(' ')
            if last_space > 0 and (start + last_space) > start:
                end = start + last_space
                chunk = text[start:end]
        segments.append(chunk.strip())
        start = end
        while start < len(text) and text[start] == ' ':
            start += 1
    return segments


def openai_reply(app: Flask, phone: str, user_text: str) -> str:
    api_key = app.config['OPENAI_API_KEY']
    model = app.config['OPENAI_MODEL']
    if not api_key:
        return "OpenAI API key not configured."

    client = OpenAI(api_key=api_key)

    system_prompt = (
        "You are an SMS assistant. Reply concisely in under 320 characters per message. "
        "Use plain text; avoid links unless necessary. Australian context when relevant."
    )

    history = get_recent_history(phone, limit=10)
    messages = [{"role": "system", "content": system_prompt}]
    for role, content in history:
        messages.append({"role": role, "content": content})
    messages.append({"role": "user", "content": user_text})

    try:
        completion = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.3,
            max_tokens=400,  # keep it short and cheap
        )
        content = completion.choices[0].message.content or ""
    except Exception as e:
        return f"Error from OpenAI: {e}"

    # Trim to ~1000 chars max
    if len(content) > 1000:
        content = content[:1000].rstrip() + "…"
    return content.strip()


def send_via_twilio_twilml(segments: List[str]) -> Response:
    # Build a TwiML response containing multiple <Message>
    body = ["<?xml version=\"1.0\" encoding=\"UTF-8\"?>", "<Response>"]
    for seg in segments:
        body.append(f"<Message>{xml_escape(seg)}</Message>")
    body.append("</Response>")
    xml = "".join(body)
    return Response(xml, content_type='application/xml')


def send_via_twilio_rest(app: Flask, to_number: str, segments: List[str]) -> Tuple[int, str]:
    # Optional: use Twilio REST if desired
    from twilio.rest import Client as TwilioClient

    sid = app.config['TWILIO_ACCOUNT_SID']
    token = app.config['TWILIO_AUTH_TOKEN']
    from_number = app.config['TWILIO_FROM_NUMBER']
    if not (sid and token and from_number):
        return 500, "Twilio credentials not configured"

    client = TwilioClient(sid, token)
    try:
        for seg in segments:
            client.messages.create(from_=from_number, to=to_number, body=seg)
        return 200, "sent"
    except Exception as e:
        return 500, f"Twilio send error: {e}"


def send_via_playsms(app: Flask, to_number: str, segments: List[str]) -> Tuple[int, str]:
    base_url = app.config['PLAYSMS_API_URL']
    api_key = app.config['PLAYSMS_API_KEY']
    sender = app.config['PLAYSMS_SENDER_ID']
    if not (base_url and api_key and sender):
        return 500, "PlaySMS config missing"

    # Common PlaySMS WS endpoint pattern: /index.php?app=ws&op=pv
    # Using GET for compatibility; some installs require auth via h (API key)
    try:
        for seg in segments:
            params = {
                'app': 'ws',
                'op': 'pv',
                'h': api_key,
                'to': to_number,
                'msg': seg,
                'sender': sender,
            }
            resp = requests.get(base_url.rstrip('/') + '/index.php', params=params, timeout=15)
            if resp.status_code >= 300:
                return resp.status_code, f"PlaySMS send failed: {resp.text[:200]}"
        return 200, "sent"
    except Exception as e:
        return 500, f"PlaySMS send error: {e}"


def create_app():
    app = Flask(__name__)

    # Basic config from env
    app.config['OPENAI_API_KEY'] = os.getenv('OPENAI_API_KEY', '')
    app.config['OPENAI_MODEL'] = os.getenv('OPENAI_MODEL', 'gpt-4o-mini')

    app.config['USE_TWILIO'] = os.getenv('USE_TWILIO', 'false').lower() == 'true'
    app.config['USE_PLAYSMS'] = os.getenv('USE_PLAYSMS', 'false').lower() == 'true'

    app.config['TWILIO_ACCOUNT_SID'] = os.getenv('TWILIO_ACCOUNT_SID', '')
    app.config['TWILIO_AUTH_TOKEN'] = os.getenv('TWILIO_AUTH_TOKEN', '')
    app.config['TWILIO_FROM_NUMBER'] = os.getenv('TWILIO_FROM_NUMBER', '')

    app.config['PLAYSMS_API_URL'] = os.getenv('PLAYSMS_API_URL', '')
    app.config['PLAYSMS_API_KEY'] = os.getenv('PLAYSMS_API_KEY', '')
    app.config['PLAYSMS_SENDER_ID'] = os.getenv('PLAYSMS_SENDER_ID', '')

    init_db()

    @app.route('/')
    def health():
        return {'status': 'ok'}

    @app.route('/sms', methods=['POST'])
    def sms_webhook():
        # Determine provider by payload or env toggles
        form = request.form or {}
        json_data = request.get_json(silent=True) or {}

        # Twilio: From, Body
        from_number = form.get('From') or json_data.get('From') or form.get('from') or json_data.get('from')
        body_text = form.get('Body') or json_data.get('Body') or form.get('text') or json_data.get('text') or form.get('message') or json_data.get('message')

        if not from_number or not body_text:
            return Response('Missing sender or message', status=400)

        # Enforce simple rate limit: 0.5s between requests per sender
        if not rate_limit_ok(from_number, 0.5):
            # For Twilio, we should still return TwiML to avoid retries; say wait
            limited_message = "Please wait a moment before sending another message."
            if app.config['USE_TWILIO']:
                return send_via_twilio_twilml(split_sms(limited_message))
            return Response(limited_message, status=429)

        # Save user message
        save_message(from_number, 'user', body_text)

        # Get AI reply
        ai_text = openai_reply(app, from_number, body_text)
        save_message(from_number, 'assistant', ai_text)
        segments = split_sms(ai_text, 320)

        # Send back depending on integration
        if app.config['USE_TWILIO']:
            # Prefer TwiML multimessage response
            return send_via_twilio_twilml(segments)

        if app.config['USE_PLAYSMS']:
            code, msg = send_via_playsms(app, from_number, segments)
            status = 200 if code == 200 else 500
            return Response(msg, status=status)

        # Fallback: just echo as text for dev/testing
        return Response("\n\n".join(segments), status=200, mimetype='text/plain')

    return app


# Expose module-level app for Gunicorn
app = create_app()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', '5000')))
