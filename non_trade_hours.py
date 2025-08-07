import streamlit as st
import requests
import pandas as pd
import plotly.graph_objs as go
from datetime import datetime
from calendar import monthrange
import pytz
import yfinance as yf

API_KEY = "uPE6xgvnK5v3vruLdXnWmpZDxSpYTOvf"

st.title("Daily Stock Highs and Lows (Pre-market, Regular, After-hours) + Open/Close")

with st.form("user_inputs"):
    symbol = st.text_input("Enter a stock symbol:", "AAPL").upper()
    today = datetime.now()
    year = st.number_input("Year:", min_value=2000, max_value=2100, value=today.year, step=1)
    month = st.selectbox("Month:", list(range(1, 13)), index=today.month - 1, format_func=lambda m: datetime(2000, m, 1).strftime('%B'))
    submit = st.form_submit_button("Apply")

if submit:
    start_date = f"{year}-{str(month).zfill(2)}-01"
    end_date = f"{year}-{str(month).zfill(2)}-{monthrange(year, month)[1]}"
    st.write(f"Fetching minute-level data for {symbol} ({start_date} to {end_date})...")

    # 1. Get open/close per day from Yahoo (free)
    hist_yf = yf.download(symbol, start=start_date, end=(datetime.strptime(end_date, "%Y-%m-%d") + pd.Timedelta(days=1)).strftime("%Y-%m-%d"))
    hist_yf = hist_yf.reset_index()
    hist_yf['Date'] = hist_yf['Date'].dt.strftime("%Y-%m-%d")
    open_close = hist_yf[['Date', 'Open', 'Close']].copy()
    open_close.set_index('Date', inplace=True)

    # 2. Get all high/low (per session) from Polygon
    url = f"https://api.polygon.io/v2/aggs/ticker/{symbol}/range/1/minute/{start_date}/{end_date}"
    params = {
        "adjusted": "true",
        "sort": "asc",
        "limit": 50000,
        "apiKey": API_KEY
    }
    resp = requests.get(url, params=params)
    data = resp.json()

    if "results" not in data or not data["results"]:
        st.error("No data found. Please check the symbol or try later.")
        st.stop()

    eastern = pytz.timezone("America/New_York")
    df = pd.DataFrame(data["results"])
    df['timestamp'] = pd.to_datetime(df['t'], unit='ms', utc=True).dt.tz_convert(eastern)
    df['date'] = df['timestamp'].dt.date
    df['hour'] = df['timestamp'].dt.hour
    df['minute'] = df['timestamp'].dt.minute

    def get_session(row):
        h, m = row['hour'], row['minute']
        if h < 4 or h > 20 or (h == 20 and m > 0):
            return "none"
        elif h < 9 or (h == 9 and m < 30):
            return "pre"
        elif (h == 9 and m >= 30) or (9 < h < 16) or (h == 16 and m == 0):
            return "regular"
        elif (h > 16) or (h == 16 and m > 0) or (h < 20):
            return "after"
        elif h == 20 and m == 0:
            return "after"
        else:
            return "none"

    df['session'] = df.apply(get_session, axis=1)

    results = []
    for date, group in df.groupby('date'):
        date_str = pd.Timestamp(date).strftime("%Y-%m-%d")
        result = {'Date': date_str}
        for session in ['pre', 'regular', 'after']:
            sess_group = group[group['session'] == session]
            if not sess_group.empty:
                result[f"{session.capitalize()} High"] = sess_group['h'].max()
                result[f"{session.capitalize()} Low"] = sess_group['l'].min()
            else:
                result[f"{session.capitalize()} High"] = None
                result[f"{session.capitalize()} Low"] = None
        # merge open/close from yfinance
        if date_str in open_close.index:
            result['Open'] = open_close.loc[date_str, 'Open']
            result['Close'] = open_close.loc[date_str, 'Close']
        else:
            result['Open'] = None
            result['Close'] = None
        results.append(result)

    daily_df = pd.DataFrame(results).sort_values('Date')
    daily_df['Date'] = daily_df['Date'].astype(str)

    # Table columns in order: Pre, Regular (with open/close), After
    columns_to_format = [
        'Pre High', 'Pre Low',
        'Regular High', 'Regular Low', 'Open', 'Close',
        'After High', 'After Low'
    ]
    ordered_cols = ['Date'] + columns_to_format

    tab1, tab2, tab3 = st.tabs(["Pre-market", "Regular", "After-hours"])

    with tab1:
        fig_pre = go.Figure()
        fig_pre.add_trace(go.Scatter(x=daily_df['Date'], y=daily_df['Pre High'], name="High", mode='lines+markers', line=dict(color='seagreen')))
        fig_pre.add_trace(go.Scatter(x=daily_df['Date'], y=daily_df['Pre Low'], name="Low", mode='lines+markers', line=dict(color='lightgreen')))
        fig_pre.update_layout(title="Pre-market Session", xaxis_title="Date", yaxis_title="Price", legend_title="")
        st.plotly_chart(fig_pre, use_container_width=True)

    with tab2:
        fig_regular = go.Figure()
        fig_regular.add_trace(go.Scatter(x=daily_df['Date'], y=daily_df['Regular High'], name="High", mode='lines+markers', line=dict(color='royalblue')))
        fig_regular.add_trace(go.Scatter(x=daily_df['Date'], y=daily_df['Regular Low'], name="Low", mode='lines+markers', line=dict(color='lightblue')))
        # Add Open/Close as dots
        fig_regular.add_trace(go.Scatter(x=daily_df['Date'], y=daily_df['Open'], name="Open", mode='markers', marker=dict(symbol='diamond', size=10, color='orange')))
        fig_regular.add_trace(go.Scatter(x=daily_df['Date'], y=daily_df['Close'], name="Close", mode='markers', marker=dict(symbol='circle', size=10, color='black')))
        fig_regular.update_layout(title="Regular Session", xaxis_title="Date", yaxis_title="Price", legend_title="")
        st.plotly_chart(fig_regular, use_container_width=True)

    with tab3:
        fig_after = go.Figure()
        fig_after.add_trace(go.Scatter(x=daily_df['Date'], y=daily_df['After High'], name="High", mode='lines+markers', line=dict(color='firebrick')))
        fig_after.add_trace(go.Scatter(x=daily_df['Date'], y=daily_df['After Low'], name="Low", mode='lines+markers', line=dict(color='salmon')))
        fig_after.update_layout(title="After-hours Session", xaxis_title="Date", yaxis_title="Price", legend_title="")
        st.plotly_chart(fig_after, use_container_width=True)

    st.subheader(f"Daily Values Table ({datetime(year, month, 1).strftime('%B %Y')})")
    st.dataframe(
        daily_df[ordered_cols].style.format(
            {col: "{:.2f}" for col in columns_to_format}, na_rep="—"
        ),
        use_container_width=True
    )
