---
name: stock-financial-enricher
description: Use to enrich stock ticker rows with fundamentals, valuation ratios, growth rates, margins, liquidity, float, short interest, and technical momentum fields, preferably from yfinance or configured market data providers.
---

# Stock Financial Enricher

Add market, valuation, growth, quality, liquidity, and technical fields to normalized ticker rows.

## Preferred Source

Use `yfinance` when available and appropriate for personal research. Respect that it is unofficial and may have missing or unstable fields.

## Target Fields

Add or preserve:
- `Market Cap`
- `Enterprise Value`
- `PS Ratio`
- `Forward PE`
- `PEG Ratio`
- `Rev Growth YoY`
- `EPS Growth YoY`
- `Gross Margin`
- `Operating Margin`
- `FCF Margin`
- `Total Cash`
- `Total Debt`
- `Float Shares`
- `Short % Float`
- `Avg Volume 20D`
- `RVOL 20D`
- `50-Day MA`
- `200-Day MA`
- `Price vs 50D MA %`
- `Price vs 200D MA %`
- `Dist 52W High %`
- `RSI 14`
- `ATR 14 %`

## Scoring

Create component scores on a 0-100 scale:
- `Growth Score`
- `Quality Score`
- `Valuation Score`
- `Momentum Score`
- `Liquidity Score`
- `Risk Score`

Prefer deterministic formulas. If a field is missing, reduce confidence rather than inventing a value.

## Output

Return enriched rows and a `Data Quality Notes` field for each ticker.

