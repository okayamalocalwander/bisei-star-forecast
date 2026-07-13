"""20〜40代の観光客をターゲットにした、夜空をイメージしたUIテーマ用のCSSとHTML部品。"""
import html

BASE_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Manrope:wght@700;800&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
}

.stApp {
    background:
        radial-gradient(circle at 15% 8%, rgba(124, 156, 255, 0.10), transparent 42%),
        radial-gradient(circle at 85% 0%, rgba(245, 194, 66, 0.08), transparent 40%),
        #0B1120;
}

h1, h2, h3, h4 { font-family: 'Manrope', 'Inter', sans-serif; letter-spacing: -0.01em; }

.bsf-hero {
    padding: 28px 32px;
    border-radius: 20px;
    margin-bottom: 8px;
    background: linear-gradient(135deg, rgba(124,156,255,0.16), rgba(245,194,66,0.10));
    border: 1px solid rgba(255,255,255,0.08);
}
.bsf-hero-title {
    font-family: 'Manrope', sans-serif;
    font-weight: 800;
    font-size: 2.1rem;
    margin: 0 0 6px 0;
    background: linear-gradient(90deg, #F5C242, #7C9CFF);
    -webkit-background-clip: text;
    background-clip: text;
    -webkit-text-fill-color: transparent;
}
.bsf-hero-sub { color: #A8B0C3; font-size: 0.95rem; margin: 0; }
.bsf-hero-icon { -webkit-text-fill-color: initial; background: none; }

.bsf-section-title {
    font-family: 'Manrope', sans-serif;
    font-weight: 700;
    font-size: 1.25rem;
    margin: 4px 0 14px 0;
    display: flex; align-items: center; gap: 8px;
}

.bsf-recommend {
    padding: 20px 24px;
    border-radius: 18px;
    background: linear-gradient(135deg, rgba(245,194,66,0.16), rgba(245,194,66,0.04));
    border: 1px solid rgba(245,194,66,0.35);
    box-shadow: 0 0 32px rgba(245,194,66,0.08);
}
.bsf-recommend .label { color: #F5C242; font-weight: 700; font-size: 0.8rem; letter-spacing: 0.06em; text-transform: uppercase; }
.bsf-recommend .headline { font-size: 1.35rem; font-weight: 800; margin: 4px 0 0 0; color: #F2F1EC; }

.bsf-extend {
    padding: 18px 22px;
    border-radius: 18px;
    background: rgba(124,156,255,0.10);
    border: 1px solid rgba(124,156,255,0.35);
    height: 100%;
}
.bsf-extend .label { color: #93A9FF; font-weight: 700; font-size: 0.8rem; letter-spacing: 0.06em; text-transform: uppercase; }
.bsf-extend .body { font-size: 0.95rem; margin-top: 6px; color: #E5E9FF; line-height: 1.5; }

.bsf-daycard {
    border-radius: 20px;
    padding: 22px 24px;
    margin-bottom: 22px;
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.08);
}
.bsf-date-title { font-family:'Manrope',sans-serif; font-weight: 800; font-size: 1.15rem; margin: 0 0 2px 0; }
.bsf-meta-line { color: #A8B0C3; font-size: 0.85rem; margin: 2px 0; }

.bsf-spotcard {
    border-radius: 16px;
    padding: 16px 16px 14px 16px;
    border: 1px solid var(--bsf-border, rgba(255,255,255,0.10));
    background: var(--bsf-bg, rgba(255,255,255,0.02));
    height: 100%;
}
.bsf-spotcard.best { border-color: rgba(245,194,66,0.55); box-shadow: 0 0 24px rgba(245,194,66,0.12); }
.bsf-spot-name { font-weight: 700; font-size: 0.95rem; display:flex; align-items:center; gap:6px; margin-bottom: 6px; }
.bsf-score-row { display:flex; align-items:baseline; gap: 8px; margin: 4px 0 6px 0; }
.bsf-score-num { font-family:'Manrope',sans-serif; font-weight: 800; font-size: 2.1rem; line-height:1; }
.bsf-score-badge {
    display:inline-block; padding: 3px 10px; border-radius: 999px;
    font-size: 0.72rem; font-weight: 700; letter-spacing: 0.02em;
}
.bsf-spot-note { color:#A8B0C3; font-size: 0.82rem; margin: 4px 0 8px 0; line-height:1.45; }
.bsf-moon-line { font-size: 0.83rem; color:#D9DEEC; }

.bsf-pill {
    display:inline-block; padding: 2px 9px; border-radius: 999px; font-size: 0.72rem;
    background: rgba(124,156,255,0.16); color:#B9C6FF; margin-right: 4px;
}
</style>
"""


def inject():
    import streamlit as st

    st.markdown(BASE_CSS, unsafe_allow_html=True)


def score_color(score: int) -> str:
    if score >= 80:
        return "#F5C242"
    if score >= 60:
        return "#4ADE80"
    if score >= 40:
        return "#60A5FA"
    if score >= 20:
        return "#FB923C"
    return "#F87171"


def hero(icon: str, title: str, subtitle: str) -> str:
    return (
        f'<div class="bsf-hero">'
        f'<p class="bsf-hero-title"><span class="bsf-hero-icon">{icon}</span> {html.escape(title)}</p>'
        f'<p class="bsf-hero-sub">{html.escape(subtitle)}</p>'
        f"</div>"
    )


def section_title(icon: str, text: str) -> str:
    return f'<div class="bsf-section-title">{icon} {html.escape(text)}</div>'


def recommend_card(headline: str) -> str:
    return (
        '<div class="bsf-recommend">'
        '<div class="label">Best Night</div>'
        f'<p class="headline">{html.escape(headline)}</p>'
        "</div>"
    )


def extend_card(body: str) -> str:
    return f'<div class="bsf-extend"><div class="label">Stay Longer?</div><div class="body">{body}</div></div>'


def spot_card(name: str, is_best: bool, score: int, label: str, note: str, moon_line: str) -> str:
    color = score_color(score)
    best_class = " best" if is_best else ""
    badge = f'🏆 {html.escape(name)}' if is_best else html.escape(name)
    return f"""
<div class="bsf-spotcard{best_class}" style="--bsf-border:{color}33; --bsf-bg:{color}0d;">
  <div class="bsf-spot-name">{badge}</div>
  <div class="bsf-score-row">
    <span class="bsf-score-num" style="color:{color};">{score}</span>
    <span style="color:#7A8296; font-size:0.85rem;">/ 100</span>
  </div>
  <span class="bsf-score-badge" style="background:{color}22; color:{color};">{html.escape(label)}</span>
  <div class="bsf-spot-note">{html.escape(note)}</div>
  <div class="bsf-moon-line">{moon_line}</div>
</div>
"""
