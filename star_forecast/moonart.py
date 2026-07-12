"""月齢（輝面比・満ち欠けの向き）から、実際の見え方に近い月のイラスト（SVG）を生成する。"""
import math

SYNODIC_MONTH_DAYS = 29.53

_PHASE_NAMES = ["新月", "三日月", "上弦の月", "十三夜月", "満月", "十六夜月", "下弦の月", "有明の月"]


def phase_name(age_days: float) -> str:
    """月齢から和風の月相名（8区分）を返す。"""
    age = age_days % SYNODIC_MONTH_DAYS
    segment_width = SYNODIC_MONTH_DAYS / 8
    idx = int((age + segment_width / 2) / segment_width) % 8
    return _PHASE_NAMES[idx]


def moon_phase_svg(
    illumination_pct: float,
    waxing: bool,
    size: int = 72,
    dark_color: str = "#1b1f3a",
    light_color: str = "#f4e9c1",
    ring_color: str = "#7a7a8c",
) -> str:
    """輝面比(0-100)と満ち欠けの向き(waxing=満ちていく途中か)から月のSVGを生成する。

    日本（北半球）から見た向きを想定し、waxing=Trueのときは右側から満ちていく。
    """
    r = size / 2 - 3
    cx = cy = size / 2
    k = max(0.0, min(1.0, illumination_pct / 100.0))
    cos_theta = 1 - 2 * k
    rx = r * abs(cos_theta)

    limb_side = 1 if waxing else -1
    term_side = limb_side if k < 0.5 else -limb_side

    steps = 40
    points = []
    for i in range(steps + 1):
        a = math.pi / 2 - math.pi * i / steps
        y = cy - r * math.sin(a)
        x = cx + limb_side * r * math.cos(a)
        points.append((x, y))
    for i in range(steps + 1):
        a = -math.pi / 2 + math.pi * i / steps
        y = cy - r * math.sin(a)
        x = cx + term_side * rx * math.cos(a)
        points.append((x, y))
    points_str = " ".join(f"{x:.2f},{y:.2f}" for x, y in points)

    return (
        f'<svg width="{size}" height="{size}" viewBox="0 0 {size} {size}" '
        f'xmlns="http://www.w3.org/2000/svg" role="img" aria-label="moon phase">'
        f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{dark_color}"/>'
        f'<polygon points="{points_str}" fill="{light_color}"/>'
        f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{ring_color}" stroke-width="1"/>'
        f"</svg>"
    )
