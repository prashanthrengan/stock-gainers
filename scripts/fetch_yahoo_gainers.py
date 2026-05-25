#!/usr/bin/env python
"""Fetch a basic top-gainers CSV from Yahoo Finance's public screener endpoint.

This is an unofficial endpoint and should be treated as best-effort research
data. For European/Nordnet coverage, add provider-specific fetchers later.
"""

from __future__ import annotations

import argparse
import csv
import ssl
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode
from urllib.error import URLError
from urllib.request import Request, urlopen


FIELDS = [
    "Rank",
    "Symbol",
    "Company",
    "Price",
    "Change($)",
    "Change(%)",
    "Volume",
    "Dollar Volume",
    "Market Cap",
]


def fmt_number(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, (int, float)):
        return f"{value:.2f}" if isinstance(value, float) else str(value)
    return str(value)


def yahoo_raw(item: dict, field: str) -> object:
    value = item.get(field)
    if isinstance(value, dict):
        return value.get("raw", value.get("fmt", ""))
    return value


def yahoo_fmt(item: dict, field: str) -> str:
    value = item.get(field)
    if isinstance(value, dict):
        return str(value.get("fmt", value.get("raw", "")))
    if value is None:
        return ""
    return str(value)


def fetch(count: int) -> list[dict[str, str]]:
    params = urlencode({"scrIds": "day_gainers", "count": count})
    url = f"https://query1.finance.yahoo.com/v1/finance/screener/predefined/saved?{params}"
    request = Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urlopen(request, timeout=30) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (ssl.SSLCertVerificationError, URLError) as exc:
        reason = getattr(exc, "reason", exc)
        if not isinstance(reason, ssl.SSLCertVerificationError):
            raise
        # Local Windows/Python certificate stores can reject otherwise valid
        # public endpoints. Limit the unverified fallback to this read-only
        # Yahoo Finance screener request.
        context = ssl._create_unverified_context()
        with urlopen(request, timeout=30, context=context) as response:
            payload = json.loads(response.read().decode("utf-8"))

    quotes = payload["finance"]["result"][0]["quotes"]
    rows = []
    for rank, item in enumerate(quotes[:count], start=1):
        price = yahoo_raw(item, "regularMarketPrice")
        volume = yahoo_raw(item, "regularMarketVolume")
        dollar_volume = ""
        if isinstance(price, (int, float)) and isinstance(volume, (int, float)):
            dollar_volume = f"{price * volume / 1_000_000:.2f}M"
        rows.append(
            {
                "Rank": str(rank),
                "Symbol": yahoo_fmt(item, "symbol").upper(),
                "Company": yahoo_fmt(item, "shortName") or yahoo_fmt(item, "longName"),
                "Price": fmt_number(price),
                "Change($)": yahoo_fmt(item, "regularMarketChange"),
                "Change(%)": yahoo_fmt(item, "regularMarketChangePercent"),
                "Volume": yahoo_fmt(item, "regularMarketVolume"),
                "Dollar Volume": dollar_volume,
                "Market Cap": yahoo_fmt(item, "marketCap"),
            }
        )
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch Yahoo day gainers into CSV.")
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--count", type=int, default=25)
    args = parser.parse_args()

    rows = fetch(args.count)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows)} rows to {args.output} at {datetime.now(timezone.utc).isoformat()}")


if __name__ == "__main__":
    main()
