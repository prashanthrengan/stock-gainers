#!/usr/bin/env python
"""Run the stock discovery workflow over an input CSV.

This MVP uses the fields already present in the gainers CSV. Later versions can
call provider-specific scripts from the enrichment skills before this scoring
and publishing step.
"""

from __future__ import annotations

import argparse
import csv
import json
import ssl
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, quote
from urllib.request import Request, urlopen


OUTPUT_COLUMNS = [
    "Rank",
    "Symbol",
    "Company",
    "Theme",
    "Price",
    "Change($)",
    "Change(%)",
    "Volume",
    "Dollar Volume",
    "RVOL 20D",
    "Catalyst Type",
    "Catalyst Summary",
    "Catalyst Score",
    "Catalyst Confidence",
    "Market Cap",
    "Enterprise Value",
    "PS Ratio",
    "Forward PE",
    "PEG Ratio",
    "Rev Growth YoY",
    "EPS Growth YoY",
    "Gross Margin",
    "Operating Margin",
    "FCF Margin",
    "Analyst Rating",
    "Analyst Count",
    "Buy Count",
    "Hold Count",
    "Sell Count",
    "Target Low",
    "Target Avg",
    "Target High",
    "Implied Upside %",
    "Next FY Revenue Estimate",
    "Next FY Revenue Growth Estimate",
    "Next FY EPS Estimate",
    "Next FY EPS Growth Estimate",
    "Estimate Revision Trend",
    "50-Day MA",
    "200-Day MA",
    "Price vs 50D MA %",
    "Price vs 200D MA %",
    "Dist 52W High %",
    "RSI 14",
    "ATR 14 %",
    "Float Shares",
    "Short % Float",
    "Recent Offering",
    "Dilution Risk",
    "Low Float",
    "Growth Score",
    "Quality Score",
    "Momentum Score",
    "Valuation Score",
    "Liquidity Score",
    "Risk Score",
    "Final Score",
    "Support Price",
    "Stop Review Price",
    "Hold Zone Low",
    "Hold Zone High",
    "Trim / Partial Sell Price",
    "Stretch Sell Price",
    "Price Level Basis",
    "Growth Analyst Note",
    "Growth Analyst Confidence",
    "Growth Analyst Reason",
    "Momentum Analyst Note",
    "Momentum Analyst Confidence",
    "Momentum Analyst Reason",
    "Valuation Analyst Note",
    "Valuation Analyst Confidence",
    "Valuation Analyst Reason",
    "Risk Analyst Note",
    "Risk Analyst Confidence",
    "Risk Analyst Reason",
    "PM Verdict",
    "PM Confidence",
    "PM Reason",
    "Recommendation",
    "Confidence 1-5",
    "Next Research Step",
    "Data Quality Notes",
    "Analyst Data Quality",
    "Input Source",
    "Run Timestamp",
]


def parse_number(value: str | None) -> float | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text or text.upper() in {"N/A", "NA", "NONE", "NULL", "UNKNOWN"}:
        return None
    multiplier = 1.0
    if text.endswith("%"):
        text = text[:-1]
    if text.endswith("B"):
        multiplier = 1_000_000_000.0
        text = text[:-1]
    elif text.endswith("M"):
        multiplier = 1_000_000.0
        text = text[:-1]
    elif text.endswith("K"):
        multiplier = 1_000.0
        text = text[:-1]
    text = text.replace(",", "").replace("+", "")
    try:
        return float(text) * multiplier
    except ValueError:
        return None


def has_value(value: object) -> bool:
    return bool(str(value or "").strip()) and str(value).strip().upper() != "N/A"


def set_if_missing(row: dict[str, str], key: str, value: object) -> None:
    if has_value(row.get(key)) or value is None:
        return
    text = str(value).strip()
    if text and text.upper() != "N/A":
        row[key] = text


def request_json(url: str) -> dict:
    request = Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urlopen(request, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))
    except (ssl.SSLCertVerificationError, URLError) as exc:
        reason = getattr(exc, "reason", exc)
        if not isinstance(reason, ssl.SSLCertVerificationError):
            raise
        context = ssl._create_unverified_context()
        with urlopen(request, timeout=30, context=context) as response:
            return json.loads(response.read().decode("utf-8"))


def raw(value: object) -> object:
    if isinstance(value, dict):
        return value.get("raw", value.get("fmt", ""))
    return value


def fmt(value: object) -> str:
    value = raw(value)
    if value is None or value == "":
        return ""
    if isinstance(value, float):
        return f"{value:.2f}"
    return str(value)


def fmt_pct(value: object) -> str:
    number = raw(value)
    if number is None or number == "":
        return ""
    try:
        return f"{float(number) * 100:.1f}%"
    except (TypeError, ValueError):
        return str(number)


def fmt_money(value: object) -> str:
    number = raw(value)
    if number is None or number == "":
        return ""
    try:
        number = float(number)
    except (TypeError, ValueError):
        return str(number)
    if abs(number) >= 1_000_000_000:
        return f"{number / 1_000_000_000:.2f}B"
    if abs(number) >= 1_000_000:
        return f"{number / 1_000_000:.2f}M"
    return f"{number:.2f}"


