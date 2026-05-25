#!/usr/bin/env python
"""GitHub Actions wrapper for the stock discovery skill workflow."""

from __future__ import annotations

import argparse
import csv
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ORCHESTRATOR = ROOT / "skills" / "stock-discovery-orchestrator" / "scripts" / "run_workflow.py"
FETCHER = ROOT / "scripts" / "fetch_yahoo_gainers.py"


def find_input_csv(scan: str, explicit_input: str | None) -> Path:
    if explicit_input:
        path = (ROOT / explicit_input).resolve()
        if path.exists():
            return path
        raise FileNotFoundError(f"Requested input CSV does not exist: {path}")

    candidates = []
    for pattern in (
        f"data/{scan}/*.csv",
        f"data/{scan}.csv",
        "data/latest/*.csv",
        "data/*.csv",
    ):
        candidates.extend(ROOT.glob(pattern))
    if candidates:
        return max(candidates, key=lambda path: path.stat().st_mtime)

    generated = ROOT / "data" / "generated" / scan / f"yahoo_gainers_{datetime.now(timezone.utc).strftime('%Y-%m-%d_%H%M_utc')}.csv"
    subprocess.run(
        [sys.executable, str(FETCHER), "--output", str(generated), "--count", "25"],
        check=True,
        cwd=ROOT,
    )
    return generated


def write_summary(output_csv: Path, summary_path: Path, scan: str) -> None:
    with output_csv.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))

    lines = [
        f"Stock Discovery Momentum Report - {scan}",
        f"Generated: {datetime.now(timezone.utc).replace(microsecond=0).isoformat()}",
        "",
        "Top candidates:",
    ]

    for idx, row in enumerate(rows[:7], start=1):
        lines.append(
            f"{idx}. {row.get('Symbol', '')} - {row.get('Recommendation', '')}; "
            f"move {row.get('Change(%)', 'N/A')}; RVOL {row.get('RVOL 20D', 'N/A')}; "
            f"catalyst {row.get('Catalyst Type', 'N/A')}; confidence {row.get('Confidence 1-5', 'N/A')}/5; "
            f"hold zone {row.get('Hold Zone Low', 'N/A')} - {row.get('Hold Zone High', 'N/A')}; "
            f"trim review {row.get('Trim / Partial Sell Price', 'N/A')}; analyst {row.get('Analyst Rating', 'N/A')}; "
            f"upside {row.get('Implied Upside %', 'N/A')}; "
            f"next: {row.get('Next Research Step', 'N/A')}"
        )

    lines.extend(
        [
            "",
            "Research reminder: this is a watchlist and discussion aid, not financial advice.",
        ]
    )
    summary_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run scheduled stock discovery report.")
    parser.add_argument("--scan", required=True, help="Scan name, for example us_open.")
    parser.add_argument("--input-csv", default="", help="Optional input CSV path relative to repo root.")
    args = parser.parse_args()

    scan = args.scan.strip() or "manual"
    input_csv = find_input_csv(scan, args.input_csv.strip() or None)
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d_%H%M_utc")
    out_dir = ROOT / "outputs" / scan
    out_dir.mkdir(parents=True, exist_ok=True)
    output_csv = out_dir / f"stock_discovery_watchlist_{scan}_{stamp}.csv"
    summary_path = out_dir / f"stock_discovery_summary_{scan}_{stamp}.txt"

    subprocess.run(
        [
            sys.executable,
            str(ORCHESTRATOR),
            "--input",
            str(input_csv),
            "--output",
            str(output_csv),
            "--limit",
            "25",
        ],
        check=True,
        cwd=ROOT,
    )
    write_summary(output_csv, summary_path, scan)
    print(f"Wrote {output_csv}")
    print(f"Wrote {summary_path}")


if __name__ == "__main__":
    main()
