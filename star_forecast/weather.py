"""気象庁の天気予報JSONを取得し、日付ごとの天気概要を組み立てるモジュール。"""
import datetime

import requests

from . import config


def fetch_raw_forecast() -> list:
    """気象庁の天気予報JSON（短期＋週間）を取得する。"""
    resp = requests.get(config.JMA_FORECAST_URL, timeout=10)
    resp.raise_for_status()
    return resp.json()


def _parse_short_term(raw_short: dict) -> dict:
    """forecast[0]（当日〜3日目、時系列あり）を日付ごとの天気情報に変換する。"""
    result = {}
    area_name = None
    for series in raw_short.get("timeSeries", []):
        area = series["areas"][0]
        area_name = area_name or area.get("area", {}).get("name")
        time_defines = series["timeDefines"]

        if "weathers" in area:
            for t, weather in zip(time_defines, area["weathers"]):
                date = _to_date(t)
                result.setdefault(date, {})["weather_text"] = weather.strip()

        if "pops" in area:
            for t, pop in zip(time_defines, area["pops"]):
                if pop == "":
                    continue
                date = _to_date(t)
                result.setdefault(date, {})["pop"] = int(pop)

    for date in result:
        result[date]["area_name"] = area_name
        result[date]["source"] = "短期予報"
    return result


def _parse_weekly(raw_weekly: dict) -> dict:
    """forecast[1]（週間予報、3〜7日目）を日付ごとの天気情報に変換する。"""
    result = {}
    series = raw_weekly["timeSeries"][0]
    area = series["areas"][0]
    area_name = area.get("area", {}).get("name")
    time_defines = series["timeDefines"]

    weather_codes = area.get("weatherCodes", [])
    pops = area.get("pops", [])

    for i, t in enumerate(time_defines):
        date = _to_date(t)
        entry = {"area_name": area_name, "source": "週間予報"}
        if i < len(weather_codes):
            entry["weather_text"] = _weather_code_to_text(weather_codes[i])
        if i < len(pops) and pops[i] not in ("", "-"):
            entry["pop"] = int(pops[i])
        result[date] = entry
    return result


def _to_date(iso_datetime: str) -> datetime.date:
    return datetime.datetime.fromisoformat(iso_datetime).date()


# 週間予報の天気コードは簡略な数値コード。主要なものだけ人が読めるテキストに変換する。
_WEATHER_CODE_MAP = {
    "100": "晴れ", "101": "晴れ時々曇り", "102": "晴れ一時雨", "103": "晴れ時々雨",
    "104": "晴れ一時雪", "105": "晴れ時々雪", "106": "晴れ一時雨か雪", "107": "晴れ時々雨か雪",
    "110": "晴れ後時々曇り", "111": "晴れ後曇り", "112": "晴れ後一時雨", "113": "晴れ後時々雨",
    "114": "晴れ後雨", "115": "晴れ後一時雪", "116": "晴れ後時々雪", "117": "晴れ後雪",
    "119": "晴れ後雨か雪", "120": "晴れ朝夕一時雨", "130": "晴れ朝の内霧後晴れ",
    "200": "曇り", "201": "曇り時々晴れ", "202": "曇り一時雨", "203": "曇り時々雨",
    "204": "曇り一時雪", "205": "曇り時々雪", "206": "曇り一時雨か雪", "207": "曇り時々雨か雪",
    "210": "曇り後時々晴れ", "211": "曇り後晴れ", "212": "曇り後一時雨", "213": "曇り後時々雨",
    "214": "曇り後雨", "215": "曇り後一時雪", "216": "曇り後時々雪", "217": "曇り後雪",
    "300": "雨", "301": "雨時々晴れ", "302": "雨時々止む", "303": "雨時々雪",
    "308": "雨で暴風を伴う", "311": "雨後晴れ", "313": "雨後曇り", "314": "雨後時々雪",
    "400": "雪", "401": "雪時々晴れ", "402": "雪時々止む", "403": "雪時々雨",
    "411": "雪後晴れ", "413": "雪後曇り", "414": "雪後雨",
}


def _weather_code_to_text(code: str) -> str:
    return _WEATHER_CODE_MAP.get(code, "不明")


def get_daily_forecast() -> dict:
    """日付(date) -> {area_name, source, weather_text, pop} の辞書を返す。

    取得に失敗した場合は空の辞書を返す（呼び出し側は「天気予報なし」として扱う）。
    """
    try:
        raw = fetch_raw_forecast()
    except (requests.RequestException, ValueError):
        return {}

    daily = {}
    if len(raw) > 0:
        daily.update(_parse_short_term(raw[0]))
    if len(raw) > 1:
        # 短期予報の日付を優先し、週間予報は不足分のみ補う
        weekly = _parse_weekly(raw[1])
        for date, entry in weekly.items():
            daily.setdefault(date, entry)
    return daily
