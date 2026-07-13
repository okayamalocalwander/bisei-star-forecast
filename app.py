import datetime
import os

import altair as alt
import pandas as pd
import streamlit as st

from star_forecast import cloudmsm, config, imageutil, moonart, scoring, sky, theme, theme_v3, weather

_REFERENCE_LOCATION = next(iter(config.LOCATIONS.values()))  # 星の見え方の共通計算に使う代表地点
_SPOT_COLORS = {"美星天文台": "#F5C242", "星空公園": "#7C9CFF", "竜王山公園": "#4ADE80"}
_SPOT_EMOJI = {"美星天文台": "🔭", "星空公園": "🌠", "竜王山公園": "🌸"}
_SPOT_GRADIENT = {
    "美星天文台": "linear-gradient(135deg,#E4E1FF,#C9C4FF)",
    "星空公園": "linear-gradient(135deg,#FFE3C7,#FFCBA4)",
    "竜王山公園": "linear-gradient(135deg,#FFE0EC,#FFC2D6)",
}
_ASSETS_DIR = os.path.join(os.path.dirname(__file__), "assets")
_HERO_PHOTO = "hero.jpg"
_SPOT_PHOTO = {
    "美星天文台": "spot_bisei.jpg",
    "星空公園": "spot_hoshizora.jpg",
    "竜王山公園": "spot_ryuozan.jpg",
}

st.set_page_config(page_title="美星町 星空予報", page_icon="🌌", layout="wide")


@st.cache_data
def load_photo(filename: str) -> str:
    return imageutil.image_to_data_uri(os.path.join(_ASSETS_DIR, filename))


@st.cache_data(ttl=1800)
def load_weather():
    return weather.get_daily_forecast()


@st.cache_data(ttl=1800)
def load_hourly_cloud():
    return cloudmsm.get_hourly_cloud_forecast(_REFERENCE_LOCATION["lat"], _REFERENCE_LOCATION["lon"])


def build_all_location_scores(dates, weather_by_date):
    """日付ごとに、全観測スポットのスコア一覧（指数の高い順）を計算する。"""
    return [
        scoring.compute_day_scores_all_locations(d, weather_by_date.get(d), config.WEATHER_FORECAST_HORIZON_DAYS)
        for d in dates
    ]


def best_per_day(all_location_scores):
    """各日ごとの最良スポットのスコアを取り出す。"""
    return [day[0] for day in all_location_scores]


def weather_and_events_lines(weather_entry):
    if weather_entry["weather_available"]:
        weather_line = weather_entry["weather_text"] or "―"
        if weather_entry["pop"] is not None:
            weather_line += f"（降水確率 {weather_entry['pop']}%）"
        weather_line += f" ／ {weather_entry['weather_area']}地域"
    else:
        weather_line = "天気予報はまだ発表されていません（月齢のみの参考値）"

    if weather_entry["dusk"] and weather_entry["dawn"]:
        dark_window = f"{weather_entry['dusk'].strftime('%H:%M')} 〜 翌 {weather_entry['dawn'].strftime('%H:%M')}"
    else:
        dark_window = "計算不可"
    events_line = "、".join(weather_entry["events"]) if weather_entry["events"] else "特になし"
    return weather_line, dark_window, events_line


METHOD_NOTES = """
- **天気予報あり（概ね7日先まで）**: 天気予報の空模様と降水確率から算出したスコアを55%、月明かりの影響を35%、天文イベントのボーナスを加味します。天気は3スポット共通（気象庁の岡山県南部予報）です。
- **天気予報なし（8日先〜1か月程度先）**: 天気はまだ予測できないため、月齢・月の出没時刻から算出した「月明かりの影響が少ないか」を主な指標にした参考値を表示します。
- **観測スポット別の違い**: 各スポットは方角ごとの見やすさが異なります（美星天文台＝西がやや苦手、星空公園＝東が得意、竜王山公園＝南が得意）。天文薄明の時間帯に月がどの方角にあるかを計算し、そのスポットで見やすい方角に月がある場合は影響を大きく、見えにくい方角にある場合は影響を小さく補正しています。
- **時間帯別に見える星**: 3スポットとも見えている星そのものはほぼ共通（同じ空）ですが、その方角がスポットごとに見やすいかどうかで「◎見やすい／○普通／△やや見えにくい」を表示します。高度15°以上に昇っている主要な恒星・惑星が対象です。
- **本日の詳細な雲の動き**: 気象庁MSM（メソモデル）の実況〜短期予報データから、当日のみ1時間ごとの雲量を取得して表示します（全雲量から算出した観望期待度）。日別予報とは別に、当日に限りより細かい時間解像度で確認できます。
"""


