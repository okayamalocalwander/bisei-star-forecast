"""NetCDF3 classic形式のヘッダーだけを最小限パースし、必要な1格子点・時系列分の
バイトだけをファイルから直接読み出すための軽量モジュール。

scipy.io.netcdf_file は mmap=False だと変数データを丸ごとメモリに展開してしまい、
190MB超のMSMファイル（多数の格子変数を含む）ではメモリ超過でクラッシュする
（Streamlit Community Cloudの無料枠で実際に発生）。
このモジュールは対象の変数について、ヘッダーから格納位置(begin)と形状だけを取得し、
必要な要素だけをseek+readするため、メモリ使用量を最小限に抑えられる。

このMSMミラーのファイルには record 変数（unlimited次元）が存在しないことを確認済みのため、
record variable のインターリーブ処理には対応していない（固定サイズ変数のみ対応）。
"""
import struct

_NC_TYPE_INFO = {
    1: (1, "b"),  # NC_BYTE
    2: (1, "c"),  # NC_CHAR
    3: (2, "h"),  # NC_SHORT
    4: (4, "i"),  # NC_INT
    5: (4, "f"),  # NC_FLOAT
    6: (8, "d"),  # NC_DOUBLE
}


def _read_name(fp) -> str:
    (nelems,) = struct.unpack(">I", fp.read(4))
    raw = fp.read(nelems)
    pad = (4 - nelems % 4) % 4
    if pad:
        fp.read(pad)
    return raw.decode("ascii")


def _read_values(fp, nc_type: int, nelems: int):
    size, fmt = _NC_TYPE_INFO[nc_type]
    total = size * nelems
    raw = fp.read(total)
    pad = (4 - total % 4) % 4
    if pad:
        fp.read(pad)
    if nc_type == 2:
        return raw.decode("ascii", errors="replace")
    values = struct.unpack(">" + fmt * nelems, raw)
    return values[0] if nelems == 1 else list(values)


def _read_dim_list(fp):
    struct.unpack(">I", fp.read(4))  # tag
    (count,) = struct.unpack(">I", fp.read(4))
    dims = []
    for _ in range(count):
        name = _read_name(fp)
        (length,) = struct.unpack(">I", fp.read(4))
        dims.append((name, length))
    return dims


def _read_attr_list(fp) -> dict:
    struct.unpack(">I", fp.read(4))  # tag
    (count,) = struct.unpack(">I", fp.read(4))
    attrs = {}
    for _ in range(count):
        name = _read_name(fp)
        (nc_type,) = struct.unpack(">I", fp.read(4))
        (nelems,) = struct.unpack(">I", fp.read(4))
        attrs[name] = _read_values(fp, nc_type, nelems)
    return attrs


def _read_var_list(fp, dim_sizes: list, version: int) -> dict:
    struct.unpack(">I", fp.read(4))  # tag
    (count,) = struct.unpack(">I", fp.read(4))
    offset_fmt = ">I" if version == 1 else ">Q"
    offset_size = 4 if version == 1 else 8
    variables = {}
    for _ in range(count):
        name = _read_name(fp)
        (ndims,) = struct.unpack(">I", fp.read(4))
        dimids = struct.unpack(">" + "I" * ndims, fp.read(4 * ndims)) if ndims else ()
        attrs = _read_attr_list(fp)
        (nc_type,) = struct.unpack(">I", fp.read(4))
        (vsize,) = struct.unpack(">I", fp.read(4))
        (begin,) = struct.unpack(offset_fmt, fp.read(offset_size))
        shape = tuple(dim_sizes[i] for i in dimids)
        variables[name] = {
            "shape": shape,
            "dimids": dimids,
            "nc_type": nc_type,
            "vsize": vsize,
            "begin": begin,
            "attrs": attrs,
        }
    return variables


def parse_header(path: str) -> dict:
    """NetCDF3 classicファイルのヘッダー（次元・属性・変数のメタ情報）だけを読み取る。"""
    with open(path, "rb") as fp:
        magic = fp.read(4)
        if magic[:3] != b"CDF":
            raise ValueError("NetCDF3 classic形式ではありません")
        version = magic[3]
        (numrecs,) = struct.unpack(">I", fp.read(4))
        if numrecs != 0:
            raise ValueError("record変数（unlimited次元）を含むファイルには未対応です")
        dims = _read_dim_list(fp)
        dim_sizes = [d[1] for d in dims]
        _read_attr_list(fp)  # global attributes（未使用）
        variables = _read_var_list(fp, dim_sizes, version)
    return {"dims": dims, "variables": variables}


def read_1d(path: str, header: dict, var_name: str) -> list:
    """1次元の変数（lat, lon, time など）を丸ごと読み出す。要素数は小さい前提。"""
    var = header["variables"][var_name]
    (n,) = var["shape"]
    nc_type = var["nc_type"]
    itemsize, fmt = _NC_TYPE_INFO[nc_type]
    with open(path, "rb") as fp:
        fp.seek(var["begin"])
        raw = fp.read(itemsize * n)
    return list(struct.unpack(">" + fmt * n, raw))


def read_point_series(path: str, header: dict, var_name: str, i0: int, i1: int) -> list:
    """3次元変数(dim0, dim1, dim2)について、dim1=i1固定・dim2=i2... ではなく
    (dim0=:, i1, i2) の時系列を1要素ずつ読み出す。

    対象変数は形状 (dim0, n1, n2) の固定サイズ変数を想定（dim0方向にすべて取得）。
    i0, i1 は dim1, dim2 のインデックス（例: 緯度・経度の格子インデックス）。
    """
    var = header["variables"][var_name]
    n0, n1, n2 = var["shape"]
    nc_type = var["nc_type"]
    itemsize, fmt = _NC_TYPE_INFO[nc_type]
    begin = var["begin"]

    values = []
    with open(path, "rb") as fp:
        for t in range(n0):
            offset = begin + (t * n1 * n2 + i0 * n2 + i1) * itemsize
            fp.seek(offset)
            raw = fp.read(itemsize)
            (value,) = struct.unpack(">" + fmt, raw)
            values.append(value)
    return values