def get_nested(data: dict, *path: str) -> object:
    current: object = data
    for key in path:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current


def quote_summary(symbol: str) -> dict:
    modules = ",".join(
        [
            "price",
            "summaryDetail",
            "defaultKeyStatistics",
            "financialData",
            "recommendationTrend",
            "earningsTrend",
            "assetProfile",
        ]
    )
    url = f"https://query2.finance.yahoo.com/v10/finance/quoteSummary/{quote(symbol)}?{urlencode({'modules': modules})}"
    try:
        payload = request_json(url)
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError):
        return {}
    results = get_nested(payload, "quoteSummary", "result")
    if isinstance(results, list) and results:
        return results[0]
    return {}


def chart(symbol: str) -> dict:
    params = urlencode({"range": "1y", "interval": "1d", "includePrePost": "false"})
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{quote(symbol)}?{params}"
    try:
        payload = request_json(url)
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError):
        return {}
    results = get_nested(payload, "chart", "result")
    if isinstance(results, list) and results:
        return results[0]
    return {}


def news(symbol: str) -> list[str]:
    params = urlencode({"q": symbol, "quotesCount": 0, "newsCount": 3})
    url = f"https://query1.finance.yahoo.com/v1/finance/search?{params}"
    try:
        payload = request_json(url)
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError):
        return []
    items = payload.get("news", [])
    return [str(item.get("title", "")).strip() for item in items if item.get("title")]


def average(values: list[float]) -> float | None:
    clean = [value for value in values if value is not None]
    if not clean:
        return None
    return sum(clean) / len(clean)


def calculate_rsi(closes: list[float], period: int = 14) -> float | None:
    if len(closes) <= period:
        return None
    gains: list[float] = []
    losses: list[float] = []
    for idx in range(1, len(closes)):
        change = closes[idx] - closes[idx - 1]
        gains.append(max(change, 0))
        losses.append(abs(min(change, 0)))
    avg_gain = average(gains[-period:])
    avg_loss = average(losses[-period:])
    if avg_gain is None or avg_loss is None:
        return None
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


def calculate_atr_pct(highs: list[float], lows: list[float], closes: list[float], period: int = 14) -> float | None:
    if len(closes) <= period or len(highs) != len(lows) or len(lows) != len(closes):
        return None
    true_ranges: list[float] = []
    for idx in range(1, len(closes)):
        true_ranges.append(max(highs[idx] - lows[idx], abs(highs[idx] - closes[idx - 1]), abs(lows[idx] - closes[idx - 1])))
    atr = average(true_ranges[-period:])
    if atr is None or closes[-1] == 0:
        return None
    return atr / closes[-1] * 100


def classify_catalyst(titles: list[str], row: dict[str, str]) -> tuple[str, str, str]:
    text = " | ".join(titles).lower()
    if not text:
        return "unclear_news_only", "No recent headline found from Yahoo search.", "1"
    checks = [
        ("merger_acquisition", ["acquire", "acquisition", "merger", "takeover", "buyout", "deal"], "5"),
        ("earnings", ["earnings", "results", "eps", "quarter", "q1", "q2", "q3", "q4"], "4"),
        ("analyst_upgrade", ["upgrade", "raises price target", "price target", "initiates", "buy rating"], "3"),
        ("guidance", ["guidance", "forecast", "outlook", "raises"], "4"),
        ("product_or_contract", ["contract", "partnership", "launch", "approval", "order"], "3"),
    ]
    for catalyst, needles, score in checks:
        if any(needle in text for needle in needles):
            return catalyst, " | ".join(titles[:3]), score
    return "sector_move", " | ".join(titles[:3]), "2"


def recommendation_counts(summary: dict) -> tuple[str, str, str, str, str]:
    trend = summary.get("recommendationTrend", {}).get("trend", [])
    if not trend:
        return "", "", "", "", ""
    current = trend[0]
    strong_buy = int(raw(current.get("strongBuy")) or 0)
    buy = int(raw(current.get("buy")) or 0)
    hold = int(raw(current.get("hold")) or 0)
    sell = int(raw(current.get("sell")) or 0)
    strong_sell = int(raw(current.get("strongSell")) or 0)
    analyst_count = strong_buy + buy + hold + sell + strong_sell
    rating = "N/A"
    if analyst_count:
        weighted = (strong_buy * 1 + buy * 2 + hold * 3 + sell * 4 + strong_sell * 5) / analyst_count
        if weighted <= 1.8:
            rating = "Strong Buy"
        elif weighted <= 2.5:
            rating = "Buy"
        elif weighted <= 3.4:
            rating = "Hold"
        elif weighted <= 4.2:
            rating = "Sell"
        else:
            rating = "Strong Sell"
    return rating, str(analyst_count), str(strong_buy + buy), str(hold), str(sell + strong_sell)