def render_sky_expander(time_slots, raw_sky_by_slot, direction_visibility):
    with st.expander("🔭 時間帯別に見える星"):
        if not time_slots:
            st.caption("天文薄明の時間帯を計算できませんでした。")
        for t in time_slots:
            annotated = sky.annotate_visibility(raw_sky_by_slot[t], direction_visibility)
            st.markdown(f"**{t.strftime('%H:%M')}**")
            if annotated["asterisms"]:
                st.caption("🌟 " + "・".join(annotated["asterisms"]) + " が見えます")
            for s in annotated["stars"][:6]:
                st.markdown(f"- {s['jp']}（{s['constellation']}）高度約{s['altitude']}° {s['sector']}の空 {s['visibility_label']}")
            for p in annotated["planets"]:
                st.markdown(f"- {p['jp']} 高度約{p['altitude']}° {p['sector']}の空 {p['visibility_label']}")
            if not annotated["stars"] and not annotated["planets"]:
                st.caption("この時間帯に見える主要な星はありません。")


# =====================================================================================
# v0: シンプル版（標準のStreamlitコンポーネントのみを使ったオリジナルデザイン）
# =====================================================================================
def render_v0(ctx):
    st.title("🌌 美星町 星空予報ダッシュボード")
    st.caption(f"{config.TOWN_NAME} を訪れる観光客向けの星空指数プロトタイプ（観測スポット別）")

    col1, col2 = st.columns([2, 1])
    with col1:
        st.subheader(
            f"⭐ この期間のおすすめは {ctx['best_day']['date'].strftime('%m/%d')}の{ctx['best_day']['location']}"
            f"（{ctx['best_day']['label']}・指数{ctx['best_day']['total_score']}）"
        )
    with col2:
        if ctx["extension"]:
            e = ctx["extension"]
            st.info(
                f"📅 延泊のご提案: {e['date'].strftime('%m/%d')} は星空指数 {e['score']} "
                f"（出発日より +{e['diff']}）。延泊すると、より良い星空が期待できます。"
            )

    if ctx["today"] in ctx["trip_dates"]:
        st.divider()
        st.subheader(f"🌤 本日（{ctx['today'].strftime('%m/%d')}）の詳細な雲の動き")
        if ctx["cloud_records"] is None:
            st.warning("MSM雲データの取得に失敗しました。下の日別予報のみをご参照ください。")
        elif not ctx["today_records"]:
            st.info("本日の時間別雲データはまだ取得できませんでした。")
        else:
            today_records = ctx["today_records"]
            cloud_df = pd.DataFrame(
                {
                    "時刻": [r["time"].strftime("%H:%M") for r in today_records],
                    "観望期待度": [cloudmsm.viewing_expectation(r["total_cloud_pct"])[0] for r in today_records],
                }
            )
            st.line_chart(cloud_df, x="時刻", y="観望期待度")

            best_hour = max(today_records, key=lambda r: cloudmsm.viewing_expectation(r["total_cloud_pct"])[0])
            best_score, best_label = cloudmsm.viewing_expectation(best_hour["total_cloud_pct"])
            st.caption(
                f"本日は {best_hour['time'].strftime('%H:%M')} ごろが最も観望に適しています"
                f"（観望期待度 {best_score}・{best_label}、全雲量 {best_hour['total_cloud_pct']}%）"
            )
            with st.expander("時間別の詳細（雲の高さ別内訳）"):
                for r in today_records:
                    score, label = cloudmsm.viewing_expectation(r["total_cloud_pct"])
                    st.markdown(
                        f"**{r['time'].strftime('%H:%M')}** 観望期待度 {score}（{label}） ｜ "
                        f"全雲量 {r['total_cloud_pct']}%（低層 {r['low_pct']}% ・中層 {r['mid_pct']}% ・上層 {r['upper_pct']}%）"
                    )
            st.caption(
                f"データ: {cloudmsm.ATTRIBUTION}。教育研究目的の非公式ミラー経由のプロトタイプ実装のため、"
                "本番運用時は気象業務支援センター等の正規データ契約への切り替えを推奨します。"
            )

    st.divider()
    chart_rows = []
    for day in ctx["trip_all_scores"] + ctx["lookahead_all_scores"]:
        for loc_score in day:
            chart_rows.append(
                {"日付": loc_score["date"].strftime("%m/%d"), "観測スポット": loc_score["location"], "星空指数": loc_score["total_score"]}
            )
    chart_df = pd.DataFrame(chart_rows).pivot(index="日付", columns="観測スポット", values="星空指数")
    chart_df = chart_df.reindex([d.strftime("%m/%d") for d in ctx["trip_dates"] + ctx["lookahead_dates"]])
    st.bar_chart(chart_df, stack=False)

    st.divider()
    st.subheader("日別・観測スポット別の詳細")

    for day in ctx["trip_all_scores"]:
        date = day[0]["date"]
        with st.container(border=True):
            st.markdown(f"#### {date.strftime('%m/%d (%a)')}")
            weather_entry = day[0]
            weather_line, dark_window, events_line = weather_and_events_lines(weather_entry)

            moon_col, info_col = st.columns([1, 5])
            with moon_col:
                svg = moonart.moon_phase_svg(weather_entry["moon_illumination_pct"], weather_entry["moon_waxing"], size=64)
                st.markdown(svg, unsafe_allow_html=True)
                st.caption(moonart.phase_name(weather_entry["moon_age_days"]))
            with info_col:
                st.caption(f"天気: {weather_line}　｜　天文薄明: {dark_window}　｜　天文イベント: {events_line}")
                st.caption(f"月齢 {weather_entry['moon_age_days']}　｜　輝面比 {weather_entry['moon_illumination_pct']}%")

            time_slots = sky.generate_time_slots(weather_entry["dusk"], weather_entry["dawn"])
            raw_sky_by_slot = {
                t: sky.get_sky_objects(t, _REFERENCE_LOCATION["lat"], _REFERENCE_LOCATION["lon"], _REFERENCE_LOCATION["elevation"])
                for t in time_slots
            }

            cols = st.columns(len(day))
            for col, loc_score in zip(cols, day):
                with col:
                    is_best = loc_score is day[0]
                    title = f"{'🏆 ' if is_best else ''}{loc_score['location']}"
                    col.metric(title, f"{loc_score['total_score']} / 100", loc_score["label"])
                    col.caption(loc_score["location_note"])
                    if loc_score["moon_sector"]:
                        col.markdown(
                            f"月: **{loc_score['moon_sector']}の空**（高度約{loc_score['moon_altitude_deg']}°、輝面比{loc_score['moon_illumination_pct']}%）"
                        )
                    else:
                        col.markdown(f"月: 観測に適した時間帯は沈んでいます（輝面比{loc_score['moon_illumination_pct']}%）")

                    direction_visibility = config.LOCATIONS[loc_score["location"]]["direction_visibility"]
                    render_sky_expander(time_slots, raw_sky_by_slot, direction_visibility)

    st.divider()
    with st.expander("この指数の算出方法について"):
        st.markdown(METHOD_NOTES)


