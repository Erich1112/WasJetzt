from __future__ import annotations

from datetime import datetime


def now_local() -> datetime:
    """Momentul curent, cu fus orar local (aware)."""
    return datetime.now().astimezone()


def timezone_name(moment: datetime) -> str:
    """Numele IANA al fusului local dacă poate fi aflat, altfel offset-ul (ex. UTC+02:00)."""
    try:
        from tzlocal import get_localzone_name

        name = get_localzone_name()
        if name:
            return str(name)
    except Exception:  # tzlocal lipsește sau nu poate determina fusul
        pass
    return offset_label(moment)


def offset_label(moment: datetime) -> str:
    offset = moment.utcoffset()
    if offset is None:
        return "UTC"
    total = int(offset.total_seconds() // 60)
    sign = "+" if total >= 0 else "-"
    total = abs(total)
    return f"UTC{sign}{total // 60:02d}:{total % 60:02d}"