def estimate_fields(summary: dict) -> dict[str, str]:
    earnings_trend = summary.get("earningsTrend", {}).get("trend", [])
    next_year = next((item for item in earnings_trend if item.get("period") == "+1y"), {})
    current_year = next((item for item in earnings_trend if item.get("period") == "0y"), {})
    eps_est = get_nested(next_year, "earningsEstimate", "avg")
    rev_est = get_nested(next_year, "revenueEstimate", "avg")
    rev_growth = get_nested(next_year, "revenueEstimate", "growth")
    eps_growth = next_year.get("growth")
    current_eps = get_nested(current_year, "earningsEstimate", "avg")
    return {
        "Next FY Revenue Estimate": fmt_money(rev_est),
        "Next FY Revenue Growth Estimate": fmt_pct(rev_growth),
        "Next FY EPS Estimate": fmt(eps_est),
        "Next FY EPS Growth Estimate": fmt_pct(eps_growth),
        "Estimate Revision Trend": "Next FY EPS estimate vs current FY available" if eps_est and current_eps else "Limited estimate trend data",
    }


def df_value(frame: object, period: str, column: str) -> object:
    try:
        if frame is None or getattr(frame, "empty", True):
            return None
        if period not in frame.index or column not in frame.columns:
            return None
        value = frame.loc[period, column]
        if str(value) == "nan":
            return None
        return value
    except Exception:
        return None


