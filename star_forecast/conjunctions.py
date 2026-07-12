"""月・惑星同士の「合」（接近）や、外惑星の「衝」を ephem で自前計算するモジュール。

流星群のような毎年ほぼ同じ日付のイベントは events.py の静的カレンダーで扱うが、
合・衝は年によって日付が変わるため、既に使っている ephem のその場計算で求める。
"""
import datetime
import itertools

import ephem

from . import astro, config

_BODIES = [
    ("Moon", "月", ephem.Moon),
    ("Venus", "金星", ephem.Venus),
    ("Mars", "火星", ephem.Mars),
    ("Jupiter", "木星", ephem.Jupiter),
    ("Saturn", "土星", ephem.Saturn),
]

_OPPOSITION_PLANETS = [("Mars", "火星"), ("Jupiter", "木星"), ("Saturn", "土星")]

MOON_CONJUNCTION_THRESHOLD_DEG = 5.0
PLANET_CONJUNCTION_THRESHOLD_DEG = 3.0
OPPOSITION_THRESHOLD_DEG = 178.0


def get_events_for_date(date: datetime.date, lat: float, lon: float, elevation: float) -> list:
    """その日の21時（JST）時点での、月・惑星の接近（合）や外惑星の衝を返す。"""
    ref_local = datetime.datetime.combine(date, datetime.time(21, 0), tzinfo=config.JST)
    ref_utc = ref_local.astimezone(datetime.timezone.utc).replace(tzinfo=None)
    observer = astro.make_observer(ref_utc, lat, lon, elevation)

    bodies = {}
    for name, jp, factory in _BODIES:
        body = factory()
        body.compute(observer)
        bodies[name] = (jp, body)

    events = []
    for name1, name2 in itertools.combinations(bodies.keys(), 2):
        jp1, body1 = bodies[name1]
        jp2, body2 = bodies[name2]
        sep_deg = float(ephem.separation(body1, body2)) * astro.RAD2DEG
        threshold = MOON_CONJUNCTION_THRESHOLD_DEG if "Moon" in (name1, name2) else PLANET_CONJUNCTION_THRESHOLD_DEG
        if sep_deg < threshold:
            events.append(f"{jp1}と{jp2}が接近（角距離約{sep_deg:.1f}°）")

    sun = ephem.Sun()
    sun.compute(observer)
    for name, jp in _OPPOSITION_PLANETS:
        _, body = bodies[name]
        sep_from_sun = float(ephem.separation(sun, body)) * astro.RAD2DEG
        if sep_from_sun > OPPOSITION_THRESHOLD_DEG:
            events.append(f"{jp}が衝（一晩中見え、観測の好機）")

    return events
