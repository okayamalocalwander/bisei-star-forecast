"""月齢・月の出没・天文薄明などの天体計算モジュール（ephem使用）。

観測地点（美星天文台／星空公園／竜王山公園）ごとに、緯度経度がわずかに異なるだけでなく
「どの方角の空が見やすいか」が異なるため、月がどの方角にあるかも加味して
その地点での月明かりの影響度を計算する。
"""
import datetime
import math

import ephem

from . import config

JST = config.JST
RAD2DEG = 180 / math.pi

_COMPASS_SECTORS = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]


def make_observer(dt_utc: datetime.datetime, lat: float, lon: float, elevation: float, horizon: str = "0") -> ephem.Observer:
    observer = ephem.Observer()
    observer.lat = str(lat)
    observer.lon = str(lon)
    observer.elevation = elevation
    observer.horizon = horizon
    observer.date = dt_utc
    return observer


def _local_noon_utc(date: datetime.date) -> datetime.datetime:
    local = datetime.datetime.combine(date, datetime.time(12, 0), tzinfo=JST)
    return local.astimezone(datetime.timezone.utc).replace(tzinfo=None)


def compass_sector(azimuth_deg: float) -> str:
    idx = int(((azimuth_deg + 22.5) % 360) // 45)
    return _COMPASS_SECTORS[idx]


def get_dark_window(date: datetime.date, lat: float, lon: float, elevation: float):
    """その日の夜〜翌朝における天文薄明の開始・終了時刻（JST）を返す。

    (dusk, dawn) のタプル。計算できない場合は (None, None)。
    """
    observer = make_observer(
        _local_noon_utc(date), lat, lon, elevation, horizon=config.ASTRONOMICAL_TWILIGHT_HORIZON
    )
    try:
        dusk_utc = observer.next_setting(ephem.Sun(), use_center=True)
        dawn_utc = observer.next_rising(ephem.Sun(), use_center=True)
    except (ephem.AlwaysUpError, ephem.NeverUpError):
        return None, None

    dusk = dusk_utc.datetime().replace(tzinfo=datetime.timezone.utc).astimezone(JST)
    dawn = dawn_utc.datetime().replace(tzinfo=datetime.timezone.utc).astimezone(JST)
    if dawn <= dusk:
        dawn += datetime.timedelta(days=1)
    return dusk, dawn


def get_moon_info(date: datetime.date, lat: float, lon: float, elevation: float, direction_visibility: dict = None) -> dict:
    """月齢・輝面比・月の出没・暗夜時間帯における月の干渉度合いを、指定地点について返す。

    direction_visibility を渡すと、月がその地点で見やすい方角にあるほど干渉度が高く、
    見えにくい方角にあるほど干渉度が低くなるよう補正する。
    """
    dusk, dawn = get_dark_window(date, lat, lon, elevation)

    ref_local = datetime.datetime.combine(date, datetime.time(21, 0), tzinfo=JST)
    ref_utc = ref_local.astimezone(datetime.timezone.utc).replace(tzinfo=None)
    observer = make_observer(ref_utc, lat, lon, elevation)
    moon = ephem.Moon(observer)
    illumination = moon.phase  # 輝面比（%、0=新月 100=満月）

    moon_age_days = _moon_age(ref_utc)

    rise_str = set_str = "―"
    try:
        rise_utc = observer.next_rising(ephem.Moon())
        rise_str = _to_jst_str(rise_utc)
    except (ephem.AlwaysUpError, ephem.NeverUpError):
        pass
    try:
        set_utc = observer.next_setting(ephem.Moon())
        set_str = _to_jst_str(set_utc)
    except (ephem.AlwaysUpError, ephem.NeverUpError):
        pass

    interference = _moon_interference_fraction(dusk, dawn, illumination, lat, lon, elevation, direction_visibility)
    ref_sector, ref_alt = _moon_position_at_midpoint(dusk, dawn, lat, lon, elevation)

    return {
        "illumination_pct": round(illumination, 1),
        "moon_age_days": round(moon_age_days, 1),
        "waxing": moon_age_days < 14.765,  # 新月から満月に向かう途中かどうか
        "moonrise": rise_str,
        "moonset": set_str,
        "interference_fraction": interference,  # 0=月の影響なし 1=影響大
        "dusk": dusk,
        "dawn": dawn,
        "moon_sector": ref_sector,  # 観測に適した時間帯の中間時点での月の方角（8方位）
        "moon_altitude_deg": ref_alt,
    }


def _moon_age(ref_utc: datetime.datetime) -> float:
    prev_new_moon = ephem.previous_new_moon(ref_utc)
    return (ref_utc - prev_new_moon.datetime()).total_seconds() / 86400


def _to_jst_str(ephem_date: ephem.Date) -> str:
    dt = ephem_date.datetime().replace(tzinfo=datetime.timezone.utc).astimezone(JST)
    return dt.strftime("%H:%M")


def _moon_interference_fraction(
    dusk, dawn, illumination_pct: float, lat: float, lon: float, elevation: float,
    direction_visibility: dict = None, samples: int = 8,
) -> float:
    """暗夜時間帯のうち、月が出ていて・かつその地点から見やすい方角にある割合 × 輝面比 で
    月による影響度を0〜1で近似する（見やすい方角に月があるほど、明るさの影響を強く受けると仮定）。
    """
    if dusk is None or dawn is None:
        return illumination_pct / 100.0

    weighted_up = 0.0
    total_seconds = (dawn - dusk).total_seconds()
    for i in range(samples):
        t = dusk + datetime.timedelta(seconds=total_seconds * i / (samples - 1))
        t_utc = t.astimezone(datetime.timezone.utc).replace(tzinfo=None)
        observer = make_observer(t_utc, lat, lon, elevation)
        moon = ephem.Moon(observer)
        alt_deg = float(moon.alt) * RAD2DEG
        if alt_deg <= 0:
            continue
        if direction_visibility:
            az_deg = float(moon.az) * RAD2DEG
            weight = direction_visibility.get(compass_sector(az_deg), 0.6)
        else:
            weight = 1.0
        weighted_up += weight

    up_fraction = weighted_up / samples
    return round(up_fraction * (illumination_pct / 100.0), 2)


def _moon_position_at_midpoint(dusk, dawn, lat: float, lon: float, elevation: float):
    if dusk is None or dawn is None:
        return None, None
    midpoint = dusk + (dawn - dusk) / 2
    t_utc = midpoint.astimezone(datetime.timezone.utc).replace(tzinfo=None)
    observer = make_observer(t_utc, lat, lon, elevation)
    moon = ephem.Moon(observer)
    alt_deg = float(moon.alt) * RAD2DEG
    if alt_deg <= 0:
        return None, None
    az_deg = float(moon.az) * RAD2DEG
    return compass_sector(az_deg), round(alt_deg)
