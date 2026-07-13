"""気象庁MSM（メソモデル）の実況〜短期の雲データから、当日の時間別の雲量を取得するモジュール。

データ提供元: 京都大学生存圏研究所 生存圏データベース（気象庁データの非公式ミラー）
  http://database.rish.kyoto-u.ac.jp/arch/jmadata/
  ※このミラーは教育研究機関向けに提供されているもので、商用利用の可否は明記されていない。
    本番運用時は気象業務支援センター(JMBSC)との正規契約への切り替えを想定したプロトタイプ実装。

「latest/MSM-S.nc」は、直近のMSM解析〜予報をつないだローリング更新ファイル（1日あたり数回更新、
向こう34時間分の実況+短期予報を含む）で、当日の時間別の雲の動きを見るのに適している。

ファイルは190MB超あり、scipy.io.netcdf_file(mmap=False)で開くと全変数・全格子点を
メモリに展開してしまいメモリ超過でクラッシュする（Streamlit Community Cloudの
無料枠で実際に発生）。そのため netcdf3.py の軽量パーサーで、必要な1格子点・
必要な変数のみをファイルから直接読み出す。
"""
import datetime
import os
import struct
import tempfile
import time

import requests

from . import config, netcdf3

MSM_LATEST_URL = "http://database.rish.kyoto-u.ac.jp/arch/jmadata/data/gpv/latest/MSM-S.nc"
_CACHE_PATH = os.path.join(tempfile.gettempdir(), "bisei_star_forecast_msm_latest.nc")
_CACHE_TTL_SECONDS = 3 * 60 * 60  # MSMはおよそ3時間おきに更新される

_CLOUD_VARS = ("clda", "ncld_low", "ncld_mid", "ncld_upper")

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


def _nearest_index(values: list, target: float) -> int:
    return min(range(len(values)), key=lambda i: abs(values[i] - target))


def get_hourly_cloud_forecast(lat: float, lon: float) -> list:
    """指定した地点に最も近いMSM格子点の、時間別の雲量データを返す。

    各要素: {"time": JSTのdatetime, "total_cloud_pct", "low_pct", "mid_pct", "upper_pct"}
    MSMのローリングデータの範囲（実況〜向こう34時間程度）に含まれる時刻のみ返る。
    """
    path = _ensure_cache()
    try:
        header = netcdf3.parse_header(path)

        lat_values = netcdf3.read_1d(path, header, "lat")
        lon_values = netcdf3.read_1d(path, header, "lon")
        ilat = _nearest_index(lat_values, lat)
        ilon = _nearest_index(lon_values, lon)

        time_values = netcdf3.read_1d(path, header, "time")
        base_str = header["variables"]["time"]["attrs"]["units"].replace("hours since ", "")
        base_utc = datetime.datetime.fromisoformat(base_str).replace(tzinfo=datetime.timezone.utc)

        scaled_by_var = {}
        for var_name in _CLOUD_VARS:
            raw = netcdf3.read_point_series(path, header, var_name, ilat, ilon)
            attrs = header["variables"][var_name]["attrs"]
            scale = attrs.get("scale_factor", 1.0)
            offset = attrs.get("add_offset", 0.0)
            scaled_by_var[var_name] = [v * scale + offset for v in raw]
    except (OSError, ValueError, KeyError, struct.error) as exc:
        raise CloudDataUnavailable("MSMデータの解析に失敗しました") from exc

    records = []
    for i, h in enumerate(time_values):
        dt_utc = base_utc + datetime.timedelta(hours=float(h))
        dt_jst = dt_utc.astimezone(config.JST)
        records.append(
            {
                "time": dt_jst,
                "total_cloud_pct": round(max(0.0, min(100.0, scaled_by_var["clda"][i])), 1),
                "low_pct": round(max(0.0, min(100.0, scaled_by_var["ncld_low"][i])), 1),
                "mid_pct": round(max(0.0, min(100.0, scaled_by_var["ncld_mid"][i])), 1),
                "upper_pct": round(max(0.0, min(100.0, scaled_by_var["ncld_upper"][i])), 1),
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