# =====================================================================================
# v1: ナイトスカイ版（20〜40代向けにデザインしたテーマ）
# =====================================================================================
def render_v1(ctx):
    theme.inject()
    st.markdown(theme.hero("🌌", "美星町 星空予報ダッシュボード", "夜、空を見上げたくなる町へ。観測スポット別・星空指数プロトタイプ"), unsafe_allow_html=True)

    st.write("")
    col1, col2 = st.columns([2, 1])
    with col1:
        headline = (
            f"{ctx['best_day']['date'].strftime('%m/%d (%a)')} の {ctx['best_day']['location']} "
            f"— {ctx['best_day']['label']} ・ 指数 {ctx['best_day']['total_score']}"
        )
        st.markdown(theme.recommend_card(headline), unsafe_allow_html=True)
    with col2:
        if ctx["extension"]:
            e = ctx["extension"]
            body = (
                f"{e['date'].strftime('%m/%d')} は星空指数 {e['score']}"
                f"（出発日より +{e['diff']}）。延泊すると、より良い星空が期待できます。"
            )
        else:
            body = "現在の滞在期間内が、この先数日で最も星空指数の高いタイミングです。"
        st.markdown(theme.extend_card(body), unsafe_allow_html=True)

    if ctx["today"] in ctx["trip_dates"]:
        st.write("")
        st.markdown(theme.section_title("🌤", f"本日（{ctx['today'].strftime('%m/%d')}）の詳細な雲の動き"), unsafe_allow_html=True)
        if ctx["cloud_records"] is None:
            st.warning("MSM雲データの取得に失敗しました。下の日別予報のみをご参照ください。")
        elif not ctx["today_records"]:
            st.info("本日の時間別雲データはまだ取得できませんでした。")
        else:
            today_records = ctx["today_records"]
            cloud_df = pd.DataFrame(
                {
                    "時刻": [r["time"] for r in today_records],
                    "観望期待度": [cloudmsm.viewing_expectation(r["total_cloud_pct"])[0] for r in today_records],
                }
            )
            cloud_chart = (
                alt.Chart(cloud_df)
                .mark_area(
                    line={"color": "#F5C242", "size": 2.5},
                    color=alt.Gradient(
                        gradient="linear",
                        stops=[
                            alt.GradientStop(color="#F5C24200", offset=0),
                            alt.GradientStop(color="#F5C24255", offset=1),
                        ],
                        x1=1, x2=1, y1=1, y2=0,
                    ),
                    interpolate="monotone",
                )
                .encode(
                    x=alt.X("時刻:T", title=None, axis=alt.Axis(format="%H:%M", labelColor="#A8B0C3", gridColor="#243047")),
                    y=alt.Y("観望期待度:Q", title="観望期待度", scale=alt.Scale(domain=[0, 100]), axis=alt.Axis(labelColor="#A8B0C3", gridColor="#243047")),
                )
                .properties(height=220)
                .configure_view(strokeWidth=0)
                .configure(background="transparent")
            )
            st.altair_chart(cloud_chart, use_container_width=True)

            best_hour = max(today_records, key=lambda r: cloudmsm.viewing_expectation(r["total_cloud_pct"])[0])
            best_score, best_label = cloudmsm.viewing_expectation(best_hour["total_cloud_pct"])
            st.caption(
                f"本日は {best_hour['time'].strftime('%H:%M')} ごろが最も観望に適しています"
                f"（観望期待度 {best_score}・{best_label}、全雲量 {best_hour['total_cloud_pct']}%）"
            )
            with st.expander("時間別の詳細（雲の高さ別内訳）"):
                for r in today_records:
                    score, label = cloudmsm.viewing_expectation(r["total_cloud_pct"])
                    st.markdown(
                        f"**{r['time'].strftime('%H:%M')}** 観望期待度 {score}（{label}） ｜ "
                        f"全雲量 {r['total_cloud_pct']}%（低層 {r['low_pct']}% ・中層 {r['mid_pct']}% ・上層 {r['upper_pct']}%）"
                    )
            st.caption(
                f"データ: {cloudmsm.ATTRIBUTION}。教育研究目的の非公式ミラー経由のプロトタイプ実装のため、"
                "本番運用時は気象業務支援センター等の正規データ契約への切り替えを推奨します。"
            )

    st.write("")
    st.markdown(theme.section_title("📊", "期間中の星空指数（観測スポット別）"), unsafe_allow_html=True)

    chart_rows = []
    for day in ctx["trip_all_scores"] + ctx["lookahead_all_scores"]:
        for loc_score in day:
            chart_rows.append(
                {"日付": loc_score["date"].strftime("%m/%d"), "観測スポット": loc_score["location"], "星空指数": loc_score["total_score"]}
            )
    score_df = pd.DataFrame(chart_rows)
    score_chart = (
        alt.Chart(score_df)
        .mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4)
        .encode(
            x=alt.X("日付:O", title=None, sort=None, axis=alt.Axis(labelColor="#A8B0C3", gridColor="#243047")),
            xOffset="観測スポット:N",
            y=alt.Y("星空指数:Q", scale=alt.Scale(domain=[0, 100]), axis=alt.Axis(labelColor="#A8B0C3", gridColor="#243047")),
            color=alt.Color(
                "観測スポット:N",
                scale=alt.Scale(domain=list(_SPOT_COLORS.keys()), range=list(_SPOT_COLORS.values())),
                legend=alt.Legend(title=None, labelColor="#D9DEEC", orient="top"),
            ),
        )
        .properties(height=280)
        .configure_view(strokeWidth=0)
        .configure(background="transparent")
    )
    st.altair_chart(score_chart, use_container_width=True)

    st.write("")
    st.markdown(theme.section_title("🗓️", "日別・観測スポット別の詳細"), unsafe_allow_html=True)

    for day in ctx["trip_all_scores"]:
        date = day[0]["date"]
        weather_entry = day[0]
        weather_line, dark_window, events_line = weather_and_events_lines(weather_entry)

        st.markdown('<div class="bsf-daycard">', unsafe_allow_html=True)

        moon_col, info_col = st.columns([1, 5])
        with moon_col:
            svg = moonart.moon_phase_svg(weather_entry["moon_illumination_pct"], weather_entry["moon_waxing"], size=64)
            st.markdown(svg, unsafe_allow_html=True)
            st.caption(moonart.phase_name(weather_entry["moon_age_days"]))
        with info_col:
            st.markdown(f'<p class="bsf-date-title">{date.strftime("%m/%d (%a)")}</p>', unsafe_allow_html=True)
            st.markdown(
                f'<p class="bsf-meta-line">☁️ {weather_line}　｜　🌌 天文薄明 {dark_window}</p>'
                f'<p class="bsf-meta-line">✨ {events_line}　｜　月齢 {weather_entry["moon_age_days"]}（輝面比 {weather_entry["moon_illumination_pct"]}%）</p>',
                unsafe_allow_html=True,
            )

        time_slots = sky.generate_time_slots(weather_entry["dusk"], weather_entry["dawn"])
        raw_sky_by_slot = {
            t: sky.get_sky_objects(t, _REFERENCE_LOCATION["lat"], _REFERENCE_LOCATION["lon"], _REFERENCE_LOCATION["elevation"])
            for t in time_slots
        }

        st.write("")
        cols = st.columns(len(day))
        for col, loc_score in zip(cols, day):
            with col:
                is_best = loc_score is day[0]
                if loc_score["moon_sector"]:
                    moon_line = (
                        f'🌙 {loc_score["moon_sector"]}の空・高度約{loc_score["moon_altitude_deg"]}°'
                        f'（輝面比{loc_score["moon_illumination_pct"]}%）'
                    )
                else:
                    moon_line = f'🌙 観測に適した時間帯は月が沈んでいます（輝面比{loc_score["moon_illumination_pct"]}%）'

                st.markdown(
                    theme.spot_card(
                        loc_score["location"], is_best, loc_score["total_score"], loc_score["label"],
                        loc_score["location_note"], moon_line,
                    ),
                    unsafe_allow_html=True,
                )

                direction_visibility = config.LOCATIONS[loc_score["location"]]["direction_visibility"]
                render_sky_expander(time_slots, raw_sky_by_slot, direction_visibility)

        st.markdown("</div>", unsafe_allow_html=True)

    st.divider()
    with st.expander("この指数の算出方法について"):
        st.markdown(METHOD_NOTES)


