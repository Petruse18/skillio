"""Ceasul aplicației și formatarea datelor în română.

Ceasul poate fi „dat înainte” din panoul de admin (decalaj în zile), ca să
puteți arăta la prezentare feedback-ul de după o zi, o săptămână și o lună.
"""
from datetime import date, datetime, timedelta

from . import db

ZILE = ["luni", "marți", "miercuri", "joi", "vineri", "sâmbătă", "duminică"]
ZILE_SCURT = ["L", "Ma", "Mi", "J", "V", "S", "D"]
LUNI = ["ian", "feb", "mar", "apr", "mai", "iun", "iul", "aug", "sep", "oct", "nov", "dec"]


def decalaj_zile() -> int:
    return int(db.setare("decalaj_zile", 0) or 0)


def acum() -> datetime:
    return datetime.now().replace(microsecond=0) + timedelta(days=decalaj_zile())


def azi() -> date:
    return acum().date()


def iso(dt) -> str | None:
    return dt.isoformat(timespec="seconds") if dt else None


def din_iso(s) -> datetime | None:
    return datetime.fromisoformat(s) if s else None


def zi_frumos(d, scurt=False) -> str:
    """azi / mâine / luni 16 nov"""
    if isinstance(d, str):
        d = datetime.fromisoformat(d)
    if isinstance(d, datetime):
        d = d.date()
    delta = (d - azi()).days
    if delta == 0:
        return "azi"
    if delta == 1:
        return "mâine"
    if delta == -1:
        return "ieri"
    nume = ZILE_SCURT[d.weekday()] if scurt else ZILE[d.weekday()]
    return f"{nume} {d.day} {LUNI[d.month - 1]}"


def data_ora(dt) -> str:
    """luni 16 nov, 14:00"""
    if isinstance(dt, str):
        dt = datetime.fromisoformat(dt)
    return f"{zi_frumos(dt)}, {dt:%H:%M}"


def ora(dt) -> str:
    if isinstance(dt, str):
        dt = datetime.fromisoformat(dt)
    return f"{dt:%H:%M}"


def de_cand(dt) -> str:
    """acum 5 min / acum 2 ore / acum 3 zile"""
    if isinstance(dt, str):
        dt = datetime.fromisoformat(dt)
    sec = (acum() - dt).total_seconds()
    if sec < 60:
        return "chiar acum"
    if sec < 3600:
        return f"acum {int(sec // 60)} min"
    if sec < 86400:
        h = int(sec // 3600)
        return f"acum {h} {'oră' if h == 1 else 'ore'}"
    z = int(sec // 86400)
    if z < 31:
        return f"acum {z} {'zi' if z == 1 else 'zile'}"
    l = z // 30
    return f"acum {l} {'lună' if l == 1 else 'luni'}"


def lei(x) -> str:
    return f"{x:,.0f} lei".replace(",", ".")
