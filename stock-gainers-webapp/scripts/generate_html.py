from __future__ import annotations

import datetime as dt
import glob
import html
import os

import pandas as pd


BUCKET_COLORS = {
    "Watchlist candidate": ("#16a34a", "Watchlist"),
    "Needs confirmation": ("#d97706", "Confirm"),
    "Speculative / news-only": ("#7c3aed", "Speculative"),
    "Avoid": ("#dc2626", "Avoid"),
}


def latest_csv() -> str:
    files = sorted(glob.glob("data/gainers_*.csv"), reverse=True)
    if not files:
        raise FileNotFoundError("No CSV found in data/")
    return files[0]


def score_bar(score: int) -> str:
    color = "#16a34a" if score >= 70 else ("#d97706" if score >= 45 else "#6b7280")
    return (
        f'<div class="score"><span style="width:{score}%;background:{color}"></span></div>'
        f'<small>{score}</small>'
    )


def cell(value: object) -> str:
    return html.escape(str(value if pd.notna(value) else "N/A"))


def build_row(row: pd.Series) -> str:
    color, label = BUCKET_COLORS.get(str(row.get("Bucket", "")), ("#6b7280", "Review"))
    score = int(row.get("Score", 0) or 0)
    change = float(row.get("Change_%", 0) or 0)
    change_class = "gain" if change >= 0 else "loss"
    desc = cell(str(row.get("Description", ""))[:220])
    symbol = cell(row.get("Symbol", ""))
    company = cell(row.get("Company", ""))
    return f"""
    <tr>
      <td class="symbol"><strong>{symbol}</strong><small>{company}</small></td>
      <td>{cell(row.get("Sector", "N/A"))}</td>
      <td>{cell(row.get("Industry", "N/A"))}</td>
      <td>${cell(row.get("Price", "N/A"))}</td>
      <td class="{change_class}">{change:.2f}%</td>
      <td>{cell(row.get("RVOL_20D", "N/A"))}</td>
      <td>{cell(row.get("RSI_14", "N/A"))}</td>
      <td>{cell(row.get("50D_MA", "N/A"))}</td>
      <td>{cell(row.get("PS_Ratio", "N/A"))}</td>
      <td>{cell(row.get("Rev_Growth_YoY", "N/A"))}</td>
      <td>{cell(row.get("Op_Margin", "N/A"))}</td>
      <td>{cell(row.get("Analyst_Rating", "N/A"))}<small>B:{cell(row.get("Buy_Count", 0))} H:{cell(row.get("Hold_Count", 0))} S:{cell(row.get("Sell_Count", 0))}</small></td>
      <td>{cell(row.get("Target_Mean", "N/A"))}</td>
      <td>{cell(row.get("Implied_Upside_%", "N/A"))}</td>
      <td>{score_bar(score)}</td>
      <td><span class="badge" style="background:{color}">{label}</span></td>
      <td class="desc">{desc}</td>
    </tr>"""


