---
name: stock-gainers-ingest
description: Use to ingest a daily stock gainers CSV or user ticker list, normalize symbols and base market columns, deduplicate entries, and select the top 25 candidates for enrichment.
---

# Stock Gainers Ingest

Normalize the initial universe for the stock discovery workflow.

## Inputs

One of:
- CSV path.
- Pasted CSV/table.
- Ticker list.

## Required Fields

For CSV input, preserve these fields when present:
- `Rank`
- `Symbol`
- `Company`
- `Price`
- `Change($)`
- `Change(%)`
- `Volume`
- `Theme`
- `Key News/Highlights`

## Process

1. Parse CSV with a structured parser.
2. Trim whitespace from symbols and uppercase them.
3. Remove duplicate symbols, keeping the highest-ranked row.
4. Sort by `Rank` if present, otherwise by `Change(%)` descending.
5. Keep the first 25 rows unless the user asks for another count.

## Output

Return normalized rows with at least:
- `Rank`
- `Symbol`
- `Company`
- `Price`
- `Change %`
- `Volume`
- `Input Source`
- `Input Timestamp`

