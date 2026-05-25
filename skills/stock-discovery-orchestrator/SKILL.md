---
name: stock-discovery-orchestrator
description: Use when the user wants to run or design the end-to-end stock discovery workflow: get top gainers or user-provided tickers, enrich fundamentals and analyst estimates, run structured analyst review, and publish a CSV watchlist.
---

# Stock Discovery Orchestrator

Coordinate the stock discovery workflow as a sequence of skills. Treat output as a research watchlist, not financial advice.

## Inputs

Accept either:
- A CSV of daily gainers with at least `Symbol`, `Company`, `Price`, `Change(%)`, and `Volume`.
- A user-provided ticker list.
- A request for "top gainers today"; if no source is configured, ask for a CSV or ticker list.

## Skill Sequence

1. Use `stock-gainers-ingest` to normalize input rows and keep the top 25 symbols.
2. Use `stock-financial-enricher` to add fundamentals, valuation, margins, growth, liquidity, and technical fields.
3. Use `stock-analyst-estimates` to add analyst rating and price target fields.
4. Use `stock-catalyst-classifier` to classify why the stock moved.
5. Use `stock-research-committee` to create structured role-based notes and a final research verdict.
6. Use `stock-csv-publisher` to export the final CSV.

## Output Contract

The final artifact is a CSV with one row per ticker. Include raw fields, calculated scores, each analyst/agent note, each analyst/agent confidence and reason, overall recommendation, overall confidence, price-level research bands, and research priority.

## Guardrails

- Be explicit about missing or stale data.
- Prefer source fields over model guesses.
- Mark rows `Needs confirmation` when news, analyst data, or estimates are unavailable.
- Do not produce direct buy/sell instructions; use research workflow labels such as `High-priority research`, `Watchlist`, `Needs confirmation`, or `Avoid for now`.
- Note that yfinance is an unofficial Yahoo Finance interface intended for research/personal use.