def run() -> None:
    path = latest_csv()
    df = pd.read_csv(path)
    date_str = os.path.basename(path).replace("gainers_", "").replace(".csv", "")
    rows_html = "\n".join(build_row(row) for _, row in df.iterrows())
    updated = dt.datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

    page = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Stock Gainers Dashboard - {date_str}</title>
  <style>
    * {{ box-sizing: border-box; }}
    body {{ margin: 0; font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; background: #f8fafc; color: #111827; }}
    header {{ padding: 24px 28px 14px; border-bottom: 1px solid #e5e7eb; background: #ffffff; }}
    h1 {{ margin: 0 0 6px; font-size: 24px; line-height: 1.2; }}
    .meta {{ margin: 0; color: #64748b; font-size: 14px; }}
    .legend {{ display: flex; gap: 10px; flex-wrap: wrap; margin-top: 14px; }}
    .legend span {{ border: 1px solid #e5e7eb; background: #f9fafb; border-radius: 6px; padding: 5px 8px; font-size: 12px; }}
    main {{ padding: 18px 24px 32px; }}
    .wrap {{ overflow-x: auto; border: 1px solid #e5e7eb; border-radius: 8px; background: #fff; }}
    table {{ width: 100%; border-collapse: collapse; min-width: 1500px; }}
    th {{ position: sticky; top: 0; background: #1f2937; color: #fff; text-align: left; padding: 10px 12px; font-size: 12px; white-space: nowrap; cursor: pointer; }}
    td {{ padding: 10px 12px; border-bottom: 1px solid #f1f5f9; font-size: 13px; vertical-align: top; }}
    tr:hover td {{ background: #f8fafc; }}
    small {{ display: block; color: #64748b; margin-top: 2px; }}
    .symbol strong {{ display: block; font-size: 14px; }}
    .gain {{ color: #16a34a; font-weight: 700; }}
    .loss {{ color: #dc2626; font-weight: 700; }}
    .badge {{ color: #fff; border-radius: 999px; padding: 4px 8px; white-space: nowrap; font-size: 12px; font-weight: 700; }}
    .score {{ width: 82px; height: 8px; background: #e5e7eb; border-radius: 999px; overflow: hidden; }}
    .score span {{ display: block; height: 8px; border-radius: 999px; }}
    .desc {{ color: #475569; max-width: 260px; line-height: 1.35; }}
  </style>
</head>
<body>
  <header>
    <h1>Stock Gainers Dashboard - {date_str}</h1>
    <p class="meta">Stocks with at least {len(df)} generated rows. Updated: {updated}. Data from Yahoo Finance/yfinance.</p>
    <div class="legend">
      <span>Watchlist: score >= 70</span>
      <span>Needs confirmation: score 45-69</span>
      <span>Speculative: score below 45</span>
    </div>
  </header>
  <main>
    <div class="wrap">
      <table id="tbl">
        <thead>
          <tr>
            <th onclick="sortTable(0)">Symbol</th>
            <th onclick="sortTable(1)">Sector</th>
            <th onclick="sortTable(2)">Industry</th>
            <th onclick="sortTable(3)">Price</th>
            <th onclick="sortTable(4)">Change %</th>
            <th onclick="sortTable(5)">RVOL</th>
            <th onclick="sortTable(6)">RSI</th>
            <th onclick="sortTable(7)">50D MA</th>
            <th onclick="sortTable(8)">P/S</th>
            <th onclick="sortTable(9)">Rev Growth</th>
            <th onclick="sortTable(10)">Op Margin</th>
            <th onclick="sortTable(11)">Analyst</th>
            <th onclick="sortTable(12)">Target</th>
            <th onclick="sortTable(13)">Upside</th>
            <th onclick="sortTable(14)">Score</th>
            <th onclick="sortTable(15)">Bucket</th>
            <th>Description</th>
          </tr>
        </thead>
        <tbody>{rows_html}</tbody>
      </table>
    </div>
  </main>
  <script>
    const directions = {{}};
    function sortTable(col) {{
      const table = document.getElementById("tbl");
      const tbody = table.tBodies[0];
      const rows = Array.from(tbody.rows);
      directions[col] = !directions[col];
      rows.sort((a, b) => {{
        const x = a.cells[col].innerText.trim();
        const y = b.cells[col].innerText.trim();
        return directions[col]
          ? x.localeCompare(y, undefined, {{ numeric: true }})
          : y.localeCompare(x, undefined, {{ numeric: true }});
      }});
      rows.forEach(row => tbody.appendChild(row));
    }}
  </script>
</body>
</html>"""

    os.makedirs("docs", exist_ok=True)
    with open("docs/index.html", "w", encoding="utf-8") as handle:
        handle.write(page)
    print(f"Generated docs/index.html with {len(df)} rows")


if __name__ == "__main__":
    run()

