import streamlit as st
from datetime import datetime, date, timedelta
import calendar
import requests
import jpholiday
import json
import os

# --- 定数定義 ---

# 天気コードから絵文字へのマッピング
WEATHER_CODE_TO_EMOJI = {
    "100": "☀️", "101": "🌤️", "102": "🌦️", "103": "🌨️", "104": "🌨️", "105": "🌨️",
    "106": "🌨️", "107": "🌨️", "108": "🌨️", "110": "☀️", "111": "🌤️", "112": "🌧️",
    "113": "🌧️", "114": "🌧️", "115": "🌨️", "116": "🌨️", "117": "🌨️", "118": "🌨️",
    "119": "🌨️", "120": "🌨️", "121": "🌨️", "122": "🌨️", "123": "☀️", "124": "☀️",
    "125": "☀️", "126": "☀️", "127": "☀️", "128": "☀️", "130": "☀️", "131": "☀️",
    "132": "☀️", "140": "🌧️", "160": "🌨️", "170": "🌨️", "181": "🌨️", "200": "☁️",
    "201": "🌥️", "202": "🌧️", "203": "🌧️", "204": "🌧️", "205": "🌧️", "206": "🌧️",
    "207": "🌧️", "208": "🌧️", "209": "🌧️", "210": "☁️", "211": "🌥️", "212": "🌧️",
    "213": "🌧️", "214": "🌧️", "215": "🌨️", "216": "🌨️", "217": "🌨️", "218": "🌨️",
    "219": "🌨️", "220": "🌨️", "221": "🌨️", "222": "🌨️", "223": "☁️", "224": "☀️",
    "225": "☀️", "226": "☀️", "227": "☀️", "228": "🌧️", "229": "🌧️", "230": "🌧️",
    "231": "☀️", "240": "🌧️", "250": "🌨️", "260": "🌨️", "270": "🌨️", "281": "🌨️",
    "300": "🌧️", "301": "🌧️", "302": "🌧️", "303": "🌧️", "304": "🌧️", "306": "🌧️",
    "308": "🌧️", "309": "🌧️", "311": "🌧️", "313": "🌧️", "314": "🌧️", "315": "🌧️",
    "316": "🌧️", "317": "🌧️", "320": "☁️", "321": "☁️", "322": "🌨️", "323": "☀️",
    "324": "☀️", "325": "☀️", "326": "🌧️", "327": "🌧️", "328": "🌧️", "329": "🌧️",
    "340": "🌨️", "350": "🌨️", "361": "🌨️", "371": "🌨️", "400": "❄️", "401": "❄️",
    "402": "❄️", "403": "❄️", "405": "❄️", "406": "❄️", "407": "❄️", "409": "❄️",
    "411": "❄️", "413": "❄️", "414": "❄️", "415": "❄️", "416": "❄️", "417": "❄️",
    "420": "❄️", "421": "❄️", "422": "❄️", "423": "❄️", "425": "❄️", "426": "❄️",
    "427": "❄️"
}

# 気象庁のエリアコード
AREA_CODES = {
    "札幌": "016000",
    "仙台": "040000",
    "東京": "130000",
    "名古屋": "230000",
    "大阪": "270000",
    "広島": "340000",
    "福岡": "400000",
    "那覇": "471000",
}

# データファイルのパス
DATA_FILE = "schedule_data.json"

# --- ローカルファイル保存関連の関数 ---