def enrich_from_yfinance(row: dict[str, str]) -> dict[str, str]:
    symbol = str(row.get("Symbol", "")).strip().upper()
    if not symbol:
        return row
    try:
        import yfinance as yf
        from curl_cffi import requests
    except Exception:
        return row

    out = dict(row)
    try:
        session = requests.Session(impersonate="chrome", verify=False)
        ticker = yf.Ticker(symbol, session=session)
        info = ticker.info or {}
    except Exception:
        return row

    price = parse_number(out.get("Price")) or info.get("currentPrice") or info.get("regularMarketPrice")
    prev_close = info.get("regularMarketPreviousClose") or info.get("previousClose")
    volume = parse_number(out.get("Volume")) or info.get("regularMarketVolume") or info.get("volume")
    avg_volume = info.get("averageVolume") or info.get("averageDailyVolume3Month")

    set_if_missing(out, "Company", info.get("longName") or info.get("shortName"))
    set_if_missing(out, "Theme", " / ".join(part for part in [info.get("sector"), info.get("industry")] if part))
    set_if_missing(out, "Price", fmt(price))
    if price and prev_close:
        set_if_missing(out, "Change($)", f"{float(price) - float(prev_close):.2f}")
        if float(prev_close) != 0:
            set_if_missing(out, "Change(%)", f"{((float(price) / float(prev_close)) - 1) * 100:.2f}%")
    set_if_missing(out, "Volume", fmt(volume))
    if price and volume:
        set_if_missing(out, "Dollar Volume", fmt_money(float(price) * float(volume)))
    if volume and avg_volume:
        set_if_missing(out, "RVOL 20D", f"{float(volume) / float(avg_volume):.2f}")

    for key, info_key, formatter in [
        ("Market Cap", "marketCap", fmt_money),
        ("Enterprise Value", "enterpriseValue", fmt_money),
        ("PS Ratio", "priceToSalesTrailing12Months", fmt),
        ("Forward PE", "forwardPE", fmt),
        ("Rev Growth YoY", "revenueGrowth", fmt_pct),
        ("EPS Growth YoY", "earningsGrowth", fmt_pct),
        ("Gross Margin", "grossMargins", fmt_pct),
        ("Operating Margin", "operatingMargins", fmt_pct),
        ("Float Shares", "floatShares", fmt_money),
        ("Short % Float", "shortPercentOfFloat", fmt_pct),
        ("50-Day MA", "fiftyDayAverage", fmt),
        ("200-Day MA", "twoHundredDayAverage", fmt),
    ]:
        set_if_missing(out, key, formatter(info.get(info_key)))
    set_if_missing(out, "PEG Ratio", fmt(info.get("trailingPegRatio") or info.get("pegRatio")))
    if info.get("freeCashflow") and info.get("totalRevenue"):
        set_if_missing(out, "FCF Margin", f"{(float(info['freeCashflow']) / float(info['totalRevenue'])) * 100:.1f}%")
    if price and info.get("fiftyDayAverage"):
        set_if_missing(out, "Price vs 50D MA %", f"{((float(price) / float(info['fiftyDayAverage'])) - 1) * 100:.1f}")
    if price and info.get("twoHundredDayAverage"):
        set_if_missing(out, "Price vs 200D MA %", f"{((float(price) / float(info['twoHundredDayAverage'])) - 1) * 100:.1f}")
    if price and info.get("fiftyTwoWeekHigh"):
        set_if_missing(out, "Dist 52W High %", f"{((float(price) / float(info['fiftyTwoWeekHigh'])) - 1) * 100:.1f}")

    try:
        targets = ticker.analyst_price_targets or {}
    except Exception:
        targets = {}
    set_if_missing(out, "Target Low", fmt(targets.get("low") or info.get("targetLowPrice")))
    set_if_missing(out, "Target Avg", fmt(targets.get("mean") or info.get("targetMeanPrice")))
    set_if_missing(out, "Target High", fmt(targets.get("high") or info.get("targetHighPrice")))
    target_avg = parse_number(out.get("Target Avg"))
    if price and target_avg:
        set_if_missing(out, "Implied Upside %", f"{((target_avg / float(price)) - 1) * 100:.1f}%")

    try:
        recs = ticker.recommendations_summary
        if recs is not None and not recs.empty:
            current = recs.iloc[0]
            strong_buy = int(current.get("strongBuy", 0) or 0)
            buy = int(current.get("buy", 0) or 0)
            hold = int(current.get("hold", 0) or 0)
            sell = int(current.get("sell", 0) or 0)
            strong_sell = int(current.get("strongSell", 0) or 0)
            set_if_missing(out, "Analyst Count", str(strong_buy + buy + hold + sell + strong_sell))
            set_if_missing(out, "Buy Count", str(strong_buy + buy))
            set_if_missing(out, "Hold Count", str(hold))
            set_if_missing(out, "Sell Count", str(sell + strong_sell))
    except Exception:
        pass
    rating = info.get("averageAnalystRating") or info.get("recommendationKey")
    if str(rating).strip().lower() != "none":
        set_if_missing(out, "Analyst Rating", rating)

    try:
        revenue_estimate = ticker.revenue_estimate
        earnings_estimate = ticker.earnings_estimate
        set_if_missing(out, "Next FY Revenue Estimate", fmt_money(df_value(revenue_estimate, "+1y", "avg")))
        set_if_missing(out, "Next FY Revenue Growth Estimate", fmt_pct(df_value(revenue_estimate, "+1y", "growth")))
        set_if_missing(out, "Next FY EPS Estimate", fmt(df_value(earnings_estimate, "+1y", "avg")))
        set_if_missing(out, "Next FY EPS Growth Estimate", fmt_pct(df_value(earnings_estimate, "+1y", "growth")))
        set_if_missing(out, "Estimate Revision Trend", "Next FY estimates available from yfinance")
    except Exception:
        pass

    try:
        hist = ticker.history(period="1y", interval="1d", auto_adjust=False)
        if hist is not None and not hist.empty:
            closes = [float(value) for value in hist["Close"].dropna().tolist()]
            highs = [float(value) for value in hist["High"].dropna().tolist()]
            lows = [float(value) for value in hist["Low"].dropna().tolist()]
            volumes = [float(value) for value in hist["Volume"].dropna().tolist()]
            rsi = calculate_rsi(closes)
            atr = calculate_atr_pct(highs, lows, closes)
            set_if_missing(out, "RSI 14", f"{rsi:.1f}" if rsi else "")
            set_if_missing(out, "ATR 14 %", f"{atr:.1f}" if atr else "")
            if not has_value(out.get("RVOL 20D")) and volumes and volume:
                avg20 = average(volumes[-21:-1]) or average(volumes[-20:])
                if avg20:
                    set_if_missing(out, "RVOL 20D", f"{float(volume) / avg20:.2f}")
    except Exception:
        pass

    titles = news(symbol)
    catalyst_type, catalyst_summary, catalyst_score = classify_catalyst(titles, out)
    set_if_missing(out, "Key News/Highlights", " | ".join(titles))
    set_if_missing(out, "Catalyst Type", catalyst_type)
    set_if_missing(out, "Catalyst Summary", catalyst_summary)
    set_if_missing(out, "Catalyst Score", catalyst_score)
    set_if_missing(out, "Recent Offering", "Unknown")
    set_if_missing(out, "Dilution Risk", "Unknown")
    float_shares = parse_number(out.get("Float Shares"))
    set_if_missing(out, "Low Float", "True" if float_shares and float_shares < 25_000_000 else "False")
    return out


