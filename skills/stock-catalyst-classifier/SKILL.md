---
name: stock-catalyst-classifier
description: Use to classify the catalyst behind a stock's daily gain, such as earnings, analyst action, merger/acquisition, product news, sector move, low-float squeeze, or unclear/news-only movement.
---

# Stock Catalyst Classifier

Classify why the stock moved.

## Inputs

Use available fields such as:
- `Key News/Highlights`
- `Catalyst Summary`
- `Next Earnings Date`
- `Last EPS Surprise %`
- price and volume change
- analyst fields

## Catalyst Types

Use one of:
- `earnings`
- `guidance`
- `analyst_upgrade`
- `merger_acquisition`
- `product_or_contract`
- `sector_move`
- `short_squeeze`
- `low_float_momentum`
- `macro_or_policy`
- `unclear_news_only`

## Catalyst Score

Score 0-5:
- 5: verified material catalyst such as M&A, major earnings beat, or raised guidance.
- 4: strong earnings/analyst/product catalyst.
- 3: plausible catalyst but needs confirmation.
- 2: weak or generic news.
- 1: move has no clear support.
- 0: data unavailable.

## Output

Return `Catalyst Type`, `Catalyst Summary`, `Catalyst Score`, and `Catalyst Confidence`.

