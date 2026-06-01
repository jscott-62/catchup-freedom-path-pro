#!/usr/bin/env python3
"""
Fetch historical monthly closing prices for catch-up assets.
Uses Yahoo Finance direct API for stocks/ETFs and CoinGecko for crypto.
Outputs docs/asset-data.json and docs/asset-data.js

Usage:
  python3 scripts/update-asset-data.py
  python3 scripts/update-asset-data.py --tickers MSTR COIN MARA
"""

import json
import sys
import os
import time
import urllib.request
from datetime import datetime, timedelta

DEFAULT_ASSETS = {
    # --- Crypto (Bitcoin + 2 blue-chip alts) ---
    "BTC": {
        "ticker": "BTC-USD",
        "name": "Bitcoin",
        "category": "Cryptocurrency",
        "color": "#f59e0b",
        "source": "yahoo"
    },
    "ETH": {
        "ticker": "ETH-USD",
        "name": "Ethereum",
        "category": "Cryptocurrency",
        "color": "#627eea",
        "source": "yahoo"
    },
    "SOL": {
        "ticker": "SOL-USD",
        "name": "Solana",
        "category": "Cryptocurrency",
        "color": "#9945ff",
        "source": "yahoo"
    },
    # --- Traditional Assets ---
    "GLD": {
        "ticker": "GLD",
        "name": "Gold (GLD ETF)",
        "category": "Commodity",
        "color": "#eab308",
        "source": "yahoo"
    },
    "SLV": {
        "ticker": "SLV",
        "name": "Silver (SLV ETF)",
        "category": "Commodity",
        "color": "#cbd5e1",
        "source": "yahoo"
    },
    "CPER": {
        "ticker": "CPER",
        "name": "Copper (CPER ETF)",
        "category": "Commodity",
        "color": "#b45309",
        "source": "yahoo"
    },
    "SPY": {
        "ticker": "SPY",
        "name": "S&P 500 (SPY)",
        "category": "Index Fund",
        "color": "#3b82f6",
        "source": "yahoo"
    },
    "QQQ": {
        "ticker": "QQQ",
        "name": "Nasdaq 100 (QQQ)",
        "category": "Tech Index",
        "color": "#a855f7",
        "source": "yahoo"
    },
    "ARKK": {
        "ticker": "ARKK",
        "name": "ARK Innovation (ARKK)",
        "category": "Disruptive Tech ETF",
        "color": "#22c55e",
        "source": "yahoo"
    },
    "TSLA": {
        "ticker": "TSLA",
        "name": "Tesla (TSLA)",
        "category": "Individual Stock",
        "color": "#ef4444",
        "source": "yahoo"
    },
    "NVDA": {
        "ticker": "NVDA",
        "name": "Nvidia (NVDA)",
        "category": "Individual Stock",
        "color": "#06b6d4",
        "source": "yahoo"
    },
    "MSTR": {
        "ticker": "MSTR",
        "name": "Strategy (MSTR)",
        "category": "Bitcoin Treasury",
        "color": "#f97316",
        "source": "yahoo"
    },
    "IBIT": {
        "ticker": "IBIT",
        "name": "iShares Bitcoin Trust (IBIT)",
        "category": "Bitcoin ETF",
        "color": "#fb923c",
        "source": "yahoo"
    },
    # --- Tech Sector ETFs (broader exposure) ---
    "SMH": {
        "ticker": "SMH",
        "name": "Semiconductor (SMH)",
        "category": "Tech Index",
        "color": "#84cc16",
        "source": "yahoo"
    },
    "VGT": {
        "ticker": "VGT",
        "name": "Vanguard Info Tech (VGT)",
        "category": "Tech Index",
        "color": "#0ea5e9",
        "source": "yahoo"
    },
    "XLK": {
        "ticker": "XLK",
        "name": "Tech Select Sector (XLK)",
        "category": "Tech Index",
        "color": "#14b8a6",
        "source": "yahoo"
    },
    # --- Mega-Cap Tech (Mag-7 individual stocks) ---
    "AAPL": {
        "ticker": "AAPL",
        "name": "Apple (AAPL)",
        "category": "Individual Stock",
        "color": "#94a3b8",
        "source": "yahoo"
    },
    "MSFT": {
        "ticker": "MSFT",
        "name": "Microsoft (MSFT)",
        "category": "Individual Stock",
        "color": "#0d9488",
        "source": "yahoo"
    },
    "AMZN": {
        "ticker": "AMZN",
        "name": "Amazon (AMZN)",
        "category": "Individual Stock",
        "color": "#d97706",
        "source": "yahoo"
    },
    "GOOGL": {
        "ticker": "GOOGL",
        "name": "Alphabet (GOOGL)",
        "category": "Individual Stock",
        "color": "#dc2626",
        "source": "yahoo"
    },
    "AVGO": {
        "ticker": "AVGO",
        "name": "Broadcom (AVGO)",
        "category": "Individual Stock",
        "color": "#7c3aed",
        "source": "yahoo"
    }
}