def enrich_from_yahoo(row: dict[str, str]) -> dict[str, str]:
    symbol = str(row.get("Symbol", "")).strip().upper()
    if not symbol:
        return row
    out = enrich_from_yfinance(dict(row))
    summary = quote_summary(symbol)
    prices = chart(symbol)
    titles = news(symbol)

    price = parse_number(out.get("Price"))
    if not price:
        price = raw(get_nested(summary, "price", "regularMarketPrice"))
    prev_close = raw(get_nested(summary, "summaryDetail", "previousClose"))
    volume = parse_number(out.get("Volume")) or raw(get_nested(summary, "price", "regularMarketVolume"))
    avg_volume = raw(get_nested(summary, "summaryDetail", "averageVolume"))
    market_cap = raw(get_nested(summary, "price", "marketCap"))
    enterprise_value = raw(get_nested(summary, "defaultKeyStatistics", "enterpriseValue"))

    out["Company"] = out.get("Company") or fmt(get_nested(summary, "price", "longName")) or fmt(get_nested(summary, "price", "shortName"))
    out["Theme"] = out.get("Theme") or " / ".join(part for part in [fmt(get_nested(summary, "assetProfile", "sector")), fmt(get_nested(summary, "assetProfile", "industry"))] if part)
    out["Price"] = out.get("Price") or fmt(price)
    if not out.get("Change($)") and price and prev_close:
        out["Change($)"] = f"{float(price) - float(prev_close):.2f}"
    if not out.get("Change(%)") and price and prev_close and float(prev_close) != 0:
        out["Change(%)"] = f"{((float(price) / float(prev_close)) - 1) * 100:.2f}%"
    out["Volume"] = out.get("Volume") or fmt(volume)
    if price and volume:
        out["Dollar Volume"] = out.get("Dollar Volume") or fmt_money(float(price) * float(volume))
    out["Avg Volume 20D"] = out.get("Avg Volume 20D") or fmt(avg_volume)
    if volume and avg_volume:
        out["RVOL 20D"] = out.get("RVOL 20D") or f"{float(volume) / float(avg_volume):.2f}"
    out["Market Cap"] = out.get("Market Cap") or fmt_money(market_cap)
    out["Enterprise Value"] = out.get("Enterprise Value") or fmt_money(enterprise_value)
    out["PS Ratio"] = out.get("PS Ratio") or fmt(get_nested(summary, "summaryDetail", "priceToSalesTrailing12Months"))
    out["Forward PE"] = out.get("Forward PE") or fmt(get_nested(summary, "summaryDetail", "forwardPE"))
    out["PEG Ratio"] = out.get("PEG Ratio") or fmt(get_nested(summary, "defaultKeyStatistics", "pegRatio"))
    out["Rev Growth YoY"] = out.get("Rev Growth YoY") or fmt_pct(get_nested(summary, "financialData", "revenueGrowth"))
    out["EPS Growth YoY"] = out.get("EPS Growth YoY") or fmt_pct(get_nested(summary, "defaultKeyStatistics", "earningsQuarterlyGrowth"))
    out["Gross Margin"] = out.get("Gross Margin") or fmt_pct(get_nested(summary, "financialData", "grossMargins"))
    out["Operating Margin"] = out.get("Operating Margin") or fmt_pct(get_nested(summary, "financialData", "operatingMargins"))
    free_cash_flow = raw(get_nested(summary, "financialData", "freeCashflow"))
    total_revenue = raw(get_nested(summary, "financialData", "totalRevenue"))
    if not out.get("FCF Margin") and free_cash_flow and total_revenue:
        out["FCF Margin"] = f"{(float(free_cash_flow) / float(total_revenue)) * 100:.1f}%"
    out["Float Shares"] = out.get("Float Shares") or fmt_money(get_nested(summary, "defaultKeyStatistics", "floatShares"))
    out["Short % Float"] = out.get("Short % Float") or fmt_pct(get_nested(summary, "defaultKeyStatistics", "shortPercentOfFloat"))

    target_low = raw(get_nested(summary, "financialData", "targetLowPrice"))
    target_mean = raw(get_nested(summary, "financialData", "targetMeanPrice"))
    target_high = raw(get_nested(summary, "financialData", "targetHighPrice"))
    out["Target Low"] = out.get("Target Low") or fmt(target_low)
    out["Target Avg"] = out.get("Target Avg") or fmt(target_mean)
    out["Target High"] = out.get("Target High") or fmt(target_high)
    if price and target_mean:
        out["Implied Upside %"] = out.get("Implied Upside %") or f"{((float(target_mean) / float(price)) - 1) * 100:.1f}%"
    rating, analyst_count, buy_count, hold_count, sell_count = recommendation_counts(summary)
    out["Analyst Rating"] = out.get("Analyst Rating") or rating
    out["Analyst Count"] = out.get("Analyst Count") or analyst_count
    out["Buy Count"] = out.get("Buy Count") or buy_count
    out["Hold Count"] = out.get("Hold Count") or hold_count
    out["Sell Count"] = out.get("Sell Count") or sell_count
    out.update({key: out.get(key) or value for key, value in estimate_fields(summary).items()})

    quote_data = prices.get("indicators", {}).get("quote", [{}])[0]
    closes = [float(value) for value in quote_data.get("close", []) if value is not None]
    highs = [float(value) for value in quote_data.get("high", []) if value is not None]
    lows = [float(value) for value in quote_data.get("low", []) if value is not None]
    volumes = [float(value) for value in quote_data.get("volume", []) if value is not None]
    if closes:
        latest = price or closes[-1]
        ma50 = average(closes[-50:])
        ma200 = average(closes[-200:])
        high_52w = max(highs or closes)
        out["50-Day MA"] = out.get("50-Day MA") or (f"{ma50:.2f}" if ma50 else "")
        out["200-Day MA"] = out.get("200-Day MA") or (f"{ma200:.2f}" if ma200 else "")
        if ma50:
            out["Price vs 50D MA %"] = out.get("Price vs 50D MA %") or f"{((float(latest) / ma50) - 1) * 100:.1f}"
        if ma200:
            out["Price vs 200D MA %"] = out.get("Price vs 200D MA %") or f"{((float(latest) / ma200) - 1) * 100:.1f}"
        out["Dist 52W High %"] = out.get("Dist 52W High %") or f"{((float(latest) / high_52w) - 1) * 100:.1f}"
        rsi = calculate_rsi(closes)
        atr = calculate_atr_pct(highs, lows, closes)
        out["RSI 14"] = out.get("RSI 14") or (f"{rsi:.1f}" if rsi else "")
        out["ATR 14 %"] = out.get("ATR 14 %") or (f"{atr:.1f}" if atr else "")
        if not out.get("RVOL 20D") and volumes:
            avg20 = average(volumes[-21:-1]) or average(volumes[-20:])
            if avg20 and volume:
                out["RVOL 20D"] = f"{float(volume) / avg20:.2f}"

    catalyst_type, catalyst_summary, catalyst_score = classify_catalyst(titles, out)
    out["Key News/Highlights"] = out.get("Key News/Highlights") or " | ".join(titles)
    out["Catalyst Type"] = out.get("Catalyst Type") or catalyst_type
    out["Catalyst Summary"] = out.get("Catalyst Summary") or catalyst_summary
    out["Catalyst Score"] = out.get("Catalyst Score") or catalyst_score
    out["Recent Offering"] = out.get("Recent Offering") or "Unknown"
    out["Dilution Risk"] = out.get("Dilution Risk") or "Unknown"
    float_shares = parse_number(out.get("Float Shares"))
    out["Low Float"] = out.get("Low Float") or ("True" if float_shares and float_shares < 25_000_000 else "False")
    return out


