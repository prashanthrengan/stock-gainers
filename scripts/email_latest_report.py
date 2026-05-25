#!/usr/bin/env python
"""Email the latest CSV and text summary for a scan using SMTP secrets."""

from __future__ import annotations

import argparse
import os
import smtplib
from email.message import EmailMessage
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def required_env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise RuntimeError(f"Missing required environment variable or GitHub Secret: {name}")
    return value


def latest_file(directory: Path, pattern: str) -> Path:
    matches = list(directory.glob(pattern))
    if not matches:
        raise FileNotFoundError(f"No files matching {pattern} in {directory}")
    return max(matches, key=lambda path: path.stat().st_mtime)


def main() -> None:
    parser = argparse.ArgumentParser(description="Email latest stock discovery report.")
    parser.add_argument("--scan", required=True)
    args = parser.parse_args()

    out_dir = ROOT / "outputs" / args.scan
    csv_path = latest_file(out_dir, "stock_discovery_watchlist_*.csv")
    summary_path = latest_file(out_dir, "stock_discovery_summary_*.txt")

    host = required_env("SMTP_HOST")
    port = int(os.environ.get("SMTP_PORT", "587"))
    username = required_env("SMTP_USERNAME")
    password = required_env("SMTP_PASSWORD")
    sender = os.environ.get("SMTP_FROM", username).strip() or username
    recipient = os.environ.get("REPORT_TO", "prashanthrengan@gmail.com").strip()

    summary = summary_path.read_text(encoding="utf-8")
    message = EmailMessage()
    message["From"] = sender
    message["To"] = recipient
    message["Subject"] = f"Stock discovery report - {args.scan}"
    message.set_content(summary)

    for path in (csv_path, summary_path):
        message.add_attachment(
            path.read_bytes(),
            maintype="text",
            subtype="csv" if path.suffix.lower() == ".csv" else "plain",
            filename=path.name,
        )

    with smtplib.SMTP(host, port, timeout=30) as smtp:
        smtp.starttls()
        smtp.login(username, password)
        smtp.send_message(message)
    print(f"Emailed {csv_path.name} and {summary_path.name} to {recipient}")


if __name__ == "__main__":
    main()

