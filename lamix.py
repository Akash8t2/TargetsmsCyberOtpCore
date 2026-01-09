#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
NumberPanel OTP Bot
Mode: LAST 3 OTP ONLY
Heroku Anti-Empty-Response Version
"""

import time
import json
import re
import requests
from datetime import datetime

# ================= CONFIG =================
BASE_URL = "http://51.89.99.105/NumberPanel"
API_URL = "http://51.89.99.105/NumberPanel/client/res/data_smscdr.php"

PHPSESSID = "ct38cra540a4hil76g82dirrft"
BOT_TOKEN = "7448362382:AAGzYcF4XH5cAOIOsrvJ6E9MXqjnmOdKs2o"

CHAT_ID = "-1003405109562"
CHECK_INTERVAL = 12
STATE_FILE = "state.json"

# ================= HEADERS =================
HEADERS = {
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "X-Requested-With": "XMLHttpRequest",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Referer": f"{BASE_URL}/client/SMSDashboard",
    "Accept-Encoding": "identity",   # 🔥 gzip OFF
    "Connection": "close",            # 🔥 keep-alive OFF
}

# ================= HELPERS =================
def load_state():
    try:
        return json.load(open(STATE_FILE))
    except Exception:
        return {"sent": []}

def save_state(state):
    json.dump(state, open(STATE_FILE, "w"))

def extract_otp(text):
    if not text:
        return None
    m = re.search(r"\b(\d{3,4}[-\s]?\d{3,4})\b", text)
    return m.group(1) if m else None

def send_telegram(msg):
    r = requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
        json={
            "chat_id": CHAT_ID,
            "text": msg,
            "parse_mode": "Markdown",
            "disable_web_page_preview": True
        },
        timeout=10
    )
    print("📤 Telegram:", r.status_code)

# ================= START =================
print("🚀 NumberPanel OTP Bot Started")
print("⚡ Mode: LAST 3 OTP ONLY")
print("📢 Group:", CHAT_ID)

state = load_state()
sent = state["sent"]

while True:
    try:
        # 🔥 NEW SESSION PER REQUEST (IMPORTANT)
        cookies = {
            "PHPSESSID": PHPSESSID
        }

        params = {
            "fdate1": "2025-01-01 00:00:00",
            "fdate2": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "iDisplayStart": 0,
            "iDisplayLength": 3,
            "sEcho": 1,
            "_": int(time.time() * 1000),
        }

        r = requests.get(
            API_URL,
            headers=HEADERS,
            cookies=cookies,
            params=params,
            timeout=10
        )

        if not r.text or not r.text.strip():
            print("⚠️ Empty response (server dropped body)")
            time.sleep(CHECK_INTERVAL)
            continue

        if "login" in r.text.lower():
            print("🔐 SESSION EXPIRED — UPDATE PHPSESSID")
            time.sleep(60)
            continue

        try:
            data = r.json()
        except Exception:
            print("⚠️ Non-JSON response")
            print(r.text[:200])
            time.sleep(CHECK_INTERVAL)
            continue

        rows = data.get("aaData", [])
        if not rows:
            time.sleep(CHECK_INTERVAL)
            continue

        rows.reverse()  # oldest → newest

        for row in rows:
            ts, pool, number, service, message = row[:5]
            key = f"{number}_{ts}"

            if key in sent:
                continue

            otp = extract_otp(message)
            print("🧾 SMS:", message)

            if otp:
                msg = (
                    f"🔐 *NEW OTP RECEIVED*\n"
                    f"━━━━━━━━━━━━━━\n"
                    f"🕒 `{ts}`\n"
                    f"📞 `{number}`\n"
                    f"📲 `{service}`\n"
                    f"🔢 *OTP:* `{otp}`\n"
                )
                send_telegram(msg)

            sent.append(key)

        sent = sent[-10:]
        save_state({"sent": sent})

    except Exception as e:
        print("💥 ERROR:", e)

    time.sleep(CHECK_INTERVAL)
