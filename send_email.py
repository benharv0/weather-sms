"""Email each recipient a one-year-ago weather report for a random city.

Env vars (not needed for --dry-run):
  GMAIL_ADDRESS       sending Gmail address
  GMAIL_APP_PASSWORD  16-character Gmail app password
  RECIPIENTS          comma-separated email addresses
"""
from __future__ import annotations

import argparse
import os
import smtplib
import sys
from email.message import EmailMessage

from weather import report_for


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="print messages instead of sending")
    ap.add_argument("--to", help="comma-separated recipients (overrides RECIPIENTS)")
    args = ap.parse_args()

    recipients = [r.strip() for r in (args.to or os.environ.get("RECIPIENTS", "")).split(",") if r.strip()]
    if not recipients:
        print("No recipients: set RECIPIENTS or pass --to", file=sys.stderr)
        return 1

    # Build every message first so a weather-API failure doesn't leave a half-sent run
    msgs = []
    for to in recipients:
        body = report_for()  # each recipient gets their own random city
        msg = EmailMessage()
        msg["To"] = to
        msg["Subject"] = body.split(". ")[0]
        msg.set_content(body)
        msgs.append(msg)

    if args.dry_run:
        for m in msgs:
            print(f"To: {m['To']}\nSubject: {m['Subject']}\n\n{m.get_content()}\n---")
        return 0

    sender = os.environ["GMAIL_ADDRESS"]
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as s:
        s.login(sender, os.environ["GMAIL_APP_PASSWORD"])
        failed = []
        for m in msgs:
            m["From"] = f"Weather Update <{sender}>"
            try:
                s.send_message(m)
                print(f"sent to {m['To']}")
            except Exception as e:
                failed.append(m["To"])
                print(f"FAILED {m['To']}: {e}", file=sys.stderr)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
