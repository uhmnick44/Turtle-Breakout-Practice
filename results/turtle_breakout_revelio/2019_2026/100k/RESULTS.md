# Turtle Breakout - Revelio on MNQ, $100,000 account, with costs

Backtest only. Not forward-tested, not live. Run 2026-11-22. Same data, signals, rules and cost assumptions
as `../10k/RESULTS.md` and `../50k/RESULTS.md`. The original no-cost $100k report is `../RESULTS.md`.

## Sizing
- contracts = floor(2% of closed equity / (stop pts x $2)), minimum 1, compounding. 2% of $100k is $2,000.
- Main case contracts: 30 signals at 1, 17 at 2, 3 at 3, 1 at 4, 2 at 5. Only 2 signals needed more than 2% at
  1 contract (2025-05-01, 2026-08-13) and were taken at 1 anyway. Actual risk 1.51% average, 2.4% max.
- From 2022 on, stops were wide enough that it was mostly 1 contract.

Consistency check: the skip, no-cost run reproduces the original report's main case ($125,561), and skip at
$2.50 reproduces its $2.50 variant ($120,856).

## Results, $100,000 start

| variant | cost/RT | traded | end equity | return | CAGR | PF | expectancy/signal | MTM max DD | costs |
|---|---|---|---|---|---|---|---|---|---|
| day-trading mode, min 1 | $0 | 53 | $127,481 | +27.5% | 3.3% | 2.04 | $519 | -$9,599 (-8.1%) | $0 |
| **day-trading mode, min 1 (main)** | **$2.50** | **53** | **$122,213** | **+22.2%** | **2.7%** | **1.81** | **$419** | **-$9,821 (-8.5%)** | **$4,352** |
| day-trading mode, min 1 | $5.00 | 53 | $117,861 | +17.9% | 2.2% | 1.64 | $337 | -$10,044 (-8.8%) | $8,705 |
| no schedule, min 1 | $2.50 | 53 | $127,004 | +27.0% | 3.3% | 1.98 | $510 | -$9,128 (-7.6%) | $228 |
| no schedule, min 1 | $5.00 | 53 | $126,777 | +26.8% | 3.2% | 1.97 | $505 | -$9,153 (-7.7%) | $455 |
| alert fills, min 1 | $2.50 | 53 | $118,547 | +18.5% | 2.3% | 1.64 | $350 | -$9,057 (-8.0%) | $4,352 |
| alert fills, min 1 | $5.00 | 53 | $114,627 | +14.6% | 1.8% | 1.49 | $276 | -$9,280 (-8.3%) | $8,645 |
| day-trading mode, skip >2% | $2.50 | 51 | $120,856 | +20.9% | 2.6% | 1.82 | $409 | -$11,143 (-9.2%) | $4,248 |
| no schedule, skip >2% | $2.50 | 51 | $127,068 | +27.1% | 3.3% | 2.10 | $531 | -$9,659 (-7.6%) | $220 |
| alert fills, skip >2% | $2.50 | 51 | $118,116 | +18.1% | 2.3% | 1.67 | $355 | -$10,726 (-8.9%) | $4,248 |

Main case detail: win rate 55%, average win $1,708, average loss -$1,138, worst losing streak 4, drawdown
Nov 2021 to Jan 2023, recovered Jul 2023, longest time under water 665 days, 47% of months positive.
Net without the best trade +$12,524, without the best two +$4,993; the two trades above +4R are 78% of net.
Bootstrap 95% interval on expectancy -$110 to +$1,034, P(mean <= 0) = 6.7%.

Holding 1 MNQ over the same period: +$36,901, max drawdown -$12,128 (-10.3% of $100k).

## By year, main case

| year | signals | wins | P&L | return | worst drawdown in year |
|---|---|---|---|---|---|
| 2019 (from Jun) | 4 | 3 | +$3,716 | +4.3% | -2.6% |
| 2020 | 8 | 6 | +$4,050 | +4.2% | -5.0% |
| 2021 | 7 | 4 | +$3,768 | +3.6% | -3.8% |
| 2022 | 7 | 2 | -$4,698 | -5.1% | -5.7% |
| 2023 | 6 | 5 | +$10,148 | +10.6% | -2.9% |
| 2024 | 9 | 4 | -$730 | -1.6% | -5.2% |
| 2025 | 7 | 3 | -$201 | -0.2% | -3.7% |
| 2026 (to Oct 20) | 5 | 2 | +$6,160 | +5.3% | -3.3% |

## Reading it
- $100k is the only size where 2% sizing actually works as designed: risk stays near 1.5%, and the account
  can size up when stops are tight (2019-2021).
- Costs take $4,352 in day-trading mode, about a fifth of gross. Without the schedule they are $228.
- Still less than holding one contract in dollars, with a smaller drawdown.
- The skip rule barely matters here (2 signals), unlike at $50k, where it removed 30.

## Files
`rep100k_<mode>_<min1|skip>_cost<x>_{summary.json,trades.csv,equity_daily.csv}`. Page data:
`python3 scripts/export_dashboard.py results/turtle_breakout_revelio/2019_2026 data/mnq/mnq_30m_continuous.csv scripts <out> 100kc`
