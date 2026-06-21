import os
import requests
from datetime import datetime, timedelta, date
from zoneinfo import ZoneInfo
from icalendar import Calendar
import recurring_ical_events

TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

calendar_urls_raw = os.environ.get("APPLE_CALENDAR_ICS_URLS", "")
calendar_urls = [url.strip() for url in calendar_urls_raw.splitlines() if url.strip()]

TIMEZONE = ZoneInfo("Europe/Vienna")


def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text
    }
    response = requests.post(url, data=data)
    response.raise_for_status()


def normalize_datetime(value):
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=TIMEZONE)
        return value.astimezone(TIMEZONE)

    if isinstance(value, date):
        return datetime(value.year, value.month, value.day, 0, 0, tzinfo=TIMEZONE)

    return None


def format_event(component, calendar_index):
    summary = str(component.get("summary", "Ohne Titel"))

    start_raw = component.get("dtstart")
    end_raw = component.get("dtend")

    if not start_raw:
        return None

    start = normalize_datetime(start_raw.dt)

    if end_raw:
        end = normalize_datetime(end_raw.dt)
    else:
        end = start

    if start is None:
        return None

    if start.hour == 0 and start.minute == 0 and end.hour == 0 and end.minute == 0:
        time_text = "Ganztägig"
    else:
        time_text = f"{start.strftime('%H:%M')}–{end.strftime('%H:%M')}"

    return {
        "text": f"{start.strftime('%d.%m.')} {time_text} | {summary} [Kalender {calendar_index}]",
        "start": start
    }


def build_message():
    now = datetime.now(TIMEZONE)
    tomorrow = now.date() + timedelta(days=1)

    start_search = datetime(tomorrow.year, tomorrow.month, tomorrow.day, 0, 0, tzinfo=TIMEZONE)
    end_search = start_search + timedelta(days=14)

    all_events = []
    debug_lines = []

    for calendar_index, calendar_url in enumerate(calendar_urls, start=1):
        try:
            response = requests.get(calendar_url, timeout=20)
            response.raise_for_status()

            calendar = Calendar.from_ical(response.text)

            raw_events = [component for component in calendar.walk() if component.name == "VEVENT"]
            debug_lines.append(f"Kalender {calendar_index}: {len(raw_events)} Roh-Termine")

            expanded_events = recurring_ical_events.of(calendar).between(start_search, end_search)
            debug_lines.append(f"Kalender {calendar_index}: {len(expanded_events)} Termine in den nächsten 14 Tagen")

            for component in expanded_events:
                event = format_event(component, calendar_index)
                if event:
                    all_events.append(event)

        except Exception as error:
            debug_lines.append(f"Kalender {calendar_index}: Fehler - {error}")

    all_events.sort(key=lambda event: event["start"])

    lines = []
    lines.append(f"Kalender-Debug ab morgen ({tomorrow.strftime('%d.%m.%Y')}):")
    lines.append("")

    if not all_events:
        lines.append("Keine Termine in den nächsten 14 Tagen gefunden.")
    else:
        lines.append("Gefundene Termine:")
        lines.append("")
        for event in all_events[:25]:
            lines.append(event["text"])

    lines.append("")
    lines.append("--- Debug ---")
    lines.extend(debug_lines)

    return "\n".join(lines)


if __name__ == "__main__":
    message = build_message()
    send_telegram_message(message)
