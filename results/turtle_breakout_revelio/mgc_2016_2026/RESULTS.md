# Turtle Breakout - Revelio on MGC (Micro Gold), 2016-10 to 2026-11: $10k, 4%, min 1 contract

Backtest only. Not forward-tested, not live. Run 2026-11-22.

## Setup
- Data: Databento GLBX.MDP3 ohlcv-1m, MGC.FUT, job GLBX-20261122-FLQH67SQMY, all 60
  outrights (G J M Q V Z, 2016-2029). Continuous front month, volume roll, additive
  back-adjustment, 30-minute candles (`data/mgc/README.md`). 51 rolls, all gaps positive.
- Contract: MGC = 10 troy oz, $0.10 tick = $1.00, so $10 per $1 of gold.
- Rules: Pine defaults, unchanged from the MNQ tests. N=20, M=10, ATR 20 Wilder, stop 2 ATR, long only.
- Account $10,000. Contracts = floor(4% of closed equity / (stop pts x $10)), **minimum 1**.
  Decided at the breakout candle, held for every re-entry of that signal.
- Main case: day-trading mode on (Pine default), fills at the indicator's modeled levels,
  $2.50 per contract round trip (assumption for commission + fees + slippage, not a quoted rate).
- Not modeled: margin requirements, margin calls, broker liquidation rules.

## The sizing problem, measured
4% of $10k is $400. One MGC contract's initial stop cost less than that on only 20 of 60
signals, almost all before 2020. The "min 1 contract" rule then decides the real risk:

| | main case |
|---|---|
| contracts on every signal | 1 (never 2) |
| average actual risk at entry | 7.8% of equity |
| signals risking over 10% / over 20% | 11 / 3 |
| largest single risk | 37.6% (2026-04-17, stop 307 pts = $3,071 on $8,172) |
| worst single loss | -$3,073 (2026-03-01, -28% of equity) |

From late 2025 the system was not a 4% system. It was a 15-38% per trade system.

## Main result (day-trading on, level fills, $2.50 RT)

| metric | value |
|---|---|
| signals / traded | 60 / 60 |
| ending equity | $7,537 |
| total return / CAGR | -24.6% / -2.8% a year over 10.1 years |
| win rate | 37% |
| average win / average loss | $794 / -$525 (payoff 1.51) |
| expectancy | -$41 per signal |
| profit factor | 0.88 |
| max drawdown, closed trades | -$5,098 |
| max drawdown, mark-to-market | -$13,862 (-69.8%), peak 2026-01-29, trough 2026-08-05, not recovered |
| lowest closed equity | $5,878 |
| worst losing streak | 6 |
| best trade | +$4,467 (Sep-Oct 2025, +5.0R) |
| net without best trade | -$6,930 |
| bootstrap 95% interval on expectancy | -$277 to +$221; P(mean <= 0) = 64% |
| months positive | 31% |
| costs paid | $2,538 (about 17 round trips per signal) |
| exits | 50 trailing 10-day low, 10 initial stop |

The mark-to-market drawdown is mostly open profit given back: the Jan 2026 signal was up
1,006 points ($10,057) at its best and closed +23 points. Across all 60 signals the average
best open gain was 117 points; the average closed result was 0.1 points.

## By year (main case)

| year | signals | P&L | return | worst drawdown in year |
|---|---|---|---|---|
| 2017 (data from Oct 2016) | 7 | +$21 | -1.9% | -6.1% |
| 2018 | 5 | -$651 | -3.2% | -12.2% |
| 2019 | 6 | +$529 | +5.0% | -7.6% |
| 2020 | 6 | -$1,555 | -11.1% | -21.7% |
| 2021 | 6 | -$860 | -10.4% | -21.0% |
| 2022 | 6 | +$225 | -11.1% | -34.2% |
| 2023 | 5 | -$384 | +3.7% | -20.3% |
| 2024 | 7 | +$810 | +11.1% | -19.4% |
| 2025 | 8 | +$2,919 | +35.9% | -47.9% |
| 2026 (to Nov 20) | 4 | -$3,517 | -31.8% | -68.4% |

P&L is by signal start year; return and drawdown are mark-to-market by calendar year, so
the two can differ in sign.

## Variants (all $10k, 4%, min 1 contract, compounding)

| variant | end equity | return | PF | MTM max DD | closed-trade DD | costs |
|---|---|---|---|---|---|---|
| **main: day-trading, level fills, $2.50** | $7,537 | -24.6% | 0.88 | -69.8% | -$5,098 | $2,538 |
| day-trading, level fills, $0 | $10,074 | +0.7% | 1.00 | -62.0% | -$5,073 | $0 |
| day-trading, level fills, $5.00 | $4,999 | -50.0% | 0.76 | -79.9% | | $5,075 |
| day-trading, close fills, $2.50 | $6,177 | -38.2% | 0.80 | -71.5% | | $2,538 |
| day-trading, close fills, $5.00 | $3,640 | -63.6% | 0.69 | -83.6% | | $5,075 |
| pure system, level fills, $2.50 | $13,333 | +33.3% | 1.19 | -56.5% | -$5,492 | $150 |
| pure system, level fills, $5.00 | $13,183 | +31.8% | 1.18 | -56.8% | | $300 |
| pure system, close fills, $2.50 | $13,697 | +37.0% | 1.21 | -54.4% | | $150 |
| reference: skip signals over 4%, day-trading, $2.50 | $9,384 | -6.2% | 0.72 | -14.9% | | $822 |

Pure system bootstrap P(mean <= 0) is about 33%: not evidence of an edge either.
2019 onward only (better data): main case -$1,832, PF 0.90; pure level $2.50 +$3,145, PF 1.19.

## Benchmark
Holding 1 MGC continuously (rolled, back-adjusted) over the same period: +$14,556,
max drawdown -$22,297 (-47.8% on a $10k start). Raw price went from $1,266 to $3,539.

## Reading it
- Observation: on MGC with day-trading mode, the system was flat before costs and lost after costs.
  60 signals is a small sample, and the bootstrap interval spans zero in every variant.
- Observation: day-trading mode cost about $3,400 versus the pure system before any commission,
  and 17 round trips per signal multiplied the costs. Why the flatten at 16:30 / re-enter at 18:00
  hurts on gold is a hypothesis to test, not something this run shows.
- Observation: the 10-day-low trail gave back almost all open profit on average (117 pts MFE vs 0.1 pts kept).
  Any exit change is a new variant to test separately, not a fix to this result.
- Risk: with $10k and min 1 contract, the position size is set by gold's volatility, not by the
  4% rule. A 2 ATR stop on gold above $4,000 was $1,700-$3,200 per contract.
- MGC was thin in 2016-2018 (median 700-900 one-minute bars a day vs about 1,380 from 2020),
  so those years' daily highs and lows are less reliable.

## Files
`bt_<mode>_<fill>_*` raw signals and segments at 1 contract; `rep_<mode>_<fill>_c1_<policy>[_cost<x>]_{summary.json,trades.csv,equity_daily.csv}`
sized runs. Rebuild:

    python3 scripts/backtest.py data/mgc/mgc_30m_continuous.csv --out <dir>/bt_dt_level --pv 10
    python3 scripts/report.py <dir>/bt_dt_level data/mgc/mgc_30m_continuous.csv --out <dir>/rep_dt_level_c1_min1_cost2.5 \
        --account 10000 --risk_pct 4 --compound 1 --policy min1 --cost_rt 2.5 --pv 10