CUSTOM_COLORS = ["#ec4899", "#14b8a6", "#f97316", "#8b5cf6", "#10b981", "#e11d48"]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
}


def fetch_yahoo(ticker):
    """Fetch monthly prices from Yahoo Finance v8 chart API."""
    print(f"  Fetching {ticker} from Yahoo Finance...")
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?range=10y&interval=1mo"
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode())

        result = data["chart"]["result"][0]
        timestamps = result["timestamp"]
        closes = result["indicators"]["quote"][0]["close"]

        prices = []
        skipped = 0
        for ts, close in zip(timestamps, closes):
            # Yahoo sometimes returns 0, None, or sub-cent values for months
            # before an asset actually existed. After rounding, sub-cent
            # values become 0.00 and would break DCA math (divide by zero →
            # NaN cascade). Use higher precision so micro-cap crypto stays
            # representable, and skip anything that still rounds to zero.
            if close is None or close <= 0:
                skipped += 1
                continue
            # Keep up to 6 decimals for sub-dollar assets, 2 decimals for
            # anything priced like a normal asset.
            close_f = float(close)
            decimals = 6 if close_f < 1 else 2
            rounded = round(close_f, decimals)
            if rounded <= 0:
                skipped += 1
                continue
            dt = datetime.fromtimestamp(ts)
            prices.append({
                "date": dt.strftime("%Y-%m-%d"),
                "close": rounded
            })

        print(f"  Got {len(prices)} monthly data points" + (f" (skipped {skipped} invalid)" if skipped else ""))
        return prices

    except Exception as e:
        print(f"  ERROR: {e}")
        return None


def fetch_coingecko(coin_id):
    """Fetch historical prices from CoinGecko (free, no API key)."""
    print(f"  Fetching {coin_id} from CoinGecko...")
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart?vs_currency=usd&days=3650&interval=daily"
    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": "CatchUpDashboard/1.0",
            "Accept": "application/json"
        })
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode())

        # Group by month, take last price per month
        monthly = {}
        for ts_ms, price in data["prices"]:
            dt = datetime.fromtimestamp(ts_ms / 1000)
            month_key = dt.strftime("%Y-%m")
            monthly[month_key] = {
                "date": dt.strftime("%Y-%m-%d"),
                "close": round(price, 2)
            }

        prices = sorted(monthly.values(), key=lambda x: x["date"])
        print(f"  Got {len(prices)} monthly data points")
        return prices

    except Exception as e:
        print(f"  ERROR: {e}")
        return None


def main():
    extra_tickers = []
    if "--tickers" in sys.argv:
        idx = sys.argv.index("--tickers")
        extra_tickers = sys.argv[idx + 1:]

    print("Fetching historical asset data...")
    if extra_tickers:
        print(f"Extra tickers: {extra_tickers}")

    assets = {}

    for key, config in DEFAULT_ASSETS.items():
        time.sleep(1)

        if config["source"] == "coingecko":
            prices = fetch_coingecko(config["coingecko_id"])
        else:
            prices = fetch_yahoo(config["ticker"])

        if prices and len(prices) > 0:
            assets[key] = {
                "name": config["name"],
                "ticker": config["ticker"],
                "category": config["category"],
                "color": config["color"],
                "inceptionDate": prices[0]["date"],
                "monthlyPrices": prices
            }
        else:
            print(f"  SKIPPED {key}")

    for i, ticker in enumerate(extra_tickers):
        time.sleep(1)
        ticker_upper = ticker.upper()
        prices = fetch_yahoo(ticker_upper)
        if prices and len(prices) > 0:
            color = CUSTOM_COLORS[i % len(CUSTOM_COLORS)]
            assets[ticker_upper] = {
                "name": ticker_upper,
                "ticker": ticker_upper,
                "category": "Custom",
                "color": color,
                "inceptionDate": prices[0]["date"],
                "monthlyPrices": prices
            }

    output = {
        "lastUpdated": datetime.now().strftime("%Y-%m-%d"),
        "assets": assets
    }

    script_dir = os.path.dirname(os.path.abspath(__file__))
    docs_dir = os.path.join(os.path.dirname(script_dir), "docs")

    json_path = os.path.join(docs_dir, "asset-data.json")
    with open(json_path, "w") as f:
        json.dump(output, f, indent=2)
    print(f"\nWrote {json_path}")

    js_path = os.path.join(docs_dir, "asset-data.js")
    with open(js_path, "w") as f:
        f.write("// Auto-generated by scripts/update-asset-data.py\n")
        f.write("// Do not edit manually. Run the script to regenerate.\n")
        f.write("window.ASSET_DATA = ")
        json.dump(output, f, indent=2)
        f.write(";\n")
    print(f"Wrote {js_path}")

    print(f"\nSummary:")
    for key, data in assets.items():
        print(f"  {key}: {len(data['monthlyPrices'])} months from {data['inceptionDate']}")


if __name__ == "__main__":
    main()
