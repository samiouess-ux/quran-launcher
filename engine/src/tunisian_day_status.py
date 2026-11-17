from __future__ import annotations

from datetime import datetime, timezone
from zoneinfo import ZoneInfo

TUNISIA_TIMEZONE = ZoneInfo("Africa/Tunis")


def tunisian_day_status(now_utc: datetime | None = None) -> dict[str, str]:
    """Return the current Tunisia-local weekday fields, with an injectable UTC clock for tests."""
    instant = now_utc if now_utc is not None else datetime.now(timezone.utc)
    if instant.tzinfo is None:
        raise ValueError("now_utc must be timezone-aware")
    local = instant.astimezone(TUNISIA_TIMEZONE)
    return {
        "is_friday": "true" if local.weekday() == 4 else "false",
        "local_date": local.date().isoformat(),
        "local_time": local.strftime("%H:%M:%S"),
    }


if __name__ == "__main__":
    status = tunisian_day_status()
    for key, value in status.items():
        print(f"{key}={value}")