def score_between(value: float | None, low: float, high: float, invert: bool = False) -> int:
    if value is None:
        return 45
    if high == low:
        return 50
    score = max(0.0, min(100.0, (value - low) / (high - low) * 100.0))
    if invert:
        score = 100.0 - score
    return int(round(score))


def first_present(row: dict[str, str], *names: str) -> str:
    for name in names:
        value = row.get(name, "")
        if has_value(value):
            return value
    return ""


def catalyst_confidence(row: dict[str, str]) -> str:
    score = parse_number(row.get("Catalyst Score"))
    if score is None:
        return "Low"
    if score >= 4:
        return "High"
    if score >= 3:
        return "Medium"
    return "Low"


def classify_recommendation(row: dict[str, str]) -> tuple[str, str, str]:
    final_score = parse_number(row.get("Final Score"))
    risk = parse_number(row.get("Risk Score"))
    catalyst = parse_number(row.get("Catalyst Score"))
    rvol = parse_number(row.get("RVOL 20D"))
    data_notes = row.get("Data Quality Notes", "")

    if final_score is None:
        return "Needs confirmation", "2", "Complete missing fundamentals and analyst estimates."
    if risk is not None and risk >= 70:
        return "Avoid for now", "2", "Review risk drivers before adding to watchlist."
    if final_score >= 70 and catalyst is not None and catalyst >= 4:
        return "High-priority research", "4", "Read earnings/news source and verify forward estimates."
    if final_score >= 58 and (rvol or 0) >= 1.5:
        return "Watchlist candidate", "3", "Confirm catalyst quality and watch next-session follow-through."
    if "missing" in data_notes.lower():
        return "Needs confirmation", "2", "Fill missing analyst or estimate fields."
    return "Speculative / news-only", "2", "Verify whether the move has a durable business catalyst."


def money(value: float | None) -> str:
    if value is None:
        return ""
    return f"{value:.2f}"


def calculate_price_levels(row: dict[str, str]) -> dict[str, str]:
    price = parse_number(row.get("Price"))
    ma50 = parse_number(row.get("50-Day MA"))
    ma200 = parse_number(row.get("200-Day MA"))
    atr_pct = parse_number(row.get("ATR 14 %"))
    target_avg = parse_number(row.get("Target Avg"))
    target_high = parse_number(row.get("Target High"))
    dist_52w_high = parse_number(row.get("Dist 52W High %"))

    if price is None:
        return {
            "Support Price": "",
            "Stop Review Price": "",
            "Hold Zone Low": "",
            "Hold Zone High": "",
            "Trim / Partial Sell Price": "",
            "Stretch Sell Price": "",
            "Price Level Basis": "Price unavailable.",
        }

    atr_move = price * ((atr_pct or 5.0) / 100.0)
    support_candidates = [value for value in [ma50, ma200, price - (2 * atr_move)] if value and value < price]
    support = max(support_candidates) if support_candidates else price - (2 * atr_move)
    stop_review = min(support, price - (2.5 * atr_move))
    hold_low = max(stop_review, support)
    hold_high = target_avg if target_avg and target_avg > price else price + (2 * atr_move)

    if target_avg and target_avg > price:
        trim_price = target_avg
        trim_basis = "target average"
    elif dist_52w_high is not None and dist_52w_high < 0:
        trim_price = price / (1 + (dist_52w_high / 100.0))
        trim_basis = "52-week high"
    else:
        trim_price = price + (3 * atr_move)
        trim_basis = "ATR extension"

    stretch = target_high if target_high and target_high > trim_price else price + (5 * atr_move)
    basis = (
        f"Support from nearest MA/ATR; hold zone from support to "
        f"{'target average' if target_avg else '2x ATR'}; trim from {trim_basis}; stretch from "
        f"{'target high' if target_high else '5x ATR'}."
    )

    return {
        "Support Price": money(support),
        "Stop Review Price": money(stop_review),
        "Hold Zone Low": money(hold_low),
        "Hold Zone High": money(hold_high),
        "Trim / Partial Sell Price": money(trim_price),
        "Stretch Sell Price": money(stretch),
        "Price Level Basis": basis,
    }


