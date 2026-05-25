# Stock Gainers Dashboard

Static GitHub Pages dashboard for daily stock-gainer discovery. It fetches Yahoo Finance day gainers, enriches them with yfinance fundamentals, technicals, analyst targets, and recommendation counts, then publishes a sortable HTML table.

## Setup

1. Upload this folder to a new GitHub repository.
2. Go to **Settings -> Pages**.
3. Set source to **Deploy from branch**.
4. Select branch `main` and folder `/docs`.
5. Go to **Actions** and enable workflows.
6. Run **Daily Stock Scan** manually once.

Your site will be available at:

```text
https://<your-username>.github.io/<repo-name>/
```

## Schedule

The workflow runs Monday-Friday at `13:35 UTC`, which is approximately `09:35 ET` during US daylight saving time.

## Files

- `scripts/fetch_gainers.py`: fetches and enriches top gainers.
- `scripts/generate_html.py`: builds `docs/index.html`.
- `.github/workflows/daily_scan.yml`: scheduled GitHub Actions job.
- `data/`: generated CSV files.
- `docs/`: GitHub Pages output.

## Notes

This is a research dashboard, not financial advice. Yahoo/yfinance data can be delayed or unavailable for some tickers.

