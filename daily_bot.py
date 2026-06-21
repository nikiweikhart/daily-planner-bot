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


# Manueller Schulplan für die letzten zwei Schulwochen
# Nur wirklich stattfindende Termine wurden übernommen.
MANUAL_SCHOOL_SCHEDULE = {
    "2026-06-22": [
        ("08:55", "09:45", "Schule: LIE D"),
        ("09:55", "10:45", "Schule: KREI SP4"),
    ],
    "2026-06-23": [
        ("09:55", "10:45", "Schule: BUGA Ph2"),
        ("12:55", "13:45", "Schule: KREI SP4"),
        ("16:20", "17:10", "Schule: WOHL WH"),
    ],
    "2026-06-24": [
        ("08:00", "08:50", "Schule: KAVS E"),
        ("08:55", "09:45", "Schule: LIE D"),
    ],
    "2026-06-25": [
        ("12:00", "12:50", "Schule: KAVS E"),
        ("12:55", "13:45", "Schule: BUGA Ph2"),
        ("16:20", "17:10", "Schule: REIN BSK"),
    ],
    "2026-06-26": [
        ("08:55", "09:45", "Schule: LIE D"),
        ("09:55", "10:45", "Schule: KON ETH"),
    ],

    # Von dir ergänzt:
    "2026-06-29": [
        ("08:00", "11:50", "Schule"),
    ],
    "2026-06-30": [
        ("08:00", "15:30", "Schule"),
    ],
    "2026-07-01": [
        ("09:15", "12:00", "Kino: Minions-Film"),
    ],

    "2026-07-02": [
        ("08:55", "09:45", "Schule: DEL Ch"),
        ("09:55", "10:45", "Schule: DEL M"),
        ("11:00", "11:50", "Schule: BLA GWB"),
    ],
    "2026-07-03": [
        ("08:55", "09:45", "Schule: LIE D"),
    ],
}


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


def parse_time_for_day(target_day, time_text):
    hour, minute = map(int, time_text.split(":"))
    return datetime(
        target_day.year,
        target_day.month,
        target_day.day,
        hour,
        minute,
        tzinfo=TIMEZONE
    )


def get_manual_school_events_for_day(target_day):
    date_key = target_day.strftime("%Y-%m-%d")
    school_entries = MANUAL_SCHOOL_SCHEDULE.get(date_key, [])

    events = []

    for start_text, end_text, title in school_entries:
        start = parse_time_for_day(target_day, start_text)
        end = parse_time_for_day(target_day, end_text)

        events.append({
            "title": title,
            "start": start,
            "end": end,
            "source": "manual"
        })

    return events


def get_calendar_events_for_day(target_day):
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
                    "end": end,
                    "source": "calendar"
                })

        except Exception:
            continue

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
    test_dates = [
        date(2026, 6, 26),
        date(2026, 6, 30),
    ]

    lines = []
    lines.append("Kalender-Test für 26.06. und 30.06.:")
    lines.append("")

    for target_day in test_dates:
        manual_events = get_manual_school_events_for_day(target_day)
        calendar_events = get_calendar_events_for_day(target_day)

        all_events = manual_events + calendar_events
        all_events.sort(key=lambda event: event["start"])

        lines.append(f"{target_day.strftime('%d.%m.%Y')}:")
        
        if not all_events:
            lines.append("Keine Termine eingetragen.")
        else:
            for event in all_events:
                lines.append(format_event(event))

        lines.append("")

    return "\n".join(lines)


if __name__ == "__main__":
    message = build_message()
    send_telegram_message(message)
