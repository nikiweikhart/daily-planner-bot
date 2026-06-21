import os
import requests
from datetime import datetime
from zoneinfo import ZoneInfo

BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

vienna_time = datetime.now(ZoneInfo("Europe/Vienna"))

weekday_names = {
    "Monday": "Montag",
    "Tuesday": "Dienstag",
    "Wednesday": "Mittwoch",
    "Thursday": "Donnerstag",
    "Friday": "Freitag",
    "Saturday": "Samstag",
    "Sunday": "Sonntag",
}

weekday = weekday_names[vienna_time.strftime("%A")]
date = vienna_time.strftime("%d.%m.%Y")

message = f"""Guten Morgen Niki 👋

Heute ist {weekday}, der {date}.

Tagesplan:
- Schule/Termine: noch nicht verbunden
- Sport: noch nicht verbunden
- Lernen: 20–30 Minuten KI oder VWA
- Lesen: 20 Minuten
- Wichtigster Fokus: eine Sache sauber erledigen

Status:
✅ Telegram funktioniert
✅ GitHub Actions funktioniert
✅ Automatischer Tagesplaner läuft grundsätzlich

Nächster Ausbau:
Kalender und Obsidian einbinden.
"""

url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

response = requests.post(url, data={
    "chat_id": CHAT_ID,
    "text": message
})

if response.status_code != 200:
    raise Exception(f"Telegram error: {response.text}")

print("Message sent successfully.")
