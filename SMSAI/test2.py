import os
from flask import Flask, request, jsonify
import requests
from openai import OpenAI

TEXTBELT_KEY = os.getenv("TEXTBELT_KEY", "3a5edbc0db952b9043572e678a103fabef5fd218IpQuOMdqcolaRilUE6aEuawT3")
# Fallback above matches the working key used in test.py
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "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")     # your OpenAI key
OPENAI_MODEL ="gpt-4o-mini"
BRAND = os.getenv("AI_BRAND_NAME", "AI SMS Assistant")

client = OpenAI(api_key=OPENAI_API_KEY)
app = Flask(__name__)

# ---- Simple in-memory session store (swap for Redis/DB in prod) ----
CONTEXT = {}  # phone -> list of {"role":"user/assistant", "content": str}, short history

def ai_reply(phone: str, user_text: str) -> str:
    # keep short rolling history
    history = CONTEXT.setdefault(phone, [])
    history.append({"role":"user","content":user_text})
    history = history[-6:]  # last 6 turns
    CONTEXT[phone] = history

    system = f"You are a concise, friendly SMS bot for {BRAND}. Keep replies under 500 characters. Plain text only."
    msgs = [{"role":"system","content":system}] + history

    resp = client.responses.create(model=OPENAI_MODEL, input=msgs)
    answer = (resp.output_text or "").strip()

    CONTEXT[phone].append({"role":"assistant","content":answer})
    CONTEXT[phone] = CONTEXT[phone][-6:]
    return answer

def send_sms(to_e164: str, message: str, reply_webhook_url: str):
    r = requests.post("https://textbelt.com/text", data={
        "phone": to_e164,
        "message": message,
        "key": TEXTBELT_KEY,
        # This tells Textbelt where to POST replies:
        "replyWebhookUrl": reply_webhook_url,
    }, timeout=20)
    r.raise_for_status()
    return r.json()

@app.get("/healthz")
def healthz():
    return {"ok": True}

# --- 1) Kick off a conversation (proactively message your client) ---
@app.post("/send")
def send_initial():
    data = request.get_json(force=True)
    to = data.get("to")       # e.g., "+1408XXXXXXX"
    text = data.get("text", "Hi! You can text me questions and I'll reply with AI.")
    if not to: return {"error":"missing 'to'"}, 400

    webhook = data.get("webhook") or (request.url_root.rstrip("/") + "/textbelt/reply")
    res = send_sms(to, text, webhook)
    return jsonify({"ok": True, "textbelt": res})

# --- 2) Handle inbound replies from Textbelt (webhook) ---
@app.post("/textbelt/reply")
def textbelt_reply():
    payload = request.get_json(force=True)  # Textbelt POSTs JSON
    # Typical fields include: from, to, text, messageId, timestamp
    frm = payload.get("from")
    body = (payload.get("text") or "").strip()

    if not frm or not body:
        return jsonify({"ok": False, "error": "missing from/text"}), 400

    # simple STOP/HELP
    if body.upper().strip() in {"STOP", "UNSUBSCRIBE"}:
        CONTEXT.pop(frm, None)
        send_sms(frm, "You’re unsubscribed. Reply START to resume.", request.url_root.rstrip("/") + "/textbelt/reply")
        return jsonify({"ok": True})

    if body.upper().strip() in {"START", "UNSTOP"}:
        send_sms(frm, "You’re subscribed. Ask me anything!", request.url_root.rstrip("/") + "/textbelt/reply")
        return jsonify({"ok": True})

    try:
        reply = ai_reply(frm, body)
    except Exception:
        reply = "Sorry—having trouble answering right now."

    send_sms(frm, reply, request.url_root.rstrip("/") + "/textbelt/reply")
    return jsonify({"ok": True})
    
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "8000")))



# curl -X POST http://192.168.1.102:8000/send \
#   -H "Content-Type: application/json" \
#   -d '{"to":"+61426367966","text":"Hi, I’m an AI-powered SMS assistant configured by Karol, here to help."}'