def confidence_from_score(score: float | None, missing_penalty: bool = False) -> str:
    if score is None:
        return "2"
    confidence = 2
    if score >= 65:
        confidence = 4
    elif score >= 50:
        confidence = 3
    if missing_penalty:
        confidence = max(1, confidence - 1)
    return str(confidence)


def enrich_row(row: dict[str, str], input_source: str, run_ts: str) -> dict[str, str]:
    out = enrich_from_yahoo(dict(row))
    rev_growth = parse_number(out.get("Rev Growth YoY"))
    eps_growth = parse_number(out.get("EPS Growth YoY"))
    gross_margin = parse_number(out.get("Gross Margin"))
    operating_margin = parse_number(out.get("Operating Margin"))
    fcf_margin = parse_number(out.get("FCF Margin"))
    ps_ratio = parse_number(out.get("PS Ratio"))
    peg_ratio = parse_number(out.get("PEG Ratio"))
    rvol = parse_number(out.get("RVOL 20D"))
    price_vs_50d = parse_number(out.get("Price vs 50D MA %"))
    rsi = parse_number(out.get("RSI 14"))
    short_float = parse_number(out.get("Short % Float"))

    growth_parts = [score_between(rev_growth, 0, 60), score_between(eps_growth, 0, 80)]
    quality_parts = [
        score_between(gross_margin, 20, 80),
        score_between(operating_margin, -10, 30),
        score_between(fcf_margin, -10, 30),
    ]
    valuation_parts = [score_between(ps_ratio, 0.5, 12, invert=True), score_between(peg_ratio, 0.5, 5, invert=True)]
    momentum_parts = [
        score_between(rvol, 1, 8),
        score_between(price_vs_50d, -20, 40),
        score_between(rsi, 30, 85),
    ]
    liquidity = parse_number(out.get("Liquidity Score"))
    risk = parse_number(out.get("Risk Score"))

    out["Growth Score"] = str(round(sum(growth_parts) / len(growth_parts)))
    out["Quality Score"] = str(round(sum(quality_parts) / len(quality_parts)))
    out["Valuation Score"] = out.get("Valuation Score") or str(round(sum(valuation_parts) / len(valuation_parts)))
    out["Momentum Score"] = out.get("Technical Score") or str(round(sum(momentum_parts) / len(momentum_parts)))
    out["Liquidity Score"] = out.get("Liquidity Score") or str(liquidity if liquidity is not None else 50)
    risk_parts = [
        score_between(short_float, 0, 30),
        score_between(rsi, 55, 85),
        80 if str(out.get("Low Float", "")).lower() == "true" else 20,
        80 if str(out.get("Dilution Risk", "")).lower() == "true" else 30,
    ]
    out["Risk Score"] = out.get("Risk Score") or str(round(sum(risk_parts) / len(risk_parts))) if risk is None else str(risk)
    out["Catalyst Confidence"] = catalyst_confidence(out)
    out["Input Source"] = input_source
    out["Run Timestamp"] = run_ts

    missing = []
    for field in ["Analyst Rating", "Target Avg", "Next FY Revenue Growth Estimate", "Next FY EPS Growth Estimate"]:
        if not out.get(field) or out.get(field) == "N/A":
            missing.append(field)
    if not missing:
        out["Analyst Data Quality"] = "Complete"
        out["Data Quality Notes"] = "Complete"
    elif len(missing) < 4:
        out["Analyst Data Quality"] = "Partial"
        out["Data Quality Notes"] = "Unavailable from Yahoo: " + ", ".join(missing)
    else:
        out["Analyst Data Quality"] = "Unavailable"
        out["Data Quality Notes"] = "Unavailable from Yahoo: " + ", ".join(missing)

    if not out.get("Final Score"):
        score = (
            parse_number(out["Growth Score"]) * 0.22
            + parse_number(out["Quality Score"]) * 0.18
            + parse_number(out["Momentum Score"]) * 0.22
            + parse_number(out["Valuation Score"]) * 0.16
            + parse_number(out["Liquidity Score"]) * 0.12
            + (100 - parse_number(out["Risk Score"])) * 0.10
        )
        out["Final Score"] = f"{score:.1f}"

    rec, confidence, next_step = classify_recommendation(out)
    out["Recommendation"] = rec
    out["Confidence 1-5"] = confidence
    out["Next Research Step"] = next_step
    out["PM Verdict"] = rec
    out["PM Confidence"] = confidence
    out["PM Reason"] = next_step

    out.update(calculate_price_levels(out))

    out["Growth Analyst Note"] = make_growth_note(out)
    out["Growth Analyst Confidence"] = confidence_from_score(parse_number(out.get("Growth Score")), "Missing:" in out["Data Quality Notes"])
    out["Growth Analyst Reason"] = make_growth_reason(out)
    out["Momentum Analyst Note"] = make_momentum_note(out)
    out["Momentum Analyst Confidence"] = confidence_from_score(parse_number(out.get("Momentum Score")))
    out["Momentum Analyst Reason"] = make_momentum_reason(out)
    out["Valuation Analyst Note"] = make_valuation_note(out)
    out["Valuation Analyst Confidence"] = confidence_from_score(parse_number(out.get("Valuation Score")), not out.get("Target Avg"))
    out["Valuation Analyst Reason"] = make_valuation_reason(out)
    out["Risk Analyst Note"] = make_risk_note(out, short_float)
    risk_score = parse_number(out.get("Risk Score"))
    out["Risk Analyst Confidence"] = confidence_from_score(100 - risk_score if risk_score is not None else None)
    out["Risk Analyst Reason"] = make_risk_reason(out)
    for column in OUTPUT_COLUMNS:
        if not str(out.get(column, "")).strip():
            out[column] = "N/A"
    return out


