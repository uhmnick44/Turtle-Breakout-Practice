# Turtle Breakout - Revelio on MNQ, 2019-05 to 2026-10: sized backtest

Backtest only. Not forward-tested, not live. Run 2026-11-21.

## Setup
- Data: Databento GLBX.MDP3 ohlcv-1m, MNQ.FUT, three batch jobs joined. The 2016-11
  start in the newest job yields nothing before 2019-05-05: MNQ did not trade before then.
  The 2022-10 to 2023-09 overlap between jobs matched on all 539,858 one-minute candles.
- Continuous front month, volume roll, additive back-adjustment (`data/mnq/README.md`).
  30-minute candles. 30 rolls; gaps were negative in 2020-2021 and positive from mid-2022.
- Rules: Pine defaults. N=20, M=10, ATR 20 Wilder, stop 2 ATR, long only.
- Account $100,000. Risk 2% per signal. Contracts = floor(2% of closed equity / (stop pts x $2)),
  decided at the breakout candle, held for every re-entry of that signal.
- Main case: day-trading mode on (the Pine default), fills at the indicator's modeled
  levels, signals whose stop needs more than 2% at 1 contract are skipped, no costs.
- Every one of the 30 signals from the earlier 2022-2026 test reappears at the same time.

## Main result

| metric | value |
|---|---|
| signals / traded / skipped | 53 / 51 / 2 |
| ending equity | $125,561 |
| total return / CAGR | +25.6% / 3.1% a year over 7.5 years |
| win rate | 55% |
| average win / average loss | $1,795 / -$1,074 |
| expectancy | $501 per signal, +0.23R |
| profit factor | 2.03 |
| max drawdown, mark-to-market | -$10,716 (-8.5%), Jul 2024 to Apr 2026 |
| longest time below a prior equity high | 683 days, Jul 2024 to May 2026 |
| worst losing streak | 4 |
| best trade | +$9,794 (Apr-Jun 2026, +4.5R, 1 contract) |
| net without best trade / without best two | +$15,767 / +$7,896 |
| share of net profit from best three trades | 82% |
| bootstrap 95% interval on expectancy | -$37 to +$1,140; P(mean <= 0) = 3.6% |
| months positive / monthly Sharpe | 48% / 0.67 |
| actual risk taken | 1.47% average, 1.99% max (whole-contract rounding) |
| exits | 44 trailing 10-day low, 7 initial stop |

Skipped (stop above the 2% budget): 2025-05-01 (+1.21R) and 2026-08-13 (-0.72R).

## By year (main case)

| year | signals | wins | P&L | return | worst drawdown in year |
|---|---|---|---|---|---|
| 2019 (from Jun) | 4 | 3 | +$4,542 | +5.1% | -2.4% |
| 2020 | 8 | 6 | +$4,987 | +5.0% | -4.9% |
| 2021 | 7 | 4 | +$4,841 | +4.6% | -3.6% |
| 2022 | 7 | 2 | -$4,526 | -4.9% | -5.4% |
| 2023 | 6 | 5 | +$10,824 | +10.9% | -2.7% |
| 2024 | 9 | 4 | -$91 | -1.0% | -4.9% |
| 2025 | 6 | 2 | -$3,184 | -2.6% | -3.6% |
| 2026 (to Oct 20) | 4 | 2 | +$8,168 | +7.0% | -1.9% |

## Variants

| variant | end equity | return | PF | MTM max DD | costs paid |
|---|---|---|---|---|---|
| main case | $125,561 | +25.6% | 2.03 | -8.5% | $0 |
| take 1 contract when the stop exceeds 2% | $127,481 | +27.5% | 2.04 | -8.1% | $0 |
| fixed $2,000 risk, no compounding, skip | $113,825 | +13.8% | 1.62 | -8.5% | $0 |
| fixed $2,000 risk, take 1 contract | $125,082 | +25.1% | 2.03 | -8.1% | $0 |
| pure system, no day-trading schedule | $127,288 | +27.3% | 2.12 | -7.6% | $0 |
| alert-driven fills at candle close | $122,364 | +22.4% | 1.86 | -8.2% | $0 |
| main case, $2.50 per contract round trip | $120,856 | +20.9% | 1.82 | -9.2% | $4,248 |
| main case, $5.00 per contract round trip | $107,024 | +7.0% | 1.27 | -9.7% | $8,285 |
| pure system, $2.50 per contract round trip | $127,068 | +27.1% | 2.10 | -7.6% | $220 |
| alert fills, $2.50 per contract round trip | $118,116 | +18.1% | 1.67 | -8.9% | $4,248 |

Cost figures are assumptions for commission plus fees plus slippage, not any broker's
quoted rate. Day-trading mode makes about 19 round trips per signal; the pure system makes 1.

## Benchmark
Holding 1 MNQ continuously over the same period (rolled, back-adjusted): +$36,901,
max drawdown -$12,671 (-10.7% of $100,000). The strategy averaged about 1.5 contracts,
was in the market about half the time, and made less.

## Reading it
- 2019-05 to 2022-09 was not in the first test and was positive with unchanged rules.
  The rules came from a video, so whether that period was truly unseen by whoever chose
  20/10/2 ATR is unknown.
- The edge is concentrated in the right tail: two trades above +4R carry about 70% of net.
- From 2022 onward the stop was usually wide enough that 2% bought only 1 contract,
  so sizing was effectively 1 contract and compounding did almost nothing.
- Day-trading mode is the cost leak. At $5 per round trip it removes most of the edge.

## Files
`rep_<mode>_<fill>_c<compound>_<policy>[_cost<x>]_{summary.json,trades.csv}`, the main
case's daily mark-to-market equity in `rep_dt_level_c1_skip_equity_daily.csv`, raw signals
in `bt_*`. Rebuild with `scripts/report.py`.
