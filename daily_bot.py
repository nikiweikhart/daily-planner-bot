import os
import requests
from datetime import datetime

BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

today = datetime.now().strftime("%d.%m.%Y")

message = f"""Guten Morgen!

Dein Tagesplaner-Bot funktioniert.
Heute ist der {today}.

Das ist erstmal nur ein Test. Danach bauen wir Kalender, Schule und Obsidian ein.
"""

url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

response = requests.post(url, data={
    "chat_id": CHAT_ID,
    "text": message
})

if response.status_code != 200:
    raise Exception(f"Telegram error: {response.text}")

print("Message sent successfully.")
