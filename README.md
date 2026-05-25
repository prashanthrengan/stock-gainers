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

## Schedule

The workflow runs Monday-Friday at `13:35 UTC`, approximately `09:35 ET` during US daylight saving time.

## How It Works

1. `.github/workflows/daily_scan.yml` runs on schedule or manually.
2. `scripts/fetch_gainers.py` creates a dated CSV under `data/`.
3. `scripts/generate_html.py` reads the newest CSV and replaces `docs/index.html`.
4. GitHub Pages serves `docs/index.html`.

The `data/` folder keeps dated CSV history. The webpage always shows the latest generated CSV.

## Notes

This is a research dashboard, not financial advice. Yahoo/yfinance data can be delayed or unavailable for some tickers.