def save_schedules_to_file(schedules):
    """予定データをJSONファイルに保存"""
    try:
        # dateオブジェクトを文字列に変換
        schedules_str = {}
        for date_obj, memo in schedules.items():
            schedules_str[date_obj.strftime('%Y-%m-%d')] = memo
        
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(schedules_str, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        st.error(f"ファイルへの保存に失敗しました: {e}")
        return False

def load_schedules_from_file():
    """JSONファイルから予定データを読み込み"""
    try:
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                schedules_str = json.load(f)
            
            # 文字列をdateオブジェクトに変換
            schedules = {}
            for date_str, memo in schedules_str.items():
                date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
                schedules[date_obj] = memo
            
            return schedules
        else:
            return {}
    except Exception as e:
        st.error(f"ファイルからの読み込みに失敗しました: {e}")
        return {}

# --- 既存の関数 ---

@st.cache_data(ttl=600)
def get_weekly_weather(area_code="130000"):
    """気象庁のAPIから週間天気予報を取得する"""
    url = f"https://www.jma.go.jp/bosai/forecast/data/forecast/{area_code}.json"
    try:
        res = requests.get(url)
        res.raise_for_status()
        data = res.json()
    except requests.exceptions.RequestException as e:
        st.warning(f"天気情報の取得に失敗しました: {e}")
        return {}

    if not data or not data[0].get("timeSeries"):
        return {}
    
    time_series = data[0]["timeSeries"][0]
    dates = time_series.get("timeDefines", [])
    weather_codes = time_series.get("areas", [{}])[0].get("weatherCodes", [])

    weather_map = {}
    for d_str, code in zip(dates, weather_codes):
        dt = datetime.fromisoformat(d_str.replace('Z', '+00:00')).date()
        weather_map[dt] = code
    return weather_map

def initialize_session_state():
    """セッションステートを初期化する"""
    if "current_date" not in st.session_state:
        st.session_state.current_date = date.today()
    if "schedules" not in st.session_state:
        # 初期化時にファイルからデータを読み込み
        st.session_state.schedules = load_schedules_from_file()
    if "selected_date" not in st.session_state:
        st.session_state.selected_date = date.today()

def draw_calendar(current_date, schedules, weather_data, holidays):
    """カレンダーを描画する"""
    year = current_date.year
    month = current_date.month
    
    st.header(f"{year}年 {month}月")

    cal = calendar.Calendar()
    month_calendar = cal.monthdatescalendar(year, month)
    
    weekdays = ["月", "火", "水", "木", "金", "土", "日"]
    cols = st.columns(7)
    for col, weekday in zip(cols, weekdays):
        col.markdown(f"<p style='text-align: center;'><b>{weekday}</b></p>", unsafe_allow_html=True)

    for week in month_calendar:
        cols = st.columns(7)
        for i, d in enumerate(week):
            with cols[i]:
                if d.month != month:
                    st.markdown(f"<p style='color: lightgray; text-align: right;'>{d.day}</p>", unsafe_allow_html=True)
                else:
                    with st.container(border=True):
                        holiday_name = holidays.get(d)
                        day_color = "red" if holiday_name or d.weekday() == 6 else "blue" if d.weekday() == 5 else "black"
                        day_display = f"<p style='color: {day_color}; text-align: right; margin-bottom: 0;'><b>{d.day}</b></p>"
                        if holiday_name:
                            day_display += f"<p style='color: red; font-size: 0.8em; text-align: right; margin-top:0;'>{holiday_name}</p>"
                        st.markdown(day_display, unsafe_allow_html=True)
                        
                        weather_emoji = WEATHER_CODE_TO_EMOJI.get(weather_data.get(d, ""), "")
                        if weather_emoji:
                            st.markdown(f"<p style='text-align: right; font-size: 1.5em; margin-bottom: 0;'>{weather_emoji}</p>", unsafe_allow_html=True)
                        
                        if d in schedules and schedules[d]:
                            st.markdown("<p style='text-align: right; color: green; margin-top: 0;'>●</p>", unsafe_allow_html=True)

                        if st.button("選択", key=f"select_{d}", use_container_width=True):
                            st.session_state.selected_date = d
                            st.rerun()

def schedule_editor():
    """選択された日付の予定を編集するフォーム"""
    selected = st.session_state.selected_date
    st.subheader(f"📝 {selected.strftime('%Y/%m/%d (%a)')} の予定・日記")

    current_memo = st.session_state.schedules.get(selected, "")
    new_memo = st.text_area("内容", value=current_memo, height=150, label_visibility="collapsed")

    col1, col2, col3 = st.columns([1,1,5])
    with col1:
        if st.button("💾 保存", use_container_width=True):
            # セッションステートを更新
            st.session_state.schedules[selected] = new_memo
            
            # ファイルに保存
            if save_schedules_to_file(st.session_state.schedules):
                st.success("保存しました！")
            else:
                st.error("ファイルへの保存に失敗しました")
            
            st.rerun()
    
    with col2:
        if st.button("🗑️ 削除", use_container_width=True):
            if selected in st.session_state.schedules:
                # セッションステートから削除
                del st.session_state.schedules[selected]
                
                # ファイルに保存
                if save_schedules_to_file(st.session_state.schedules):
                    st.success("削除しました！")
                else:
                    st.error("ファイルへの保存に失敗しました")
                
                st.rerun()
            else:
                st.info("この日には保存された予定がありません。")

# --- メイン処理 ---
def main():
    st.set_page_config(layout="wide")
    st.title("📅 スケジュール管理アプリ (ローカルファイル保存)")

    initialize_session_state()

    with st.sidebar:
        st.header("設定")
        
        # データファイルの状態表示
        if os.path.exists(DATA_FILE):
            st.success(f"✅ データファイル: {DATA_FILE}")
        else:
            st.info("ℹ️ データファイルは初回保存時に作成されます")
            
        # データ再読み込みボタン
        if st.button("🔄 データを再読み込み", use_container_width=True):
            st.session_state.schedules = load_schedules_from_file()
            st.success("データを再読み込みしました！")
            st.rerun()

        selected_area_name = st.selectbox("地域を選択", AREA_CODES.keys())
        area_code = AREA_CODES[selected_area_name]

        st.subheader("カレンダー移動")
        col1, col2 = st.columns(2)
        if col1.button("◀️ 前月", use_container_width=True):
            st.session_state.current_date = st.session_state.current_date.replace(day=1) - timedelta(days=1)
            st.rerun()
        if col2.button("翌月 ▶️", use_container_width=True):
            st.session_state.current_date = st.session_state.current_date.replace(day=28) + timedelta(days=4)
            st.session_state.current_date = st.session_state.current_date.replace(day=1)
            st.rerun()
        
        if st.button("今月に戻る", use_container_width=True):
            st.session_state.current_date = date.today()
            st.session_state.selected_date = date.today()
            st.rerun()

        st.subheader("保存済みの予定一覧")
        sorted_schedules = sorted(st.session_state.schedules.items())
        for d, memo in sorted_schedules:
            if memo:
                with st.expander(f"{d.strftime('%Y/%m/%d')}"):
                    st.write(memo)

    # --- メインコンテンツ ---
    
    # データ取得
    weather_data = get_weekly_weather(area_code)
    
    # 祝日リストを取得し、{日付: 祝日名} の辞書に変換します
    holiday_list = jpholiday.year_holidays(st.session_state.current_date.year)
    holidays = {dt: name for dt, name in holiday_list}
    
    # カレンダーと予定エディタを2カラムで表示
    cal_col, edit_col = st.columns([2, 1])

    with cal_col:
        draw_calendar(st.session_state.current_date, st.session_state.schedules, weather_data, holidays)
    
    with edit_col:
        schedule_editor()


if __name__ == "__main__":
    main()