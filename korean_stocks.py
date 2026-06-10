import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta

st.set_page_config(page_title="국내 주식 대시보드", layout="wide")

STOCKS = {
    "제룡전기": "033100.KQ",
    "인텔리안테크": "189300.KQ",
    "대덕전자": "353200.KQ",
    "인트론바이오": "048530.KQ",
    "에코프로": "086520.KQ",
    "에코프로비엠": "247540.KQ",
    "HLB": "028300.KQ",
    "알테오젠": "196170.KQ",
    "카카오게임즈": "293490.KQ",
    "펄어비스": "263750.KQ",
}

st.title("📈 국내 주식 대시보드")
st.caption("데이터 출처: Yahoo Finance (yfinance)")

col_period, col_refresh = st.columns([3, 1])
with col_period:
    period = st.selectbox("조회 기간", ["1mo", "3mo", "6mo", "1y", "2y"], index=2,
                          format_func=lambda x: {"1mo":"1개월","3mo":"3개월","6mo":"6개월","1y":"1년","2y":"2년"}[x])
with col_refresh:
    st.write("")
    refresh = st.button("🔄 새로고침")

@st.cache_data(ttl=300, show_spinner=False)
def load_data(tickers: dict, period: str):
    rows = []
    hist_data = {}
    for name, ticker in tickers.items():
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            hist = stock.history(period=period)
            if hist.empty:
                continue
            hist_data[name] = hist
            current = hist["Close"].iloc[-1]
            prev = hist["Close"].iloc[-2] if len(hist) > 1 else current
            change = current - prev
            change_pct = (change / prev) * 100
            rows.append({
                "종목명": name,
                "티커": ticker,
                "현재가 (₩)": int(current),
                "전일 대비 (₩)": int(change),
                "등락률 (%)": round(change_pct, 2),
                "거래량": int(hist["Volume"].iloc[-1]),
                "52주 최고": int(hist["Close"].max()),
                "52주 최저": int(hist["Close"].min()),
            })
        except Exception:
            continue
    return pd.DataFrame(rows), hist_data

if refresh:
    st.cache_data.clear()

with st.spinner("데이터 불러오는 중..."):
    df, hist_data = load_data(STOCKS, period)

if df.empty:
    st.error("데이터를 불러오지 못했습니다. 잠시 후 다시 시도해주세요.")
    st.stop()

st.subheader("종목 현황 요약")

def color_change(val):
    if isinstance(val, (int, float)):
        color = "red" if val > 0 else ("blue" if val < 0 else "black")
        return f"color: {color}"
    return ""

styled = df.style\
    .map(color_change, subset=["전일 대비 (₩)", "등락률 (%)"])\
    .format({
        "현재가 (₩)": "{:,}",
        "전일 대비 (₩)": "{:+,}",
        "등락률 (%)": "{:+.2f}%",
        "거래량": "{:,}",
        "52주 최고": "{:,}",
        "52주 최저": "{:,}",
    })

st.dataframe(styled, use_container_width=True, hide_index=True)

st.divider()
st.subheader("주가 차트")

cols = st.columns(2)
for i, (name, hist) in enumerate(hist_data.items()):
    with cols[i % 2]:
        fig = go.Figure()
        fig.add_trace(go.Candlestick(
            x=hist.index,
            open=hist["Open"],
            high=hist["High"],
            low=hist["Low"],
            close=hist["Close"],
            name=name,
            increasing_line_color="red",
            decreasing_line_color="blue",
        ))
        fig.update_layout(
            title=name,
            height=300,
            margin=dict(l=10, r=10, t=40, b=10),
            xaxis_rangeslider_visible=False,
            showlegend=False,
        )
        st.plotly_chart(fig, use_container_width=True)

st.divider()
st.subheader("등락률 비교")

bar_df = df.sort_values("등락률 (%)", ascending=False)
colors = ["red" if v >= 0 else "blue" for v in bar_df["등락률 (%)"]]

fig_bar = go.Figure(go.Bar(
    x=bar_df["종목명"],
    y=bar_df["등락률 (%)"],
    marker_color=colors,
    text=[f"{v:+.2f}%" for v in bar_df["등락률 (%)"]],
    textposition="outside",
))
fig_bar.update_layout(height=350, margin=dict(t=20, b=20), yaxis_title="등락률 (%)")
st.plotly_chart(fig_bar, use_container_width=True)

st.caption(f"마지막 업데이트: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | 캐시 TTL: 5분")
