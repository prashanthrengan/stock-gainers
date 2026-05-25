---
name: stock-research-committee
description: Use to run a structured multi-role stock review over enriched ticker rows, with roles for orchestrator, growth analyst, momentum analyst, valuation analyst, risk analyst, and portfolio manager.
---

# Stock Research Committee

Produce structured role-based research notes for each ticker. Keep notes concise and grounded in the row data.

## Roles

Use this sequence:

1. `Orchestrator`: summarizes the setup and missing data.
2. `Growth Analyst`: reviews revenue growth, EPS growth, margin profile, and forward estimates.
3. `Momentum Analyst`: reviews gain, RVOL, moving averages, RSI, 52-week distance, and liquidity.
4. `Valuation Analyst`: reviews P/S, PEG, forward PE, and growth-adjusted valuation.
5. `Risk Analyst`: reviews short interest, low float, dilution, volatility, weak margins, excessive RSI, and data gaps.
6. `Portfolio Manager`: assigns final research label and next action.

## Final Labels

Use one of:
- `High-priority research`
- `Watchlist candidate`
- `Needs confirmation`
- `Speculative / news-only`
- `Avoid for now`

## Output Fields

Add:
- `Growth Analyst Note`
- `Growth Analyst Confidence`
- `Growth Analyst Reason`
- `Momentum Analyst Note`
- `Momentum Analyst Confidence`
- `Momentum Analyst Reason`
- `Valuation Analyst Note`
- `Valuation Analyst Confidence`
- `Valuation Analyst Reason`
- `Risk Analyst Note`
- `Risk Analyst Confidence`
- `Risk Analyst Reason`
- `PM Verdict`
- `PM Confidence`
- `PM Reason`
- `Recommendation`
- `Confidence 1-5`
- `Next Research Step`

## Price Level Fields

Use price levels as research bands, not trading instructions:
- `Support Price`: nearest practical downside/reference level.
- `Stop Review Price`: price where the thesis should be rechecked.
- `Hold Zone Low`: lower bound where holding/research remains reasonable.
- `Hold Zone High`: upper bound where momentum may still be intact.
- `Trim / Partial Sell Price`: level where valuation or overextension suggests reviewing profit-taking.
- `Stretch Sell Price`: optimistic upside level, usually analyst target high or technical extension.
- `Price Level Basis`: short explanation of how levels were estimated.

## Guardrails

- Do not claim certainty when source fields are missing.
- Avoid direct trading instructions.
- Prefer "research" language over "buy/sell" language.
