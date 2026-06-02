#!/usr/bin/env python3
"""
AI Observer Dashboard — Runner Script

Usage:
  python run_observers.py              # run both agents
  python run_observers.py --market     # market observer only
  python run_observers.py --tech       # tech observer only
"""
import argparse
import sys
from pathlib import Path

# Ensure repo root is on path
sys.path.insert(0, str(Path(__file__).parent))

from agents.market_observer import MarketObserver
from agents.tech_observer import TechObserver


def main():
    parser = argparse.ArgumentParser(description="AI Observer Dashboard runner")
    parser.add_argument("--market", action="store_true", help="Run market observer")
    parser.add_argument("--tech",   action="store_true", help="Run tech observer")
    args = parser.parse_args()

    run_market = args.market or not (args.market or args.tech)
    run_tech   = args.tech   or not (args.market or args.tech)

    if run_market:
        print("=" * 50)
        print("MARKET OBSERVER")
        print("=" * 50)
        MarketObserver().run()
        print()

    if run_tech:
        print("=" * 50)
        print("TECH OBSERVER")
        print("=" * 50)
        TechObserver().run()
        print()

    print("Done — open index.html in your browser.")


if __name__ == "__main__":
    main()
