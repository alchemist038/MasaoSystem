from datetime import datetime, timedelta, timezone

JST = timezone(timedelta(hours=9))

def now_jst():
    return datetime(2026, 3, 15, 10, 0, 0, tzinfo=JST) # Mock time: 15th 10:00

SCHEDULE_HOURS = [10, 14, 18]

def calc_next_publish_time(scheduled_times: set) -> datetime:
    now = now_jst()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    for days_ahead in range(30):
        day_base = today_start + timedelta(days=days_ahead)
        
        for h in SCHEDULE_HOURS:
            candidate = day_base.replace(hour=h)
            if candidate > now and candidate not in scheduled_times:
                return candidate
    return now + timedelta(hours=4)

scheduled = {
    datetime(2026, 3, 15, 10, 0, 0, tzinfo=JST),
    datetime(2026, 3, 15, 14, 0, 0, tzinfo=JST),
}

print(calc_next_publish_time(scheduled))
