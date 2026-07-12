"""気象庁MSM（メソモデル）の実況〜短期の雲データから、当日の時間別の雲量を取得するモジュール。

データ提供元: 京都大学生存圏研究所 生存圏データベース（気象庁データの非公式ミラー）
  http://database.rish.kyoto-u.ac.jp/arch/jmadata/
  ※このミラーは教育研究機関向けに提供されているもので、商用利用の可否は明記されていない。
    本番運用時は気象業務支援センター(JMBSC)との正規契約への切り替えを想定したプロトタイプ実装。

「latest/MSM-S.nc」は、直近のMSM解析〜予報をつないだローリング更新ファイル（1日あたり数回更新、
向こう34時間分の実況+短期予報を含む）で、当日の時間別の雲の動きを見るのに適している。
"""
import datetime
import os
import tempfile
import time

import numpy as np
import requests
from scipy.io import netcdf_file

from . import config

MSM_LATEST_URL = "http://database.rish.kyoto-u.ac.jp/arch/jmadata/data/gpv/latest/MSM-S.nc"
_CACHE_PATH = os.path.join(tempfile.gettempdir(), "bisei_star_forecast_msm_latest.nc")
_CACHE_TTL_SECONDS = 3 * 60 * 60  # MSMはおよそ3時間おきに更新される

ATTRIBUTION = "気象庁MSMデータ（京都大学生存圏研究所ミラー経由・非公式）"


class CloudDataUnavailable(Exception):
    pass


def _ensure_cache() -> str:
    """ローカルキャッシュが古い/存在しない場合のみ、最新のMSMファイルをダウンロードする。"""
    if os.path.exists(_CACHE_PATH):
        age = time.time() - os.path.getmtime(_CACHE_PATH)
        if age < _CACHE_TTL_SECONDS:
            return _CACHE_PATH

    tmp_path = _CACHE_PATH + ".tmp"
    try:
        with requests.get(MSM_LATEST_URL, stream=True, timeout=60) as resp:
            resp.raise_for_status()
            with open(tmp_path, "wb") as f:
                for chunk in resp.iter_content(chunk_size=1024 * 1024):
                    f.write(chunk)
        os.replace(tmp_path, _CACHE_PATH)
    except requests.RequestException as exc:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        if os.path.exists(_CACHE_PATH):
            return _CACHE_PATH  # 取得失敗時は古いキャッシュがあればそれを使う
        raise CloudDataUnavailable("MSMデータの取得に失敗しました") from exc

    return _CACHE_PATH


def _nearest_index(values: np.ndarray, target: float) -> int:
    return int(np.argmin(np.abs(values - target)))


def get_hourly_cloud_forecast(lat: float, lon: float) -> list:
    """指定した地点に最も近いMSM格子点の、時間別の雲量データを返す。

    各要素: {"time": JSTのdatetime, "total_cloud_pct", "low_pct", "mid_pct", "upper_pct"}
    MSMのローリングデータの範囲（実況〜向こう34時間程度）に含まれる時刻のみ返る。
    """
    path = _ensure_cache()
    f = netcdf_file(path, mmap=True, mode="r")

    lat_values = f.variables["lat"][:].copy()
    lon_values = f.variables["lon"][:].copy()
    ilat = _nearest_index(lat_values, lat)
    ilon = _nearest_index(lon_values, lon)

    time_var = f.variables["time"]
    base_str = time_var.units.decode() if isinstance(time_var.units, bytes) else time_var.units
    base_str = base_str.replace("hours since ", "")
    base_utc = datetime.datetime.fromisoformat(base_str).replace(tzinfo=datetime.timezone.utc)
    hours = time_var[:].copy()

    def _scaled(name):
        var = f.variables[name]
        raw = var[:, ilat, ilon].copy().astype(float)
        scale = getattr(var, "scale_factor", 1.0)
        offset = getattr(var, "add_offset", 0.0)
        return raw * scale + offset

    total = _scaled("clda")
    low = _scaled("ncld_low")
    mid = _scaled("ncld_mid")
    upper = _scaled("ncld_upper")

    records = []
    for i, h in enumerate(hours):
        dt_utc = base_utc + datetime.timedelta(hours=float(h))
        dt_jst = dt_utc.astimezone(config.JST)
        records.append(
            {
                "time": dt_jst,
                "total_cloud_pct": round(max(0.0, min(100.0, total[i])), 1),
                "low_pct": round(max(0.0, min(100.0, low[i])), 1),
                "mid_pct": round(max(0.0, min(100.0, mid[i])), 1),
                "upper_pct": round(max(0.0, min(100.0, upper[i])), 1),
            }
        )
    return records


def viewing_expectation(total_cloud_pct: float) -> tuple:
    """全雲量(%)から、その時間の観望期待度スコア(0-100)とラベルを返す。"""
    score = round(max(0.0, min(100.0, 100 - total_cloud_pct)))
    if score >= 80:
        label = "絶好"
    elif score >= 60:
        label = "良好"
    elif score >= 40:
        label = "普通"
    elif score >= 20:
        label = "やや厳しい"
    else:
        label = "厳しい"
    return score, label
