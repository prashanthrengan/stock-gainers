---
name: stock-analyst-estimates
description: Use to add analyst ratings, analyst counts, price target low/average/high, implied upside, and forward revenue or EPS estimate fields to stock discovery rows.
---

# Stock Analyst Estimates

Add sell-side analyst and forward estimate context.

## Target Fields

Add:
- `Analyst Rating`
- `Analyst Count`
- `Buy Count`
- `Hold Count`
- `Sell Count`
- `Target Low`
- `Target Avg`
- `Target High`
- `Implied Upside %`
- `Next FY Revenue Estimate`
- `Next FY Revenue Growth Estimate`
- `Next FY EPS Estimate`
- `Next FY EPS Growth Estimate`
- `Estimate Revision Trend`

## Process

1. Pull analyst and estimate fields from configured sources.
2. Prefer explicit values from source data.
3. Calculate `Implied Upside %` as `(Target Avg / Price - 1) * 100` when both values exist.
4. Mark unavailable values as blank or `N/A`.

## Output

Return rows with analyst fields and `Analyst Data Quality` set to `Complete`, `Partial`, or `Unavailable`.

