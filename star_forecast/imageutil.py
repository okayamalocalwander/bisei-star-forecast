"""ローカル画像ファイルをHTML埋め込み用のdata URIに変換する。"""
import base64
import os

_MIME_BY_EXT = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png"}


def image_to_data_uri(path: str) -> str:
    ext = os.path.splitext(path)[1].lower()
    mime = _MIME_BY_EXT.get(ext, "application/octet-stream")
    with open(path, "rb") as f:
        encoded = base64.b64encode(f.read()).decode("ascii")
    return f"data:{mime};base64,{encoded}"
