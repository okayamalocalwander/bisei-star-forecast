"""v3: 20〜40代女性を意識した、白基調・余白多め・丸みのあるおしゃれLP風テーマ。

写真は未提供のため、実写真に差し替えやすいようグラデーション+アイコンのプレースホルダーで代替する。
口コミ・SNS投稿はサンプルであることを明記したダミーコンテンツ。
"""
import html

ACCENT_CORAL = "#FF7E93"
ACCENT_LAVENDER = "#8B93FF"
ACCENT_GOLD = "#FFC978"

BASE_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Zen+Maru+Gothic:wght@500;700;900&family=Noto+Sans+JP:wght@400;500;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Noto Sans JP', -apple-system, sans-serif;
    font-size: 17px;
    line-height: 1.85;
}

[data-testid="stAppViewContainer"] p,
[data-testid="stAppViewContainer"] span,
[data-testid="stAppViewContainer"] li,
[data-testid="stAppViewContainer"] label {
    color: #4A4550;
}

.stApp {
    background: #FFFCFA;
}

h1, h2, h3, h4, .v3-heading {
    font-family: 'Zen Maru Gothic', 'Noto Sans JP', sans-serif;
    font-weight: 700;
    color: #3A3540;
}

@keyframes v3fadein {
    from { opacity: 0; transform: translateY(14px); }
    to { opacity: 1; transform: translateY(0); }
}
.v3-fade { animation: v3fadein 0.9s ease-out both; }
.v3-fade.d1 { animation-delay: 0.05s; }
.v3-fade.d2 { animation-delay: 0.15s; }
.v3-fade.d3 { animation-delay: 0.25s; }