def make_growth_note(row: dict[str, str]) -> str:
    rev = first_present(row, "Rev Growth YoY")
    eps = first_present(row, "EPS Growth YoY")
    if rev or eps:
        return f"Revenue growth {rev or 'N/A'}; EPS growth {eps or 'N/A'}."
    return "Growth fields unavailable; confirm forward estimates."


def make_growth_reason(row: dict[str, str]) -> str:
    return f"Growth score {row.get('Growth Score', 'N/A')} based on reported revenue/EPS growth and available margins."


def make_momentum_note(row: dict[str, str]) -> str:
    change = first_present(row, "Change(%)")
    rvol = first_present(row, "RVOL 20D")
    rsi = first_present(row, "RSI 14")
    return f"Move {change or 'N/A'} with RVOL {rvol or 'N/A'} and RSI {rsi or 'N/A'}."


def make_momentum_reason(row: dict[str, str]) -> str:
    return f"Momentum score {row.get('Momentum Score', 'N/A')} reflects RVOL, moving-average position, and RSI."


def make_valuation_note(row: dict[str, str]) -> str:
    ps = first_present(row, "PS Ratio")
    peg = first_present(row, "PEG Ratio")
    return f"P/S {ps or 'N/A'} and PEG {peg or 'N/A'}; compare against growth and margins."


def make_valuation_reason(row: dict[str, str]) -> str:
    if row.get("Target Avg"):
        return f"Valuation score {row.get('Valuation Score', 'N/A')} plus analyst target context."
    return f"Valuation score {row.get('Valuation Score', 'N/A')}; analyst target data unavailable."


def make_risk_note(row: dict[str, str], short_float: float | None) -> str:
    flags = []
    if str(row.get("Low Float", "")).lower() == "true":
        flags.append("low float")
    if str(row.get("Dilution Risk", "")).lower() == "true":
        flags.append("dilution risk")
    if short_float is not None and short_float >= 15:
        flags.append("high short interest")
    rsi = parse_number(row.get("RSI 14"))
    if rsi is not None and rsi >= 75:
        flags.append("overbought RSI")
    if flags:
        return "Risk flags: " + ", ".join(flags) + "."
    return "No major row-level risk flag detected; still verify news and liquidity."


def make_risk_reason(row: dict[str, str]) -> str:
    return f"Risk score {row.get('Risk Score', 'N/A')} uses available short interest, float, dilution, RSI, and volatility flags."


def run(input_csv: Path, output_csv: Path, limit: int) -> None:
    run_ts = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    with input_csv.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))

    seen = set()
    normalized = []
    for row in rows:
        symbol = str(row.get("Symbol", "")).strip().upper()
        if not symbol or symbol in seen:
            continue
        seen.add(symbol)
        row["Symbol"] = symbol
        normalized.append(row)

    def rank_key(row: dict[str, str]) -> tuple[int, float]:
        rank = parse_number(row.get("Rank"))
        change = parse_number(row.get("Change(%)"))
        return (int(rank) if rank is not None else 9999, -(change or 0))

    selected = sorted(normalized, key=rank_key)[:limit]
    enriched = [enrich_row(row, str(input_csv), run_ts) for row in selected]

    output_csv.parent.mkdir(parents=True, exist_ok=True)
    with output_csv.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=OUTPUT_COLUMNS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(enriched)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run stock discovery workflow over a gainers CSV.")
    parser.add_argument("--input", required=True, type=Path, help="Input gainers CSV path.")
    parser.add_argument("--output", required=True, type=Path, help="Output CSV path.")
    parser.add_argument("--limit", type=int, default=25, help="Maximum number of tickers to process.")
    args = parser.parse_args()
    run(args.input, args.output, args.limit)


if __name__ == "__main__":
    main()
