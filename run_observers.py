#!/usr/bin/env python3
"""
AI Observer Dashboard — Runner Script

Usage:
  python run_observers.py                          # both agents, today's date
  python run_observers.py --market                 # market only, today
  python run_observers.py --tech                   # tech only, today
  python run_observers.py --market --date 2026-06-01   # market for specific date
  python run_observers.py --date 2026-06-01        # both agents for specific date

Each run saves data/market_YYYY-MM-DD.json and/or data/tech_YYYY-MM-DD.json,
then rebuilds the relevant section(s) in index.html.
If a file for that date already exists, the run is skipped (delete to regenerate).
"""
import argparse
import os
import sys
from datetime import date as DateType
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from agents.market_observer import MarketObserver
from agents.tech_observer import TechObserver


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate AI market/tech review for a given date.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--market", action="store_true", help="Run Market Observer")
    parser.add_argument("--tech",   action="store_true", help="Run Tech Observer")
    parser.add_argument(
        "--date",
        default=DateType.today().isoformat(),
        metavar="YYYY-MM-DD",
        help="Review date (default: today)",
    )
    args = parser.parse_args()

    run_market = args.market or not (args.market or args.tech)
    run_tech   = args.tech   or not (args.market or args.tech)

    if run_market:
        print("=" * 52)
        MarketObserver().run(args.date)
        print()

    if run_tech:
        print("=" * 52)
        TechObserver().run(args.date)
        print()

    print("Done. Open index.html in your browser.")


if __name__ == "__main__":
    main()
