---
name: stock-csv-publisher
description: Use to publish enriched stock discovery rows as a clean CSV file with stable column ordering, data quality fields, recommendation fields, and optional delivery metadata.
---

# Stock CSV Publisher

Create the final stock discovery CSV.

## Column Order

Use this order where fields exist:

1. Universe fields: `Rank`, `Symbol`, `Company`, `Theme`
2. Price action: `Price`, `Change($)`, `Change(%)`, `Volume`, `Dollar Volume`, `RVOL 20D`
3. Catalyst: `Catalyst Type`, `Catalyst Summary`, `Catalyst Score`, `Catalyst Confidence`
4. Fundamentals: `Market Cap`, `Enterprise Value`, `PS Ratio`, `Forward PE`, `PEG Ratio`
5. Growth/quality: `Rev Growth YoY`, `EPS Growth YoY`, `Gross Margin`, `Operating Margin`, `FCF Margin`
6. Estimates: `Analyst Rating`, `Analyst Count`, `Target Low`, `Target Avg`, `Target High`, `Implied Upside %`, `Next FY Revenue Growth Estimate`, `Next FY EPS Growth Estimate`
7. Technicals: `50-Day MA`, `200-Day MA`, `Price vs 50D MA %`, `Price vs 200D MA %`, `Dist 52W High %`, `RSI 14`, `ATR 14 %`
8. Risk/liquidity: `Float Shares`, `Short % Float`, `Recent Offering`, `Dilution Risk`, `Low Float`
9. Scores: `Growth Score`, `Quality Score`, `Momentum Score`, `Valuation Score`, `Liquidity Score`, `Risk Score`, `Final Score`
10. Price levels: `Support Price`, `Stop Review Price`, `Hold Zone Low`, `Hold Zone High`, `Trim / Partial Sell Price`, `Stretch Sell Price`, `Price Level Basis`
11. Committee: `Growth Analyst Note`, `Growth Analyst Confidence`, `Growth Analyst Reason`, `Momentum Analyst Note`, `Momentum Analyst Confidence`, `Momentum Analyst Reason`, `Valuation Analyst Note`, `Valuation Analyst Confidence`, `Valuation Analyst Reason`, `Risk Analyst Note`, `Risk Analyst Confidence`, `Risk Analyst Reason`, `PM Verdict`, `PM Confidence`, `PM Reason`, `Recommendation`, `Confidence 1-5`, `Next Research Step`
12. Audit: `Data Quality Notes`, `Analyst Data Quality`, `Input Source`, `Run Timestamp`

## Rules

- Keep one ticker per row.
- Preserve original source fields when possible.
- Use blank cells for unavailable numeric data.
- Include timestamps and source notes.
- Save CSV with a date in the filename.