# =====================================================================================
# v3: おしゃれLP版（20〜40代女性を意識した、白基調・余白多め・写真訴求型デザイン）
# =====================================================================================
def render_v3(ctx):
    theme_v3.inject()

    st.markdown(
        theme_v3.hero(
            "🌌",
            "大切な人と、満天の星に会いに行こう",
            "岡山県・美星町。日本有数の星空が見える町で、特別な夜を過ごすための旅の道しるべ。",
            photo_data_uri=load_photo(_HERO_PHOTO),
        ),
        unsafe_allow_html=True,
    )
    cta_col = st.columns([1, 2, 1])[1]
    with cta_col:
        st.markdown(
            '<div style="text-align:center; margin: 10px 0 6px 0;">'
            '<span class="v3-cta">✨ 今夜のおすすめをみる</span></div>',
            unsafe_allow_html=True,
        )

    st.markdown(
        theme_v3.section_header("ABOUT", "誰のための旅か", "SNSで見かけた星空を、今度は自分の目で。特別な人と、特別な夜を。"),
        unsafe_allow_html=True,
    )
    st.markdown(theme_v3.audience_card(), unsafe_allow_html=True)

    st.markdown(theme_v3.section_header("TONIGHT", "今夜のおすすめ"), unsafe_allow_html=True)
    bd = ctx["best_day"]
    headline = f"{bd['date'].strftime('%m/%d (%a)')} は {bd['location']} がおすすめ"
    sub_note = f"{bd['label']}／期間中でもっとも星空指数が高い夜です"
    st.markdown(theme_v3.recommend_card(headline, sub_note, bd["total_score"]), unsafe_allow_html=True)

    if ctx["extension"]:
        e = ctx["extension"]
        st.markdown(
            f'<p style="text-align:center; color:#8A8390; margin-top:14px;">'
            f"🌙 {e['date'].strftime('%m/%d')} まで滞在をのばすと、星空指数が +{e['diff']} アップするかも。"
            f"少しの延泊で、もっと綺麗な夜空に出会えます。</p>",
            unsafe_allow_html=True,
        )

    st.markdown(
        theme_v3.section_header("SPOTS", "3つの観測スポット", "それぞれ見える方角が違うから、その日の星空に合わせて選べます。"),
        unsafe_allow_html=True,
    )
    latest_day = ctx["trip_all_scores"][0] if ctx["trip_all_scores"] else None
    if latest_day:
        cols = st.columns(3)
        for col, loc_score in zip(cols, latest_day):
            with col:
                is_best = loc_score is latest_day[0]
                if loc_score["moon_sector"]:
                    moon_line = f"🌙 月は{loc_score['moon_sector']}の空（輝面比{loc_score['moon_illumination_pct']}%）"
                else:
                    moon_line = f"🌙 この時間帯は月が沈んでいます（輝面比{loc_score['moon_illumination_pct']}%）"
                photo_name = _SPOT_PHOTO.get(loc_score["location"])
                st.markdown(
                    theme_v3.spot_card(
                        _SPOT_EMOJI.get(loc_score["location"], "✨"),
                        _SPOT_GRADIENT.get(loc_score["location"], "linear-gradient(135deg,#eee,#ddd)"),
                        loc_score["location"], loc_score["location_note"],
                        loc_score["total_score"], loc_score["label"], moon_line, is_best,
                        photo_data_uri=load_photo(photo_name) if photo_name else None,
                    ),
                    unsafe_allow_html=True,
                )

    st.markdown(
        theme_v3.section_header("SCENERY", "美星町のある風景", "満天の星、朝もやの棚田、静かな山あいの町。"),
        unsafe_allow_html=True,
    )
    gallery = [
        ("🌌", "linear-gradient(135deg,#2C2A4A,#565092)"),
        ("🌄", "linear-gradient(135deg,#FFDCA8,#FFB4A2)"),
        ("🍃", "linear-gradient(135deg,#CFE8D5,#9FD8B0)"),
        ("🏕️", "linear-gradient(135deg,#FFE3E9,#FFC2D1)"),
    ]
    gcols = st.columns(4)
    for gcol, (emoji, grad) in zip(gcols, gallery):
        with gcol:
            st.markdown(
                f'<div class="v3-card-img v3-fade" style="background:{grad}; height:120px; border-radius:20px;">{emoji}</div>',
                unsafe_allow_html=True,
            )
    st.caption("📷 実際の写真に差し替え予定のイメージプレースホルダーです")

    if ctx["today"] in ctx["trip_dates"]:
        st.markdown(theme_v3.section_header("TODAY", f"本日（{ctx['today'].strftime('%m/%d')}）の雲の動き"), unsafe_allow_html=True)
        if ctx["cloud_records"] is None:
            st.info("本日の雲データはただいま取得できませんでした。")
        elif not ctx["today_records"]:
            st.info("本日の時間別雲データはまだ取得できませんでした。")
        else:
            today_records = ctx["today_records"]
            cloud_df = pd.DataFrame(
                {
                    "時刻": [r["time"] for r in today_records],
                    "観望期待度": [cloudmsm.viewing_expectation(r["total_cloud_pct"])[0] for r in today_records],
                }
            )
            cloud_chart = (
                alt.Chart(cloud_df)
                .mark_area(
                    line={"color": theme_v3.ACCENT_CORAL, "size": 2.5},
                    color=alt.Gradient(
                        gradient="linear",
                        stops=[
                            alt.GradientStop(color="#FF7E9300", offset=0),
                            alt.GradientStop(color="#FF7E9340", offset=1),
                        ],
                        x1=1, x2=1, y1=1, y2=0,
                    ),
                    interpolate="monotone",
                )
                .encode(
                    x=alt.X("時刻:T", title=None, axis=alt.Axis(format="%H:%M", labelColor="#B7B0BC", gridColor="#F4EEE9")),
                    y=alt.Y("観望期待度:Q", title=None, scale=alt.Scale(domain=[0, 100]), axis=alt.Axis(labelColor="#B7B0BC", gridColor="#F4EEE9")),
                )
                .properties(height=200)
                .configure_view(strokeWidth=0)
                .configure(background="transparent")
            )
            st.altair_chart(cloud_chart, use_container_width=True)
            best_hour = max(today_records, key=lambda r: cloudmsm.viewing_expectation(r["total_cloud_pct"])[0])
            best_score, best_label = cloudmsm.viewing_expectation(best_hour["total_cloud_pct"])
            st.caption(f"🌟 {best_hour['time'].strftime('%H:%M')} ごろが一番おすすめ（{best_label}）")

    st.markdown(theme_v3.section_header("DETAIL", "もっと詳しく見る", "天気・月齢・見える星座など、旅の計画に役立つ詳細データ"), unsafe_allow_html=True)
    for day in ctx["trip_all_scores"]:
        date = day[0]["date"]
        weather_entry = day[0]
        weather_line, dark_window, events_line = weather_and_events_lines(weather_entry)
        with st.expander(f"{date.strftime('%m/%d (%a)')} の詳細"):
            moon_col, info_col = st.columns([1, 5])
            with moon_col:
                svg = moonart.moon_phase_svg(weather_entry["moon_illumination_pct"], weather_entry["moon_waxing"], size=56)
                st.markdown(svg, unsafe_allow_html=True)
                st.caption(moonart.phase_name(weather_entry["moon_age_days"]))
            with info_col:
                st.write(f"☁️ {weather_line}")
                st.write(f"🌌 天文薄明 {dark_window}　｜　✨ {events_line}")
                st.write(f"月齢 {weather_entry['moon_age_days']}（輝面比 {weather_entry['moon_illumination_pct']}%）")

            time_slots = sky.generate_time_slots(weather_entry["dusk"], weather_entry["dawn"])
            raw_sky_by_slot = {
                t: sky.get_sky_objects(t, _REFERENCE_LOCATION["lat"], _REFERENCE_LOCATION["lon"], _REFERENCE_LOCATION["elevation"])
                for t in time_slots
            }
            for loc_score in day:
                stars = theme_v3.stars_for_score(loc_score["total_score"])
                st.markdown(f"**{loc_score['location']}** ／ {stars} ／ {loc_score['label']}")
                direction_visibility = config.LOCATIONS[loc_score["location"]]["direction_visibility"]
                render_sky_expander(time_slots, raw_sky_by_slot, direction_visibility)

    st.markdown(theme_v3.section_header("VOICE", "旅した人たちの声", "美星町を訪れた方からの感想（イメージ）"), unsafe_allow_html=True)
    st.markdown('<span class="v3-sample-tag">※サンプル表示です（実際の口コミではありません）</span>', unsafe_allow_html=True)
    quotes = [
        ("🌸", "彩花さん", "20代・友人と旅行", "写真では伝わらないくらい星が近くて、みんなで声が出ました。また絶対行きたい。"),
        ("🌙", "美咲さん", "30代・カップル旅行", "アプリのおすすめ通りに行ったら本当に雲ひとつない夜空で、忘れられない記念日になりました。"),
        ("⭐", "ゆいさん", "40代・家族旅行", "子どもと一緒に流れ星を見られて、一生の思い出になりました。延泊して正解でした。"),
    ]
    qcols = st.columns(3)
    for qcol, (emoji, name, meta, body) in zip(qcols, quotes):
        with qcol:
            st.markdown(theme_v3.quote_card(emoji, name, meta, body), unsafe_allow_html=True)

    st.markdown(theme_v3.section_header("SNS", "みんなの投稿", "#美星町 のリアルな雰囲気（イメージ）"), unsafe_allow_html=True)
    st.markdown('<span class="v3-sample-tag">※サンプル表示です（実際のSNS投稿ではありません）</span>', unsafe_allow_html=True)
    sns_tiles = [
        ("📸", "linear-gradient(135deg,#FFB4A2,#FFD6A5)"),
        ("🌠", "linear-gradient(135deg,#565092,#8B93FF)"),
        ("🌸", "linear-gradient(135deg,#FFC2D1,#FFE3E9)"),
        ("🏕️", "linear-gradient(135deg,#9FD8B0,#CFE8D5)"),
        ("🌙", "linear-gradient(135deg,#2C2A4A,#565092)"),
        ("☕", "linear-gradient(135deg,#FFE3C7,#FFB4A2)"),
    ]
    scols = st.columns(6)
    for scol, (emoji, grad) in zip(scols, sns_tiles):
        with scol:
            st.markdown(theme_v3.sns_tile(emoji, grad), unsafe_allow_html=True)

    st.markdown(
        '<div class="v3-footer-cta v3-fade">'
        '<p class="v3-section-title" style="margin-bottom:14px;">今夜、星に会いに行きませんか？</p>'
        '<span class="v3-cta">🌟 旅の計画をはじめる</span>'
        "</div>",
        unsafe_allow_html=True,
    )


