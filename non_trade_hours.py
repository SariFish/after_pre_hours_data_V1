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

# Custom hover text with all values for each date
hover_texts = [
    f"Date: {row.Date}<br>"
    f"Regular High: {row['Regular High']:.2f if row['Regular High'] is not None else 'N/A'}<br>"
    f"Regular Low: {row['Regular Low']:.2f if row['Regular Low'] is not None else 'N/A'}<br>"
    f"Pre High: {row['Pre High']:.2f if row['Pre High'] is not None else 'N/A'}<br>"
    f"Pre Low: {row['Pre Low']:.2f if row['Pre Low'] is not None else 'N/A'}<br>"
    f"After High: {row['After High']:.2f if row['After High'] is not None else 'N/A'}<br>"
    f"After Low: {row['After Low']:.2f if row['After Low'] is not None else 'N/A'}"
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

st.plotly_chart(fig, use_container_width=True)

# Daily table
st.subheader("Daily Values Table (August)")
# Optional: format numbers, drop NA if needed
st.dataframe(daily_df.style.format("{:.2f}", na_rep="—"))
