# Turtle Breakout - Revelio on MGC, 2016-10 to 2026-11: $100k, 2% risk

Backtest only. Not forward-tested, not live. Run 2026-11-22. Same signals as `../RESULTS.md`
(`../bt_*`); only the sizing differs.

## Setup
- Account $100,000. Contracts = floor(2% of closed equity / (stop pts x $10)), decided at the
  breakout candle, held for every re-entry. Compounding on.
- Main case: day-trading mode on, level fills, $2.50 per contract round trip (assumed), and a
  signal whose stop needs more than 2% at 1 contract is skipped (same convention as the MNQ $100k test).
- Skipped: 2026-03-01 (stop 319 pts, -0.96R) and 2026-04-17 (stop 307 pts, -0.65R). Both lost.
- Margin not modeled.

## Main result

| metric | value |
|---|---|
| signals / traded / skipped | 60 / 58 / 2 |
| contracts | 1 to 9, average 4.1 |
| ending equity | $104,073 |
| total return / CAGR | +4.1% / 0.4% a year over 10.1 years |
| net before costs / costs | +$14,315 / $10,455 |
| win rate | 38% |
| average win / average loss | $2,290 / -$1,286 |
| expectancy | +$70 per signal; +0.04R average, -0.40R median after costs |
| profit factor | 1.09 |
| max drawdown, mark-to-market | -$19,115 (-18.4%), peak 2020-01-07, trough 2022-08-18 |
| longest time below a prior high | 2,101 days |
| worst losing streak | 6 |
| worst single trade | -$2,133 (2020-03-06, -2.2% of equity) |
| actual risk taken | 1.73% average, 1.99% max |
| net without best trade | -$4,860 |
| bootstrap 95% interval on expectancy | -$492 to +$714; P(mean <= 0) = 43% |
| months positive | 31% |

## By year (main case)

| year | traded | P&L | return | worst drawdown in year |
|---|---|---|---|---|
| 2017 (data from Oct 2016) | 7 | +$292 | -1.4% | -4.6% |
| 2018 | 5 | -$4,251 | -1.6% | -8.8% |
| 2019 | 6 | +$2,803 | +2.3% | -6.2% |
| 2020 | 6 | -$5,674 | -4.6% | -8.8% |
| 2021 | 6 | -$3,817 | -3.7% | -7.4% |
| 2022 | 6 | +$1,122 | -2.9% | -10.7% |
| 2023 | 5 | -$1,793 | +0.2% | -6.6% |
| 2024 | 7 | +$5,367 | +6.1% | -5.6% |
| 2025 | 8 | +$8,444 | +9.0% | -7.5% |
| 2026 (to Nov 20) | 2 | +$1,581 | +1.5% | -7.4% |

## Variants (all $100k, 2%, compounding)

| variant | end equity | return | PF | MTM max DD | largest risk | costs | P(mean <= 0) |
|---|---|---|---|---|---|---|---|
| **main: day-trading, level, $2.50, skip** | $104,073 | +4.1% | 1.09 | -18.4% | 2.0% | $10,455 | 43% |
| same, always take 1 contract | $98,974 | -1.0% | 0.98 | -18.4% | 3.1% | $10,480 | 54% |
| day-trading, level, $0 | $114,315 | +14.3% | 1.31 | -16.7% | 2.0% | $0 | 24% |
| day-trading, level, $5.00 | $87,949 | -12.1% | 0.74 | -22.3% | 2.0% | $19,295 | 82% |
| day-trading, close fills, $2.50 | $94,148 | -5.9% | 0.87 | -19.5% | 2.0% | $10,388 | 66% |
| pure system, level, $2.50 | $131,642 | +31.6% | 1.68 | -12.2% | 2.0% | $685 | 8% |
| pure system, level, $5.00 | $130,957 | +31.0% | 1.66 | -12.4% | 2.0% | $1,370 | 9% |
| pure system, close fills, $2.50 | $129,996 | +30.0% | 1.66 | -11.3% | 2.0% | $685 | 8% |
| pure system, level, $2.50, take 1 contract | $126,149 | +26.1% | 1.50 | -12.2% | 2.5% | $690 | 13% |

Benchmark: holding 1 MGC over the period made +$14,556 (max drawdown -$22,297).

## Reading it
- Observation: at $100k the sizing works as intended. Risk stayed at or under 2%, unlike the $10k / 4% / min-1 test.
- Observation: with the day-trading schedule, per-contract costs on about 17 round trips per signal ate 73% of the
  pre-cost profit at $2.50, and all of it at $5.00.
- Observation: the pure system made +31.6% with 1 round trip per signal. Its bootstrap P(mean <= 0) of 8% is the
  strongest of any gold run, but the choice to turn the schedule off came after seeing results, so it is a variant to
  forward-test, not a confirmed edge. 58 trades.
- Observation: the edge is still right-tail dependent: without the best trade the main case is -$4,860.

## Files
`rep_<mode>_<fill>_c1_<policy>[_cost<x>]_{summary.json,trades.csv,equity_daily.csv}`. Rebuild:

    python3 scripts/report.py results/turtle_breakout_revelio/mgc_2016_2026/bt_dt_level data/mgc/mgc_30m_continuous.csv \
        --out <dir>/rep_dt_level_c1_skip_cost2.5 --account 100000 --risk_pct 2 --compound 1 --policy skip --cost_rt 2.5 --pv 10
