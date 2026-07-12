import datetime

import pandas as pd
import streamlit as st

from star_forecast import cloudmsm, config, moonart, scoring, sky, weather

_REFERENCE_LOCATION = next(iter(config.LOCATIONS.values()))  # 星の見え方の共通計算に使う代表地点

st.set_page_config(page_title="美星町 星空予報", page_icon="🌌", layout="wide")


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


st.title("🌌 美星町 星空予報ダッシュボード")
st.caption(f"{config.TOWN_NAME} を訪れる観光客向けの星空指数プロトタイプ（観測スポット別）")

with st.sidebar:
    st.header("滞在期間を入力")
    today = datetime.date.today()
    start_date = st.date_input("到着日", value=today, min_value=today)
    end_date = st.date_input("出発日", value=today + datetime.timedelta(days=2), min_value=start_date)
    st.caption("気象庁の予報は概ね7日先まで。それより先の日付は月齢のみを参考値として表示します。")
    st.divider()
    st.caption("観測スポットの特徴")
    for name, loc in config.LOCATIONS.items():
        st.caption(f"**{name}**: {loc['note']}")

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

col1, col2 = st.columns([2, 1])
with col1:
    st.subheader(
        f"⭐ この期間のおすすめは {best_day['date'].strftime('%m/%d')}の{best_day['location']}"
        f"（{best_day['label']}・指数{best_day['total_score']}）"
    )
with col2:
    extension = scoring.suggest_extension(trip_best, lookahead_best)
    if extension:
        st.info(
            f"📅 延泊のご提案: {extension['date'].strftime('%m/%d')} は星空指数 {extension['score']} "
            f"（出発日より +{extension['diff']}）。延泊すると、より良い星空が期待できます。"
        )

if today in trip_dates:
    st.divider()
    st.subheader(f"🌤 本日（{today.strftime('%m/%d')}）の詳細な雲の動き")
    try:
        cloud_records = load_hourly_cloud()
    except cloudmsm.CloudDataUnavailable:
        cloud_records = None

    if cloud_records is None:
        st.warning("MSM雲データの取得に失敗しました。上の日別予報のみをご参照ください。")
    else:
        today_records = [r for r in cloud_records if r["time"].date() == today]
        if not today_records:
            st.info("本日の時間別雲データはまだ取得できませんでした。")
        else:
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
for day in trip_all_scores + lookahead_all_scores:
    for loc_score in day:
        chart_rows.append(
            {"日付": loc_score["date"].strftime("%m/%d"), "観測スポット": loc_score["location"], "星空指数": loc_score["total_score"]}
        )
chart_df = pd.DataFrame(chart_rows).pivot(index="日付", columns="観測スポット", values="星空指数")
chart_df = chart_df.reindex([d.strftime("%m/%d") for d in trip_dates + lookahead_dates])
st.bar_chart(chart_df, stack=False)

st.divider()
st.subheader("日別・観測スポット別の詳細")

for day in trip_all_scores:
    date = day[0]["date"]
    with st.container(border=True):
        st.markdown(f"#### {date.strftime('%m/%d (%a)')}")

        weather_entry = day[0]
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
                with col.expander("🔭 時間帯別に見える星"):
                    if not time_slots:
                        st.caption("天文薄明の時間帯を計算できませんでした。")
                    for t in time_slots:
                        annotated = sky.annotate_visibility(raw_sky_by_slot[t], direction_visibility)
                        st.markdown(f"**{t.strftime('%H:%M')}**")
                        if annotated["asterisms"]:
                            st.caption("🌟 " + "・".join(annotated["asterisms"]) + " が見えます")
                        for s in annotated["stars"][:6]:
                            st.markdown(
                                f"- {s['jp']}（{s['constellation']}）高度約{s['altitude']}° {s['sector']}の空 {s['visibility_label']}"
                            )
                        for p in annotated["planets"]:
                            st.markdown(
                                f"- {p['jp']} 高度約{p['altitude']}° {p['sector']}の空 {p['visibility_label']}"
                            )
                        if not annotated["stars"] and not annotated["planets"]:
                            st.caption("この時間帯に見える主要な星はありません。")

st.divider()
with st.expander("この指数の算出方法について"):
    st.markdown(
        """
- **天気予報あり（概ね7日先まで）**: 天気予報の空模様と降水確率から算出したスコアを55%、月明かりの影響を35%、天文イベントのボーナスを加味します。天気は3スポット共通（気象庁の岡山県南部予報）です。
- **天気予報なし（8日先〜1か月程度先）**: 天気はまだ予測できないため、月齢・月の出没時刻から算出した「月明かりの影響が少ないか」を主な指標にした参考値を表示します。
- **観測スポット別の違い**: 各スポットは方角ごとの見やすさが異なります（美星天文台＝西がやや苦手、星空公園＝東が得意、竜王山公園＝南が得意）。天文薄明の時間帯に月がどの方角にあるかを計算し、そのスポットで見やすい方角に月がある場合は影響を大きく、見えにくい方角にある場合は影響を小さく補正しています。
- **時間帯別に見える星**: 3スポットとも見えている星そのものはほぼ共通（同じ空）ですが、その方角がスポットごとに見やすいかどうかで「◎見やすい／○普通／△やや見えにくい」を表示します。高度15°以上に昇っている主要な恒星・惑星が対象です。
- **本日の詳細な雲の動き**: 気象庁MSM（メソモデル）の実況〜短期予報データから、当日のみ1時間ごとの雲量を取得して表示します（全雲量から算出した観望期待度）。日別予報とは別に、当日に限りより細かい時間解像度で確認できます。
        """
    )
