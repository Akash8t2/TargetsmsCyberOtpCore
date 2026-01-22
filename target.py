#!/usr/bin/env python3
import requests
import time
import re
import logging
import json
import os
from datetime import datetime

# ================= CONFIG =================

AJAX_URL = "http://51.75.55.16/ints/client/res/data_smscdr.php"

BOT_TOKEN = os.getenv("BOT_TOKEN") or "YOUR_BOT_TOKEN"
CHAT_ID = os.getenv("CHAT_ID") or "-100XXXXXXXXXX"

COOKIES = {
    "PHPSESSID": os.getenv("PHPSESSID") or "PUT_SESSION_HERE"
}

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "X-Requested-With": "XMLHttpRequest",
    "Accept": "application/json"
}

CHECK_INTERVAL = 10
STATE_FILE = "state.json"

SUPPORT_URL = "https://t.me/botcasx"
NUMBERS_URL = "https://t.me/CyberOTPCore"

# ================= LOGGING =================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

# ================= SESSION =================

session = requests.Session()
session.headers.update(HEADERS)
session.cookies.update(COOKIES)

# ================= STATE =================

def load_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE) as f:
                return json.load(f)
        except Exception:
            pass
    return {"last_uid": None}

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)

STATE = load_state()

# ================= HELPERS =================

def extract_otp(text):
    if not text:
        return "N/A"
    m = re.search(r"\b(\d{4,8})\b", text)
    return m.group(1) if m else "N/A"

def build_params():
    today = datetime.now().strftime("%Y-%m-%d")
    return {
        "fdate1": f"{today} 00:00:00",
        "fdate2": f"{today} 23:59:59",
        "iDisplayStart": 0,
        "iDisplayLength": 25,
        "iSortCol_0": 0,
        "sSortDir_0": "desc",
        "iSortingCols": 1
    }

def format_message(row):
    date = row[0]
    route = row[1]
    number = row[2]
    service = row[3]
    message = row[4]

    if not number.startswith("+"):
        number = "+" + number

    otp = extract_otp(message)
    country = route.split()[0]

    return (
        "📩 *LIVE OTP RECEIVED*\n\n"
        f"📞 *Number:* `{number}`\n"
        f"🔢 *OTP:* 🔥 `{otp}` 🔥\n"
        f"🏷 *Service:* {service}\n"
        f"🌍 *Route:* {route}\n"
        f"🕒 *Time:* {date}\n\n"
        f"💬 *SMS:*\n{message}\n\n"
        "⚡ *CYBER OTP CORE*"
    )

def send_telegram(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True,
        "reply_markup": {
            "inline_keyboard": [
                [
                    {"text": "🆘 Support", "url": SUPPORT_URL},
                    {"text": "📲 Numbers", "url": NUMBERS_URL}
                ]
            ]
        }
    }
    r = requests.post(url, json=payload, timeout=15)
    if not r.ok:
        logging.error("Telegram error: %s", r.text)

# ================= CORE (LIVE ONLY) =================

def fetch_latest_sms():
    global STATE

    r = session.get(AJAX_URL, params=build_params(), timeout=20)

    try:
        data = r.json()
    except Exception:
        logging.warning("Invalid JSON / Session expired")
        return

    rows = data.get("aaData", [])
    if not rows:
        return

    valid = [r for r in rows if isinstance(r, list) and len(r) >= 5 and "20" in r[0]]
    if not valid:
        return

    valid.sort(
        key=lambda x: datetime.strptime(x[0], "%Y-%m-%d %H:%M:%S"),
        reverse=True
    )

    latest = valid[0]
    uid = f"{latest[0]}|{latest[2]}|{latest[3]}|{extract_otp(latest[4])}"

    if STATE["last_uid"] is None:
        STATE["last_uid"] = uid
        save_state(STATE)
        logging.info("ONLY LIVE MODE initialized")
        return

    if uid != STATE["last_uid"]:
        STATE["last_uid"] = uid
        save_state(STATE)
        send_telegram(format_message(latest))
        logging.info("LIVE OTP SENT")

# ================= LOOP =================

logging.info("🚀 OTP BOT STARTED (51.75.55.16 | LIVE ONLY)")

while True:
    try:
        fetch_latest_sms()
    except Exception:
        logging.exception("ERROR")
    time.sleep(CHECK_INTERVAL)
