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


def get_events_for_day(target_day):
    start_of_day = datetime(
        target_day.year,
        target_day.month,
        target_day.day,
        0,
        0,
        tzinfo=TIMEZONE
    )

    end_of_day = start_of_day + timedelta(days=1)

    events = []
    seen_events = set()

    for calendar_url in calendar_urls:
        try:
            response = requests.get(calendar_url, timeout=20)
            response.raise_for_status()

            calendar = Calendar.from_ical(response.text)

            expanded_events = recurring_ical_events.of(calendar).between(
                start_of_day,
                end_of_day
            )

            for component in expanded_events:
                summary = str(component.get("summary", "Ohne Titel"))

                start_raw = component.get("dtstart")
                end_raw = component.get("dtend")

                if not start_raw:
                    continue

                start = normalize_datetime(start_raw.dt)

                if end_raw:
                    end = normalize_datetime(end_raw.dt)
                else:
                    end = start

                if start is None:
                    continue

                # Doppelte Termine entfernen
                event_key = (
                    summary,
                    start.isoformat(),
                    end.isoformat()
                )

                if event_key in seen_events:
                    continue

                seen_events.add(event_key)

                events.append({
                    "title": summary,
                    "start": start,
                    "end": end
                })

        except Exception:
            continue

    events.sort(key=lambda event: event["start"])
    return events


def format_event(event):
    start = event["start"]
    end = event["end"]

    is_all_day = (
        start.hour == 0
        and start.minute == 0
        and end.hour == 0
        and end.minute == 0
    )

    if is_all_day:
        time_text = "Ganztägig"
    else:
        time_text = f"{start.strftime('%H:%M')}–{end.strftime('%H:%M')}"

    return f"{time_text} | {event['title']}"


def build_message():
    tomorrow = datetime.now(TIMEZONE).date() + timedelta(days=1)
    events = get_events_for_day(tomorrow)

    lines = []
    lines.append(f"Plan für morgen ({tomorrow.strftime('%d.%m.%Y')}):")
    lines.append("")

    if not events:
        lines.append("Keine Termine eingetragen.")
    else:
        for event in events:
            lines.append(format_event(event))

    return "\n".join(lines)


if __name__ == "__main__":
    message = build_message()
    send_telegram_message(message)