# =====================================================================================
# 共通データの準備
# =====================================================================================
# Googleサイトなどへの埋め込み時（?embed=true）は、v3固定でバージョン切り替えUIを隠す。
is_embedded = "embed" in st.query_params or st.query_params.get("view") == "lp"

with st.sidebar:
    if is_embedded:
        version = "v3: おしゃれLP"
    else:
        st.header("表示バージョン")
        version = st.radio(
            "デザイン",
            ["v3: おしゃれLP", "v1: ナイトスカイ", "v0: シンプル"],
            index=0,
            help="v0はデザイン刷新前のオリジナル版、v1はダークテーマ版、v3は20〜40代女性を意識した白基調・写真訴求型のLPデザインです。",
        )
        st.divider()
    st.header("滞在期間を入力")
    today = datetime.date.today()
    start_date = st.date_input("到着日", value=today, min_value=today)
    end_date = st.date_input("出発日", value=today + datetime.timedelta(days=2), min_value=start_date)
    st.caption("気象庁の予報は概ね7日先まで。それより先の日付は月齢のみを参考値として表示します。")
    st.divider()
    st.caption("観測スポットの特徴")
    for name, loc in config.LOCATIONS.items():
        dot = _SPOT_COLORS.get(name, "#999")
        st.markdown(f'<span style="color:{dot}; font-weight:700;">●</span> **{name}**: {loc["note"]}', unsafe_allow_html=True)

