# Stock Gainers Dashboard

Static GitHub Pages dashboard for daily stock-gainer discovery. It fetches Yahoo Finance day gainers, enriches them with yfinance fundamentals, technicals, analyst targets, and recommendation counts, then publishes a sortable HTML table.

## Setup

1. Go to **Settings -> Pages**.
2. Set source to **Deploy from branch**.
3. Select branch `main` and folder `/docs`.
4. Go to **Actions** and run **Daily Stock Scan** manually once.

Your site will be available at:

```text
https://prashanthrengan.github.io/stock-gainers/
```

Live dashboard:

[https://prashanthrengan.github.io/stock-gainers/](https://prashanthrengan.github.io/stock-gainers/)

## Schedule

The workflow runs Monday-Friday at `13:35 UTC`, approximately `09:35 ET` during US daylight saving time.

## How It Works

1. `.github/workflows/daily_scan.yml` runs on schedule or manually.
2. `scripts/fetch_gainers.py` creates a dated CSV under `data/`.
3. `scripts/generate_html.py` reads the newest CSV and replaces `docs/index.html`.
4. GitHub Pages serves `docs/index.html`.

The `data/` folder keeps dated CSV history. The webpage always shows the latest generated CSV.

## Dashboard Columns

The webpage intentionally shows a compact investor view instead of every raw CSV field.

| Column | Meaning |
| --- | --- |
| `Sector` | Broad business category, such as Technology, Healthcare, or Financial Services. |
| `Industry` | More specific business group, such as Semiconductors, Software, or Biotechnology. |
| `Price` | Latest Yahoo/yfinance price at scan time. |
| `Change %` | Today's percentage move. The scan targets stocks moving about `+10%` or more. |
| `RVOL` | Relative volume: `current volume / average volume`. A value of `3.0` means about 3x normal volume. |
| `RSI` | 14-day relative strength index. Roughly: `45-65` healthy, `65-75` strong, `75+` stretched. |
| `50D MA` | 50-day moving average price, used as a medium-term trend reference. |
| `P/S` | Price-to-sales ratio. Lower can be cheaper; very high values mean expectations are high. |
| `Rev Growth` | Year-over-year revenue growth from yfinance/Yahoo. |
| `Op Margin` | Operating margin, showing operating profitability. |
| `Analyst` | Average analyst rating from Yahoo/yfinance, when available. |
| `Target` | Average analyst price target. |
| `Upside` | Implied upside: `(Target / Price - 1) * 100`. |
| `Score` | Rule-based score from 0 to 100. |
| `Bucket` | Research label derived from score. |
| `Description` | Short business description from yfinance/Yahoo. |

## Score Formula

The score is intentionally simple and transparent:

```text
+15 if RSI is between 45 and 75
+20 if RVOL >= 2
+15 if analyst rating contains "buy"
+20 if revenue growth >= 15%
+15 if operating margin >= 10%
+15 if implied upside >= 10%
```

Bucket logic:

```text
Score >= 70  -> Watchlist candidate
Score 45-69  -> Needs confirmation
Score < 45   -> Speculative / news-only
```

## Notes

This is a research dashboard, not financial advice. Yahoo/yfinance data can be delayed or unavailable for some tickers.
