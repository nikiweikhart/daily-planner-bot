import os
import requests

TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

calendar_urls_raw = os.environ.get("APPLE_CALENDAR_ICS_URLS", "")
calendar_urls = [url.strip() for url in calendar_urls_raw.splitlines() if url.strip()]


def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

    data = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text
    }

    response = requests.post(url, data=data)
    response.raise_for_status()


def test_calendars():
    message_lines = []

    message_lines.append("Kalender-Test:")
    message_lines.append(f"Gefundene Kalender: {len(calendar_urls)}")
    message_lines.append("")

    for index, calendar_url in enumerate(calendar_urls, start=1):
        try:
            response = requests.get(calendar_url, timeout=20)
            response.raise_for_status()

            if "BEGIN:VCALENDAR" in response.text:
                message_lines.append(f"Kalender {index}: erfolgreich geladen")
            else:
                message_lines.append(f"Kalender {index}: geladen, aber kein gültiger Kalender erkannt")

        except Exception as error:
            message_lines.append(f"Kalender {index}: Fehler - {error}")

    return "\n".join(message_lines)


if __name__ == "__main__":
    text = test_calendars()
    send_telegram_message(text)
