from zoneinfo import ZoneInfo

TOWN_NAME = "美星町（岡山県井原市）"

TIMEZONE = "Asia/Tokyo"
JST = ZoneInfo(TIMEZONE)

# 気象庁 天気予報API（岡山県）。3スポットとも同じ気象庁予報区（岡山県南部）を利用する。
JMA_AREA_CODE = "330000"
JMA_FORECAST_URL = f"https://www.jma.go.jp/bosai/forecast/data/forecast/{JMA_AREA_CODE}.json"

# 天気予報が意味を持つ日数（これを超える先の日付は参考値のみ表示）
WEATHER_FORECAST_HORIZON_DAYS = 7

# 天文薄明（この太陽高度より下がると空が十分に暗くなる）
ASTRONOMICAL_TWILIGHT_HORIZON = "-18"

# direction_visibility: 8方位ごとの「その地点からの見やすさ」(0=見えにくい〜1=よく見える)。
# ユーザーからのヒアリングに基づく定性的な情報を数値化した近似値。
# 明示されていない方角は概ね見える想定でデフォルト0.6としている。
_DEFAULT_VISIBILITY = 0.6

LOCATIONS = {
    "美星天文台": {
        "lat": 34.671981,
        "lon": 133.545365,
        "elevation": 490,
        "note": "比較的どの角度の星も見える。西の空はやや見にくい。",
        "direction_visibility": {
            "N": 0.85, "NE": 0.85, "E": 0.85, "SE": 0.85,
            "S": 0.85, "SW": 0.7, "W": 0.4, "NW": 0.7,
        },
    },
    "星空公園": {
        "lat": 34.679972,
        "lon": 133.571113,
        "elevation": 512,
        "note": "東の空が見やすい。",
        "direction_visibility": {
            "N": _DEFAULT_VISIBILITY, "NE": 0.85, "E": 0.95, "SE": 0.85,
            "S": _DEFAULT_VISIBILITY, "SW": _DEFAULT_VISIBILITY, "W": _DEFAULT_VISIBILITY, "NW": _DEFAULT_VISIBILITY,
        },
    },
    "竜王山公園": {
        "lat": 34.6330846,
        "lon": 133.5260956,
        "elevation": 400,
        "note": "南の空が見やすい。",
        "direction_visibility": {
            "N": _DEFAULT_VISIBILITY, "NE": _DEFAULT_VISIBILITY, "E": _DEFAULT_VISIBILITY, "SE": 0.85,
            "S": 0.95, "SW": 0.85, "W": _DEFAULT_VISIBILITY, "NW": _DEFAULT_VISIBILITY,
        },
    },
}
