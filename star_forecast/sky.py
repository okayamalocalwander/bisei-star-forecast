"""その日時に空に見えている恒星・惑星をリストアップするモジュール。

3つの観測スポットは数kmしか離れておらず、見えている星そのものは共通（同じ空）。
違うのは「その方角が地形的に見やすいか」だけなので、天体の一覧は共通の代表地点で
一度だけ計算し、地点ごとの見やすさは方角ごとの重みで後から注釈を付ける。
"""
import datetime

import ephem

from . import astro

MIN_ALTITUDE_DEG = 15  # これより低いと木立や山に隠れやすく、観光客には見えにくいとみなす

# 日本から見やすい主要な恒星（ephemの内蔵カタログ名 -> 和名・星座・見頃の季節）
STAR_CATALOG = [
    {"name": "Sirius", "jp": "シリウス", "constellation": "おおいぬ座", "season": "冬"},
    {"name": "Betelgeuse", "jp": "ベテルギウス", "constellation": "オリオン座", "season": "冬"},
    {"name": "Rigel", "jp": "リゲル", "constellation": "オリオン座", "season": "冬"},
    {"name": "Aldebaran", "jp": "アルデバラン", "constellation": "おうし座", "season": "冬"},
    {"name": "Capella", "jp": "カペラ", "constellation": "ぎょしゃ座", "season": "冬"},
    {"name": "Procyon", "jp": "プロキオン", "constellation": "こいぬ座", "season": "冬"},
    {"name": "Pollux", "jp": "ポルックス", "constellation": "ふたご座", "season": "冬"},
    {"name": "Castor", "jp": "カストル", "constellation": "ふたご座", "season": "冬"},
    {"name": "Canopus", "jp": "カノープス", "constellation": "りゅうこつ座", "season": "冬（南の低空）"},
    {"name": "Regulus", "jp": "レグルス", "constellation": "しし座", "season": "春"},
    {"name": "Arcturus", "jp": "アークトゥルス", "constellation": "うしかい座", "season": "春"},
    {"name": "Spica", "jp": "スピカ", "constellation": "おとめ座", "season": "春"},
    {"name": "Denebola", "jp": "デネボラ", "constellation": "しし座", "season": "春"},
    {"name": "Antares", "jp": "アンタレス", "constellation": "さそり座", "season": "夏"},
    {"name": "Vega", "jp": "ベガ（織姫星）", "constellation": "こと座", "season": "夏"},
    {"name": "Altair", "jp": "アルタイル（彦星）", "constellation": "わし座", "season": "夏"},
    {"name": "Deneb", "jp": "デネブ", "constellation": "はくちょう座", "season": "夏"},
    {"name": "Fomalhaut", "jp": "フォーマルハウト", "constellation": "みなみのうお座", "season": "秋"},
    {"name": "Polaris", "jp": "北極星", "constellation": "こぐま座", "season": "通年"},
]

PLANETS = [
    {"name": "Venus", "jp": "金星", "factory": ephem.Venus},
    {"name": "Mars", "jp": "火星", "factory": ephem.Mars},
    {"name": "Jupiter", "jp": "木星", "factory": ephem.Jupiter},
    {"name": "Saturn", "jp": "土星", "factory": ephem.Saturn},
]

# 複数の代表的な星がそろって見えているときに知らせる有名なアステリズム（星の並び）
ASTERISMS = [
    ("夏の大三角", {"Vega", "Altair", "Deneb"}),
    ("冬の大三角", {"Sirius", "Betelgeuse", "Procyon"}),
    ("春の大三角", {"Arcturus", "Spica", "Denebola"}),
]

_VISIBILITY_LABELS = [
    (0.8, "◎ 見やすい"),
    (0.5, "○ 普通"),
    (0.0, "△ やや見えにくい"),
]


def generate_time_slots(dusk, dawn, step_hours: int = 2) -> list:
    """天文薄明の時間帯内で、時刻の切りが良い（毎時0分の）時間帯リストを返す。"""
    if dusk is None or dawn is None:
        return []
    start = (dusk + datetime.timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)
    slots = []
    t = start
    while t <= dawn:
        slots.append(t)
        t += datetime.timedelta(hours=step_hours)
    return slots


def get_sky_objects(dt_jst: datetime.datetime, lat: float, lon: float, elevation: float) -> dict:
    """指定した日時・場所で地平線上（高度15°以上）に見えている星・惑星の一覧と、
    そろい踏みしているアステリズムを返す。方角による見やすさの補正は含まない。
    """
    dt_utc = dt_jst.astimezone(datetime.timezone.utc).replace(tzinfo=None)
    observer = astro.make_observer(dt_utc, lat, lon, elevation)

    visible_stars = []
    visible_names = set()
    for star_def in STAR_CATALOG:
        body = ephem.star(star_def["name"])
        body.compute(observer)
        alt_deg = float(body.alt) * astro.RAD2DEG
        if alt_deg < MIN_ALTITUDE_DEG:
            continue
        az_deg = float(body.az) * astro.RAD2DEG
        visible_stars.append(
            {
                "type": "star",
                "jp": star_def["jp"],
                "constellation": star_def["constellation"],
                "season": star_def["season"],
                "altitude": round(alt_deg),
                "sector": astro.compass_sector(az_deg),
            }
        )
        visible_names.add(star_def["name"])
    visible_stars.sort(key=lambda s: s["altitude"], reverse=True)

    visible_planets = []
    for planet_def in PLANETS:
        body = planet_def["factory"]()
        body.compute(observer)
        alt_deg = float(body.alt) * astro.RAD2DEG
        if alt_deg < MIN_ALTITUDE_DEG:
            continue
        az_deg = float(body.az) * astro.RAD2DEG
        visible_planets.append(
            {
                "type": "planet",
                "jp": planet_def["jp"],
                "constellation": None,
                "season": None,
                "altitude": round(alt_deg),
                "sector": astro.compass_sector(az_deg),
            }
        )
    visible_planets.sort(key=lambda p: p["altitude"], reverse=True)

    asterisms = [label for label, names in ASTERISMS if names.issubset(visible_names)]

    return {"time": dt_jst, "stars": visible_stars, "planets": visible_planets, "asterisms": asterisms}


def annotate_visibility(sky_objects: dict, direction_visibility: dict) -> dict:
    """観測スポットごとの方角の見やすさで、各天体に見やすさラベルを付与する。"""
    annotated = {**sky_objects}
    for key in ("stars", "planets"):
        annotated[key] = [
            {**obj, "visibility_label": _label_for_weight(direction_visibility.get(obj["sector"], 0.6))}
            for obj in sky_objects[key]
        ]
    return annotated


def _label_for_weight(weight: float) -> str:
    for threshold, label in _VISIBILITY_LABELS:
        if weight >= threshold:
            return label
    return _VISIBILITY_LABELS[-1][1]
