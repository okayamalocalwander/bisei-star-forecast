"""天気・月・天体イベントの情報から「星空指数」を算出する。"""
from __future__ import annotations

import datetime

from . import astro, config, conjunctions, events

_WEATHER_BASE_SCORE = {
    "快晴": 100,
}


def _weather_base_score(weather_text: str) -> float:
    if weather_text is None:
        return None
    if "雨" in weather_text or "雪" in weather_text:
        return 15
    if "快晴" in weather_text:
        return 100
    if "曇" in weather_text and "晴" in weather_text:
        return 55
    if "曇" in weather_text:
        return 30
    if "晴" in weather_text:
        return 85
    return 50


def _weather_score(weather_entry: dict) -> float | None:
    if not weather_entry or "weather_text" not in weather_entry:
        return None
    score = _weather_base_score(weather_entry["weather_text"])
    if score is None:
        return None
    pop = weather_entry.get("pop")
    if pop is not None:
        score -= pop * 0.3
    return max(0, min(100, score))


def _moon_score(moon_info: dict) -> float:
    return round(100 * (1 - moon_info["interference_fraction"]))


def compute_day_score(date: datetime.date, weather_entry: dict | None, horizon_days: int, location_key: str) -> dict:
    """1日分の星空指数と内訳を、指定した観測スポットについて計算する。"""
    location = config.LOCATIONS[location_key]
    moon_info = astro.get_moon_info(
        date, location["lat"], location["lon"], location["elevation"], location["direction_visibility"]
    )
    moon_score = _moon_score(moon_info)
    weather_score = _weather_score(weather_entry)
    day_events = events.get_events_for_date(date) + conjunctions.get_events_for_date(
        date, location["lat"], location["lon"], location["elevation"]
    )
    event_bonus = 10 if day_events else 0

    weather_available = weather_score is not None
    if weather_available:
        total = weather_score * 0.55 + moon_score * 0.35 + event_bonus
    else:
        # 天気予報がまだ出ていない先の日付は、月の条件のみを参考値として使う
        total = moon_score * 0.7 + event_bonus
    total = round(max(0, min(100, total)))

    return {
        "date": date,
        "location": location_key,
        "location_note": location["note"],
        "total_score": total,
        "label": _label_for_score(total),
        "weather_available": weather_available,
        "weather_score": weather_score,
        "weather_text": (weather_entry or {}).get("weather_text"),
        "pop": (weather_entry or {}).get("pop"),
        "weather_area": (weather_entry or {}).get("area_name"),
        "moon_score": moon_score,
        "moon_illumination_pct": moon_info["illumination_pct"],
        "moon_age_days": moon_info["moon_age_days"],
        "moon_waxing": moon_info["waxing"],
        "moonrise": moon_info["moonrise"],
        "moonset": moon_info["moonset"],
        "moon_sector": moon_info["moon_sector"],
        "moon_altitude_deg": moon_info["moon_altitude_deg"],
        "dusk": moon_info["dusk"],
        "dawn": moon_info["dawn"],
        "events": day_events,
    }


def compute_day_scores_all_locations(date: datetime.date, weather_entry: dict | None, horizon_days: int) -> list:
    """全観測スポットについて1日分のスコアを計算し、指数の高い順に返す。"""
    scores = [
        compute_day_score(date, weather_entry, horizon_days, loc)
        for loc in config.LOCATIONS
    ]
    return sorted(scores, key=lambda d: d["total_score"], reverse=True)


def _label_for_score(score: int) -> str:
    if score >= 80:
        return "絶好の星空日和"
    if score >= 60:
        return "良好"
    if score >= 40:
        return "普通"
    if score >= 20:
        return "やや期待薄"
    return "厳しい空模様"


def suggest_extension(day_scores: list, lookahead_scores: list, threshold: int = 15) -> dict | None:
    """滞在最終日より後の数日間で、星空指数が大きく上回る日があれば延泊を提案する。"""
    if not day_scores or not lookahead_scores:
        return None

    checkout_score = day_scores[-1]["total_score"]
    best_after = max(lookahead_scores, key=lambda d: d["total_score"])

    if best_after["total_score"] - checkout_score >= threshold:
        return {
            "date": best_after["date"],
            "score": best_after["total_score"],
            "checkout_score": checkout_score,
            "diff": best_after["total_score"] - checkout_score,
        }
    return None
