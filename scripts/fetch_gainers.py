from __future__ import annotations

import datetime as dt
import math
import os
from typing import Any

import pandas as pd
import requests
import yfinance as yf


MIN_CHANGE_PERCENT = 10
MAX_SOURCE_COUNT = 75
MAX_OUTPUT_COUNT = 25


def safe_float(value: Any) -> float | None:
    try:
        if value is None:
            return None
        number = float(value)
        if math.isnan(number):
            return None
        return number
    except (TypeError, ValueError):
        return None


def fmt_money(value: Any) -> str:
    number = safe_float(value)
    if number is None:
        return "N/A"
    if abs(number) >= 1_000_000_000:
        return f"{number / 1_000_000_000:.2f}B"
    if abs(number) >= 1_000_000:
        return f"{number / 1_000_000:.2f}M"
    return f"{number:.2f}"


def fmt_pct(value: Any) -> str:
    number = safe_float(value)
    if number is None:
        return "N/A"
    return f"{number * 100:.1f}%"


def get_top_gainers() -> tuple[list[str], dict[str, dict[str, Any]]]:
    url = "https://query1.finance.yahoo.com/v1/finance/screener/predefined/saved"
    params = {"formatted": "false", "count": MAX_SOURCE_COUNT, "scrIds": "day_gainers"}
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, params=params, headers=headers, timeout=30)
    response.raise_for_status()
    quotes = response.json()["finance"]["result"][0]["quotes"]
    raw_map = {q["symbol"]: q for q in quotes if q.get("symbol")}
    symbols = [
        q["symbol"]
        for q in quotes
        if safe_float(q.get("regularMarketChangePercent")) is not None
        and safe_float(q.get("regularMarketChangePercent")) >= MIN_CHANGE_PERCENT
    ]
    return symbols[:MAX_OUTPUT_COUNT], raw_map


def calculate_rsi(close: pd.Series, period: int = 14) -> str:
    if len(close) <= period:
        return "N/A"
    delta = close.diff()
    gain = delta.clip(lower=0).tail(period).mean()
    loss = -delta.clip(upper=0).tail(period).mean()
    if loss == 0 or pd.isna(loss):
        return "N/A"
    rsi = 100 - 100 / (1 + gain / loss)
    return f"{rsi:.1f}"


def calculate_score(row: dict[str, Any]) -> int:
    score = 0
    rsi = safe_float(row["RSI_14"])
    rvol = safe_float(row["RVOL_20D"])
    rev_growth = safe_float(str(row["Rev_Growth_YoY"]).replace("%", ""))
    op_margin = safe_float(str(row["Op_Margin"]).replace("%", ""))
    upside = safe_float(str(row["Implied_Upside_%"]).replace("%", ""))

    if rsi is not None and 45 <= rsi <= 75:
        score += 15
    if rvol is not None and rvol >= 2:
        score += 20
    if str(row["Analyst_Rating"]).lower().find("buy") >= 0:
        score += 15
    if rev_growth is not None and rev_growth >= 15:
        score += 20
    if op_margin is not None and op_margin >= 10:
        score += 15
    if upside is not None and upside >= 10:
        score += 15
    return min(score, 100)


def bucket(score: int) -> str:
    if score >= 70:
        return "Watchlist candidate"
    if score >= 45:
        return "Needs confirmation"
    return "Speculative / news-only"


