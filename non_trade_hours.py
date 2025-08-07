import streamlit as st
import requests
import pandas as pd
import plotly.graph_objs as go
from datetime import datetime
from calendar import monthrange

API_KEY = "uPE6xgvnK5v3vruLdXnWmpZDxSpYTOvf"

st.title("Daily Stock Highs and Lows (Regular, Pre-market, After-hours) - August")

symbol = st.text_input("Enter a stock symbol:", "AAPL").upper()

now = datetime.now()
year = now.year
month = 8
start_date = f"{year}-08-01"
end_date = f"{year}-08-{monthrange(year, month)[1]}"

url = f"https://api.polygon.io/v2/aggs/ticker/{symbol}/range/1/minute/{start_date}/{end_date}"
params = {
    "adjusted": "true",
    "sort": "asc",
    "limit": 50000,
    "apiKey": API_KEY
}
st.write(f"Fetching minute-level data for {symbol} ({start_date} to {end_date})...")
resp = requests.get(url, params=params)
data = resp.json()

if "results" not in data or not data["results"]:
    st.error("No data found. Please check the symbol or try later.")
    st.stop()

df = pd.DataFrame(data["results"])
df['timestamp'] = pd.to_datetime(df['t'], unit='ms')
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
    result = {'Date': date}
    for session in ['regular', 'pre', 'after']:
        sess_group = group[group['session'] == session]
        if not sess_group.empty:
            result[f"{session.capitalize()} High"] = sess_group['h'].max()
            result[f"{session.capitalize()} Low"] = sess_group['l'].min()
        else:
            result[f"{session.capitalize()} High"] = None
            result[f"{session.capitalize()} Low"] = None
    results.append(result)

daily_df = pd.DataFrame(results).sort_values('Date')

def safe_fmt(val):
    return f"{val:.2f}" if val is not None else "N/A"
    
hover_texts = [
    f"Date: {row.Date}<br>"
    f"Regular High: {safe_fmt(row['Regular High'])}<br>"
    f"Regular Low: {safe_fmt(row['Regular Low'])}<br>"
    f"Pre High: {safe_fmt(row['Pre High'])}<br>"
    f"Pre Low: {safe_fmt(row['Pre Low'])}<br>"
    f"After High: {safe_fmt(row['After High'])}<br>"
    f"After Low: {safe_fmt(row['After Low'])}"
    for _, row in daily_df.iterrows()
]

fig = go.Figure()
# High/Low - Regular
fig.add_trace(go.Scatter(
    x=daily_df['Date'], y=daily_df['Regular High'],
    name="High (Regular)", mode='lines+markers',
    hovertext=hover_texts, hoverinfo="text"
))
fig.add_trace(go.Scatter(
    x=daily_df['Date'], y=daily_df['Regular Low'],
    name="Low (Regular)", mode='lines+markers',
    hovertext=hover_texts, hoverinfo="text"
))
# High/Low - After-hours
fig.add_trace(go.Scatter(
    x=daily_df['Date'], y=daily_df['After High'],
    name="High (After-hours)", mode='lines+markers',
    hovertext=hover_texts, hoverinfo="text"
))
fig.add_trace(go.Scatter(
    x=daily_df['Date'], y=daily_df['After Low'],
    name="Low (After-hours)", mode='lines+markers',
    hovertext=hover_texts, hoverinfo="text"
))
# High/Low - Pre-market
fig.add_trace(go.Scatter(
    x=daily_df['Date'], y=daily_df['Pre High'],
    name="High (Pre-market)", mode='lines+markers',
    hovertext=hover_texts, hoverinfo="text"
))
fig.add_trace(go.Scatter(
    x=daily_df['Date'], y=daily_df['Pre Low'],
    name="Low (Pre-market)", mode='lines+markers',
    hovertext=hover_texts, hoverinfo="text"
))

fig.update_layout(
    title=f"{symbol} - Daily High/Low (August {year})",
    xaxis_title="Date",
    yaxis_title="Price",
    legend_title="Session",
    height=650,
    margin=dict(t=70, r=20, l=30, b=30)
)
import streamlit as st
import plotly.graph_objs as go

# Assume daily_df is ready as in your code

tab1, tab2, tab3 = st.tabs(["Regular", "Pre-market", "After-hours"])

with tab1:
    fig_regular = go.Figure()
    fig_regular.add_trace(go.Scatter(x=daily_df['Date'], y=daily_df['Regular High'], name="High", mode='lines+markers', line=dict(color='royalblue')))
    fig_regular.add_trace(go.Scatter(x=daily_df['Date'], y=daily_df['Regular Low'], name="Low", mode='lines+markers', line=dict(color='lightblue')))
    fig_regular.update_layout(title="Regular Session", xaxis_title="Date", yaxis_title="Price", legend_title="")
    st.plotly_chart(fig_regular, use_container_width=True)

with tab2:
    fig_pre = go.Figure()
    fig_pre.add_trace(go.Scatter(x=daily_df['Date'], y=daily_df['Pre High'], name="High", mode='lines+markers', line=dict(color='seagreen')))
    fig_pre.add_trace(go.Scatter(x=daily_df['Date'], y=daily_df['Pre Low'], name="Low", mode='lines+markers', line=dict(color='lightgreen')))
    fig_pre.update_layout(title="Pre-market Session", xaxis_title="Date", yaxis_title="Price", legend_title="")
    st.plotly_chart(fig_pre, use_container_width=True)

with tab3:
    fig_after = go.Figure()
    fig_after.add_trace(go.Scatter(x=daily_df['Date'], y=daily_df['After High'], name="High", mode='lines+markers', line=dict(color='firebrick')))
    fig_after.add_trace(go.Scatter(x=daily_df['Date'], y=daily_df['After Low'], name="Low", mode='lines+markers', line=dict(color='salmon')))
    fig_after.update_layout(title="After-hours Session", xaxis_title="Date", yaxis_title="Price", legend_title="")
    st.plotly_chart(fig_after, use_container_width=True)

st.plotly_chart(fig, use_container_width=True)

# Daily table
st.subheader("Daily Values Table (August)")
# Optional: format numbers, drop NA if needed
st.dataframe(daily_df.style.format("{:.2f}", na_rep="—"))


