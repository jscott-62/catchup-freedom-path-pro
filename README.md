# Freedom Path Explorer

The "step 2" dashboard in The Great Catch-Up funnel. Given a Freedom Number (and the rate of return required to hit it), this tool lets a user explore which catch-up assets could realistically get them there.

**Live:** https://jscott-62.github.io/catchup-freedom-path/

## Tabs

1. **Freedom Number** — build the target from current expenses, income, retirement-adjustment, optional inflation
2. **Overview** — asset cards with Catch-Up Fit Score for the user's required return
3. **Compare** — returns, volatility, drawdown charts side-by-side
4. **DCA Simulator** — what monthly investing would have produced per asset

## Asset universe

- **Crypto (3):** BTC, ETH, SOL
- **Traditional (8):** GLD, SPY, QQQ, ARKK, TSLA, NVDA, MSTR, IBIT

Custom tickers can be added at runtime via CoinGecko (crypto only).

## Funnel position

```
Freedom Number Calculator  →  Freedom Path Explorer  →  Catch-Up Asset Dashboard (full)
(jscott-62.github.io/         (this repo)                (catchup-asset-dashboard)
 catchup-freedom-number)
```

The full Asset Dashboard adds Portfolio Builder, My Portfolio, Holding Periods, and the Selling Rules (Mechanical Harvest Framework).

## Data

Prices refresh weekly via GitHub Action (`refresh-data.yml`) every Monday 06:00 UTC. The dashboard shows a stale-data banner if the file is older than 14 days.

## Architecture

Single-file vanilla JS app. No dependencies. localStorage keys:

- `catchup-freedom-path-settings` — user inputs and selected assets
- `catchup-freedom-path-cached-assets` — custom CoinGecko tickers

Settings can be exported / imported / reset from the header.