if end_date < start_date:
    st.error("出発日は到着日より後の日付にしてください。")
    st.stop()

weather_by_date = load_weather()

trip_dates = [start_date + datetime.timedelta(days=i) for i in range((end_date - start_date).days + 1)]
lookahead_dates = [end_date + datetime.timedelta(days=i) for i in range(1, 4)]

trip_all_scores = build_all_location_scores(trip_dates, weather_by_date)
lookahead_all_scores = build_all_location_scores(lookahead_dates, weather_by_date)

trip_best = best_per_day(trip_all_scores)
lookahead_best = best_per_day(lookahead_all_scores)

best_day = max(trip_best, key=lambda d: d["total_score"])
extension = scoring.suggest_extension(trip_best, lookahead_best)

cloud_records = None
today_records = []
if today in trip_dates:
    try:
        cloud_records = load_hourly_cloud()
    except cloudmsm.CloudDataUnavailable:
        cloud_records = None
    if cloud_records is not None:
        today_records = [r for r in cloud_records if r["time"].date() == today]

ctx = {
    "today": today,
    "trip_dates": trip_dates,
    "lookahead_dates": lookahead_dates,
    "trip_all_scores": trip_all_scores,
    "lookahead_all_scores": lookahead_all_scores,
    "best_day": best_day,
    "extension": extension,
    "cloud_records": cloud_records,
    "today_records": today_records,
}

if version.startswith("v3"):
    render_v3(ctx)
elif version.startswith("v1"):
    render_v1(ctx)
else:
    render_v0(ctx)
