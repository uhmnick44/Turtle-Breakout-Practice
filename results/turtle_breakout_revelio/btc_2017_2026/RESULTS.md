# Turtle Breakout - Revelio on CME Bitcoin futures, 2017-12 to 2026-11: sized backtest

Backtest only. Not forward-tested, not live. Run 2026-11-22.

## Setup
- Data: Databento GLBX.MDP3 ohlcv-1m BTC.FUT, continuous front month, calendar roll,
  additive back-adjustment, 30-minute candles, classic CME hours (`data/btc/README.md`).
  CME BTC futures start 2017-12-17, so this is 8.9 years, not 10.
- Rules: Pine defaults, unchanged from the MNQ test. N=20, M=10, ATR 20 Wilder, stop 2 ATR, long only.
- Account $100,000. Risk at most 2% of closed equity per signal.
  Contracts = floor(2% of equity / (stop pts x $ per point)), decided at the breakout candle, held for every
  re-entry of that signal. Signals that need more than 2% at 1 contract are skipped.
- Costs are assumptions, per contract per side (not any broker's quoted rate):
  - BTC (5 BTC): $7.50 commission and fees + 2 ticks slippage ($50) = $115 round trip.
  - MBT (0.1 BTC): $2.50 commission and fees + 2 ticks slippage ($1) = $7 round trip. Stress: $15 round trip.
- MBT did not exist before 2021-05-03. For 2017-12 to 2021-05 the MBT results are synthetic:
  BTC futures prices at 0.1 BTC per contract. Real MBT fills in that period cannot be tested.

## 1. The full-size BTC contract does not fit a 2% risk budget on $100k

| | value |
|---|---|
| signals | 42 |
| median 2-ATR stop | 4,404 points = $22,021 per BTC contract |
| smallest stop | 352 points = $1,761 per contract (2019-02) |
| signals tradable at <= 2% | 1 of 42 |

The one tradable signal (2019-02-08) made +3.8R gross but cost $9,545 in day-trading-mode churn
(83 round trips) and closed at -$2,795. With 1 contract on every signal regardless, risk would be
$22k per signal at the median, about 22% of the account. **This instrument is out of reach at this
account size and risk rule.** Everything below uses MBT-sized contracts.

## 2. Main results (MBT, $7 round trip, 2% compounding, skip policy)

| metric | pure system (day-trading off) | Pine default (day-trading on) |
|---|---|---|
| signals traded | 42 | 42 |
| ending equity | $252,505 | $64,720 |
| total return / CAGR | +152.5% / 10.9% | -35.3% / -4.8% |
| win rate | 50% | 26% |
| average win / average loss | $10,302 / -$3,040 | $2,024 / -$1,856 |
| expectancy | $3,631 per signal | -$840 per signal |
| profit factor | 3.39 | 0.39 |
| costs paid | $4,480 | $70,280 |
| max drawdown, mark-to-market | -17.6% (Jan 2021 to Jan 2023) | -38.5% |
| longest time below a prior equity high | 1,035 days | 3,132 days (never recovered) |
| worst losing streak | 5 | 9 |
| months positive | 35% | |
| round trips per signal | 1 | 21 |

### Pure system, by year

| year | signals | wins | P&L | return | worst drawdown in year |
|---|---|---|---|---|---|
| 2018 | 3 | 1 | -$1,986 | -2.0% | -5.6% |
| 2019 | 3 | 2 | +$20,290 | +20.7% | -7.7% |
| 2020 | 4 | 4 | +$71,876 | +56.0% | -4.3% |
| 2021 | 5 | 3 | +$8,313 | +7.6% | -14.9% |
| 2022 | 5 | 0 | -$12,200 | -6.1% | -6.1% |
| 2023 | 5 | 4 | +$44,155 | +25.2% | -5.1% |
| 2024 | 6 | 2 | +$25,403 | +9.7% | -8.5% |
| 2025 | 5 | 2 | -$4,004 | -1.6% | -5.0% |
| 2026 (to Nov 20) | 6 | 3 | +$659 | +0.3% | -4.3% |

### Pure system: how concentrated the edge is
- Best trade: 2020-10-11, +22.7R, +$58,900. The best three trades carry 71% of net profit.
- Net without the best trade: +$93,605. Without the best two: +$64,565.
- Median trade: +0.01R. Mean: +1.30R. Mean without the best two: +0.53R.
- Bootstrap 95% interval on mean R: +0.25R to +2.73R (resampling trades, ignores clustering).
- Since 2025-01: 11 signals, net -$3,345.
- Exits: 38 trailing 10-day low, 4 initial stop. Average hold 28 days, in the market 36% of the time.

## 3. All variants (MBT)

| variant | end equity | return | PF | MTM max DD | costs paid |
|---|---|---|---|---|---|
| pure, level fills, $0 | $257,488 | +157.5% | 3.51 | -17.1% | $0 |
| **pure, level fills, $7** | **$252,505** | **+152.5%** | **3.39** | **-17.6%** | **$4,480** |
| pure, level fills, $15 | $244,130 | +144.1% | 3.27 | -17.9% | $9,375 |
| pure, close fills, $7 | $243,771 | +143.8% | 3.15 | -20.0% | $4,368 |
| pure, close fills, $15 | $233,519 | +133.5% | 3.01 | -20.1% | $9,165 |
| pure, level, $7, fixed $2,000 risk (no compounding) | $203,327 | +103.3% | 4.68 | -14.1% | $2,919 |
| day-trading, level fills, $0 | $163,230 | +63.2% | 2.31 | -21.7% | $0 |
| day-trading, level fills, $7 | $64,720 | -35.3% | 0.39 | -38.5% | $70,280 |
| day-trading, level fills, $15 | $20,839 | -79.2% | 0.01 | -80.3% | $95,595 |
| day-trading, close fills, $7 | $59,928 | -40.1% | 0.31 | -43.6% | $68,187 |

Fixed $2,000 risk rose to 3.4% of equity during drawdowns in the day-trading case, breaking the
2% maximum; it is shown for comparison only.

## 4. Benchmark
50 MBT-sized contracts bought at the first close ($100k notional at $19,660), held and rolled:
$161,300 at the end, with a mark-to-market drawdown of -85% (equity low $16,875). Unadjusted front
month went from $19,660 to $58,915 (3.0x), with a high of $127,240. The start date is
CME BTC's launch week, near the 2017 top, which flatters any strategy compared with holding.

## Reading it
- Day-trading mode is the wrong schedule for Bitcoin. Even before costs it made $63k against $157k
  for the pure system: being flat 16:30-18:00 and from Friday 16:30 to Sunday 18:00 gives up the
  overnight and weekend moves, and spot bitcoin keeps trading during those hours. With costs, about
  21 round trips per signal turn it into a loss. Tiny 2019 stops meant up to 53 contracts x 83 round
  trips on one signal: $30,793 in costs on a trade that made +$7,155 gross.
- The pure system's result rests on a few long trends (2019, 2020, 2023, 2024-Q4). Most trades are
  small losers or scratches, and only 35% of months are positive. To trade it you would need to
  sit through 5-loss streaks and roughly 2-3 years below a prior equity high.
- 42 trades is a small sample. Win rate, profit factor and drawdown each have wide uncertainty, and
  the bootstrap treats trades as independent when they cluster by market regime.
- The rules were not fitted to BTC, which is mildly in their favour. But this is a second market
  tested after seeing the MNQ result, and long-only trend following in an asset that tripled is
  not independent evidence of an edge.
- Before 2021-05 the MBT trades are synthetic, and slippage in thin early BTC futures is probably
  worse than 2 ticks.

## Files
`rep_<btc|mbt>_<mode>_<fill>_cost<rt>[_fixed]_{summary.json,trades.csv,equity_daily.csv}`, raw signals
and segments in `bt_<mode>_<fill>_*`. Rebuild:
    python3 scripts/backtest.py data/btc/btc_30m_continuous.csv --out <dir>/bt_pure_level --daytrading 0 --pv 0.1
    python3 scripts/report.py <dir>/bt_pure_level data/btc/btc_30m_continuous.csv --out <dir>/rep_mbt_pure_level_cost7 --pv 0.1 --cost_rt 7