.v3-hero {
    border-radius: 32px;
    overflow: hidden;
    position: relative;
    margin-bottom: 12px;
}
.v3-hero-img {
    height: 320px;
    background: linear-gradient(135deg, #FFE3E9 0%, #FFDCC7 45%, #E4E1FF 100%);
    display: flex; align-items: center; justify-content: center;
    position: relative;
}
.v3-hero-img .v3-ph-tag {
    position: absolute; top: 16px; right: 16px;
    background: rgba(255,255,255,0.85); color: #8A8390; font-size: 12px;
    padding: 5px 12px; border-radius: 999px;
}
.v3-hero-emoji { font-size: 4.2rem; filter: drop-shadow(0 6px 18px rgba(0,0,0,0.08)); }
.v3-hero-text {
    padding: 30px 8px 6px 8px;
    text-align: center;
}
.v3-hero-title { font-size: 1.9rem; font-weight: 900; margin: 0 0 10px 0; line-height: 1.5; color: #3A3540 !important; font-family: 'Zen Maru Gothic', sans-serif; }
.v3-hero-sub { font-size: 1.02rem; color: #7A7480; margin: 0; line-height: 1.9; }

.v3-cta {
    display: inline-block; text-decoration:none;
    background: linear-gradient(135deg, #FF7E93, #FF9E7E);
    color: white !important; font-weight: 700; font-size: 1rem;
    padding: 16px 40px; border-radius: 999px; border: none;
    box-shadow: 0 10px 24px rgba(255,126,147,0.35);
}

.v3-section { padding: 46px 4px 10px 4px; }
.v3-eyebrow {
    display:inline-block; font-size: 0.8rem; font-weight: 700; letter-spacing: 0.08em;
    color: #FF7E93; background: #FFF0F3; padding: 5px 14px; border-radius: 999px; margin-bottom: 10px;
}
.v3-section-title { font-size: 1.5rem; font-weight: 900; margin: 4px 0 10px 0; color: #3A3540 !important; font-family: 'Zen Maru Gothic', sans-serif; }
.v3-section-lead { color: #7A7480; font-size: 1rem; margin-bottom: 26px; line-height: 1.9; }

.v3-card {
    background: #FFFFFF;
    border-radius: 26px;
    padding: 26px 24px;
    border: 1px solid #F4EEE9;
    box-shadow: 0 10px 30px rgba(80,60,60,0.06);
    height: 100%;
}
.v3-card-img {
    height: 150px; border-radius: 20px; margin-bottom: 16px;
    display:flex; align-items:center; justify-content:center; font-size: 2.6rem;
}
.v3-card-title { font-weight: 700; font-size: 1.08rem; margin-bottom: 6px; color: #3A3540 !important; }
.v3-card-body { color: #7A7480; font-size: 0.94rem; line-height: 1.85; }

.v3-badge {
    display:inline-block; padding: 4px 12px; border-radius: 999px; font-size: 0.78rem; font-weight: 700;
    background: #F1F1FF; color: #6B74E0; margin-right: 6px; margin-bottom: 6px;
}

.v3-recommend {
    background: linear-gradient(135deg, #FFF6F0, #F3F1FF);
    border-radius: 30px;
    padding: 34px 30px;
    text-align:center;
    border: 1px solid #F6E9F0;
}
.v3-recommend .v3-stars { font-size: 1.7rem; letter-spacing: 4px; margin: 6px 0 10px 0; color: #FFB94D; }
.v3-recommend .v3-headline { font-size: 1.3rem; font-weight: 900; margin: 4px 0; color: #3A3540 !important; }
.v3-recommend .v3-note { color: #8A8390; font-size: 0.92rem; margin-top: 6px; }

.v3-quote-card {
    background:#FFFFFF; border-radius: 22px; padding: 22px; border: 1px solid #F4EEE9;
    box-shadow: 0 8px 20px rgba(80,60,60,0.05); height: 100%;
}
.v3-quote-avatar {
    width: 46px; height: 46px; border-radius: 50%;
    background: linear-gradient(135deg, #FFD3DC, #D9D6FF);
    display:flex; align-items:center; justify-content:center; font-size: 1.3rem; margin-bottom: 10px;
}
.v3-quote-name { font-weight: 700; font-size: 0.92rem; margin-bottom: 2px; color: #3A3540 !important; }
.v3-quote-meta { color:#B7B0BC; font-size: 0.78rem; margin-bottom: 10px; }
.v3-quote-body { color:#5C5660; font-size: 0.93rem; line-height: 1.8; }

.v3-sns-tile {
    aspect-ratio: 1/1; border-radius: 18px;
    display:flex; align-items:center; justify-content:center; font-size: 1.8rem;
    color: white;
}

.v3-sample-tag {
    display:inline-block; font-size: 0.72rem; color:#B7B0BC; background:#FAF7F5;
    padding: 3px 10px; border-radius: 999px; margin-bottom: 14px;
}

.v3-audience {
    background:#FFFFFF; border-radius: 26px; padding: 30px 28px; border:1px solid #F4EEE9;
    box-shadow: 0 10px 30px rgba(80,60,60,0.06);
}
.v3-audience-title { font-weight: 900; font-size: 1.15rem; margin-bottom: 12px; color: #3A3540 !important; font-family: 'Zen Maru Gothic', sans-serif; }
.v3-audience-item { display:flex; gap:10px; align-items:flex-start; margin-bottom: 10px; color:#5C5660; font-size:0.96rem; line-height:1.7;}

.v3-footer-cta {
    background: linear-gradient(135deg, #FFEFE6, #EFEEFF);
    border-radius: 32px; padding: 46px 30px; text-align:center; margin-top: 20px;
}
</style>
"""


def inject():
    import streamlit as st

    st.markdown(BASE_CSS, unsafe_allow_html=True)


def fade(html_str: str, delay_class: str = "") -> str:
    cls = f"v3-fade {delay_class}".strip()
    return f'<div class="{cls}">{html_str}</div>'


def hero(emoji: str, title: str, subtitle: str) -> str:
    return f"""
<div class="v3-hero v3-fade">
  <div class="v3-hero-img">
    <span class="v3-ph-tag">📷 写真差し替え予定</span>
    <span class="v3-hero-emoji">{emoji}</span>
  </div>
  <div class="v3-hero-text">
    <p class="v3-hero-title">{html.escape(title)}</p>
    <p class="v3-hero-sub">{html.escape(subtitle)}</p>
  </div>
</div>
"""


def section_header(eyebrow: str, title: str, lead: str = "") -> str:
    lead_html = f'<p class="v3-section-lead">{html.escape(lead)}</p>' if lead else ""
    return f"""
<div class="v3-section v3-fade">
  <span class="v3-eyebrow">{html.escape(eyebrow)}</span>
  <p class="v3-section-title">{html.escape(title)}</p>
  {lead_html}
</div>
"""


def audience_card() -> str:
    items = [
        "満天の星の下で、大切な人と特別な時間を過ごしたい方",
        "SNSでは伝わらない“本物の景色”を自分の目で確かめたい方",
        "旅の計画をもっと効率よく、失敗なく立てたい方",
    ]
    items_html = "".join(f'<div class="v3-audience-item">💫 {html.escape(t)}</div>' for t in items)
    return f"""
<div class="v3-audience v3-fade">
  <p class="v3-audience-title">こんな方におすすめです</p>
  {items_html}
</div>
"""


def stars_for_score(score: int) -> str:
    filled = max(1, min(5, round(score / 20)))
    return "★" * filled + "☆" * (5 - filled)


def recommend_card(headline: str, sub_note: str, score: int) -> str:
    return f"""
<div class="v3-recommend v3-fade">
  <div class="v3-stars">{stars_for_score(score)}</div>
  <p class="v3-headline">{html.escape(headline)}</p>
  <p class="v3-note">{html.escape(sub_note)}</p>
</div>
"""


def spot_card(emoji: str, gradient: str, name: str, note: str, score: int, label: str, moon_line: str, is_best: bool) -> str:
    badge = '<span class="v3-badge">🏆 今夜のイチオシ</span>' if is_best else ""
    return f"""
<div class="v3-card v3-fade">
  <div class="v3-card-img" style="background:{gradient};">{emoji}</div>
  {badge}
  <p class="v3-card-title">{html.escape(name)}</p>
  <p class="v3-card-body">{html.escape(note)}</p>
  <div style="margin-top:10px;">
    <span class="v3-stars" style="font-size:1.05rem;">{stars_for_score(score)}</span>
    <span style="color:#B7B0BC; font-size:0.85rem;"> ・{html.escape(label)}</span>
  </div>
  <p class="v3-card-body" style="margin-top:8px;">{moon_line}</p>
</div>
"""


def quote_card(avatar_emoji: str, name: str, meta: str, body: str) -> str:
    return f"""
<div class="v3-quote-card v3-fade">
  <div class="v3-quote-avatar">{avatar_emoji}</div>
  <p class="v3-quote-name">{html.escape(name)}</p>
  <p class="v3-quote-meta">{html.escape(meta)}</p>
  <p class="v3-quote-body">{html.escape(body)}</p>
</div>
"""


def sns_tile(emoji: str, gradient: str) -> str:
    return f'<div class="v3-sns-tile" style="background:{gradient};">{emoji}</div>'
