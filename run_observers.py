#!/usr/bin/env python3
"""
AI Observer Dashboard — Runner Script

Usage:
  python run_observers.py                           # all agents, today's date
  python run_observers.py --market                  # market only, today
  python run_observers.py --tech                    # tech only, today
  python run_observers.py --startup                 # startup only, today
  python run_observers.py --market --date 2026-06-01    # market for specific date
  python run_observers.py --date 2026-06-01         # all agents for specific date

Each run saves data/{section}_YYYY-MM-DD.json and rebuilds index.html.
If a file for that date already exists, the run is skipped (delete to regenerate).
"""
import argparse
import sys
from datetime import date as DateType
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from agents.market_observer import MarketObserver
from agents.startup_observer import StartupObserver
from agents.tech_observer import TechObserver


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate AI market/tech/startup review for a given date.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--market",  action="store_true", help="Run Market Observer")
    parser.add_argument("--tech",    action="store_true", help="Run Tech Observer")
    parser.add_argument("--startup", action="store_true", help="Run Startup Observer")
    parser.add_argument(
        "--date",
        default=DateType.today().isoformat(),
        metavar="YYYY-MM-DD",
        help="Review date (default: today)",
    )
    args = parser.parse_args()

    any_selected = args.market or args.tech or args.startup
    run_market  = args.market  or not any_selected
    run_tech    = args.tech    or not any_selected
    run_startup = args.startup or not any_selected

    if run_market:
        print("=" * 52)
        MarketObserver().run(args.date)
        print()

    if run_tech:
        print("=" * 52)
        TechObserver().run(args.date)
        print()

    if run_startup:
        print("=" * 52)
        StartupObserver().run(args.date)
        print()

    print("Done. Open index.html in your browser.")


if __name__ == "__main__":
    main()