def enrich(symbol: str, raw: dict[str, Any]) -> dict[str, Any]:
    ticker = yf.Ticker(symbol)
    info = ticker.info or {}
    hist = ticker.history(period="1y", interval="1d", auto_adjust=False)

    price = safe_float(raw.get("regularMarketPrice")) or safe_float(info.get("currentPrice")) or 0
    change_pct = safe_float(raw.get("regularMarketChangePercent")) or 0
    volume = safe_float(raw.get("regularMarketVolume")) or safe_float(info.get("volume")) or 0
    avg_volume = safe_float(info.get("averageVolume")) or safe_float(info.get("averageDailyVolume3Month")) or 0
    rvol = round(volume / avg_volume, 2) if avg_volume else "N/A"

    close = hist["Close"].dropna() if not hist.empty else pd.Series(dtype=float)
    high = hist["High"].dropna() if not hist.empty else pd.Series(dtype=float)
    low = hist["Low"].dropna() if not hist.empty else pd.Series(dtype=float)
    ma8 = round(close.tail(8).mean(), 2) if len(close) >= 8 else "N/A"
    ma50 = round(close.tail(50).mean(), 2) if len(close) >= 50 else "N/A"
    ma200 = round(close.tail(200).mean(), 2) if len(close) >= 200 else "N/A"
    rsi = calculate_rsi(close)
    atr = round((high - low).tail(14).mean() / price * 100, 2) if price and len(high) >= 14 else "N/A"

    try:
        targets = ticker.analyst_price_targets or {}
    except Exception:
        targets = {}
    target_low = safe_float(targets.get("low") or info.get("targetLowPrice"))
    target_mean = safe_float(targets.get("mean") or info.get("targetMeanPrice"))
    target_high = safe_float(targets.get("high") or info.get("targetHighPrice"))
    implied_upside = ((target_mean / price) - 1) * 100 if target_mean and price else None

    buy_count = hold_count = sell_count = 0
    analyst_rating = info.get("averageAnalystRating") or "N/A"
    try:
        rec = ticker.recommendations_summary
        if rec is not None and not rec.empty:
            latest = rec.iloc[0]
            buy_count = int(latest.get("strongBuy", 0) + latest.get("buy", 0))
            hold_count = int(latest.get("hold", 0))
            sell_count = int(latest.get("sell", 0) + latest.get("strongSell", 0))
    except Exception:
        pass

    row = {
        "Symbol": symbol,
        "Company": info.get("longName") or raw.get("longName") or raw.get("shortName") or symbol,
        "Sector": info.get("sector") or "N/A",
        "Industry": info.get("industry") or "N/A",
        "Price": round(price, 2) if price else "N/A",
        "Change_%": round(change_pct, 2),
        "Volume": int(volume) if volume else "N/A",
        "Dollar_Volume": fmt_money(price * volume if price and volume else None),
        "RVOL_20D": rvol,
        "8D_MA": ma8,
        "50D_MA": ma50,
        "200D_MA": ma200,
        "RSI_14": rsi,
        "ATR_%": atr,
        "Market_Cap": fmt_money(info.get("marketCap")),
        "PS_Ratio": round(info["priceToSalesTrailing12Months"], 2) if info.get("priceToSalesTrailing12Months") else "N/A",
        "Forward_PE": round(info["forwardPE"], 2) if info.get("forwardPE") else "N/A",
        "Rev_Growth_YoY": fmt_pct(info.get("revenueGrowth")),
        "EPS_Growth_YoY": fmt_pct(info.get("earningsGrowth") or info.get("earningsQuarterlyGrowth")),
        "Gross_Margin": fmt_pct(info.get("grossMargins")),
        "Op_Margin": fmt_pct(info.get("operatingMargins")),
        "Short_%_Float": fmt_pct(info.get("shortPercentOfFloat")),
        "Analyst_Rating": analyst_rating,
        "Buy_Count": buy_count,
        "Hold_Count": hold_count,
        "Sell_Count": sell_count,
        "Target_Low": round(target_low, 2) if target_low else "N/A",
        "Target_Mean": round(target_mean, 2) if target_mean else "N/A",
        "Target_High": round(target_high, 2) if target_high else "N/A",
        "Implied_Upside_%": f"{implied_upside:.1f}%" if implied_upside is not None else "N/A",
        "Description": (info.get("longBusinessSummary") or "N/A")[:320],
    }
    row["Score"] = calculate_score(row)
    row["Bucket"] = bucket(row["Score"])
    return row


def run() -> pd.DataFrame:
    symbols, raw_map = get_top_gainers()
    rows = []
    for symbol in symbols:
        try:
            rows.append(enrich(symbol, raw_map[symbol]))
        except Exception as exc:
            print(f"Skipping {symbol}: {exc}")
    df = pd.DataFrame(rows)
    if not df.empty:
        df = df.sort_values(["Score", "Change_%"], ascending=[False, False])
    date_str = dt.datetime.utcnow().strftime("%Y-%m-%d")
    os.makedirs("data", exist_ok=True)
    path = f"data/gainers_{date_str}.csv"
    df.to_csv(path, index=False)
    print(f"Saved {len(df)} rows to {path}")
    return df


if __name__ == "__main__":
    run()

