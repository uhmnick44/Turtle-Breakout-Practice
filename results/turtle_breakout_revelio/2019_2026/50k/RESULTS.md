# Turtle Breakout - Revelio on MNQ, $50,000 account, with costs

Backtest only. Not forward-tested, not live. Run 2026-11-22. Same data, signals, rules and cost
assumptions as `../10k/RESULTS.md` (MNQ 30-minute candles, 2019-05 to 2026-10, N=20, M=10, 2 ATR stop, long only).

## Sizing
- contracts = floor(2% of closed equity / (stop pts x $2)), minimum 1 (`--policy min1`), compounding.
- 2% of $50k is $1,000. Risk at 1 MNQ ran $365 to $2,721 (median $1,193), so 30 of 53 signals needed more than 2%.
- Main case: 50 signals at 1 contract, 3 at 2 (Dec 2019, Jan 2020, Feb 2020). Actual risk 2.3% average, 5.1% max.
- Skip variants instead pass on any signal that needs more than 2% at 1 contract.

## Costs (assumptions, not a broker quote)
$2.50 per contract per round trip base case (about $1.50 commission plus fees, plus 1 tick of slippage per side), $5.00 stress.
Each day-trading-mode scheduled close and re-entry counts as a round trip, about 19 per signal.

## Results, $50,000 start

| variant | cost/RT | traded | end equity | return | CAGR | PF | expectancy/signal | MTM max DD | costs |
|---|---|---|---|---|---|---|---|---|---|
| day-trading mode, min 1 | $0 | 53 | $63,140 | +26.3% | 3.2% | 1.56 | $248 | -$8,040 (-13.6%) | $0 |
| **day-trading mode, min 1 (main)** | **$2.50** | **53** | **$60,515** | **+21.0%** | **2.6%** | **1.44** | **$198** | **-$8,250 (-14.2%)** | **$2,625** |
| day-trading mode, min 1 | $5.00 | 53 | $57,890 | +15.8% | 2.0% | 1.32 | $149 | -$8,460 (-14.9%) | $5,250 |
| no schedule, min 1 | $2.50 | 53 | $63,767 | +27.5% | 3.3% | 1.60 | $260 | -$7,641 (-12.8%) | $140 |
| no schedule, min 1 | $5.00 | 53 | $63,627 | +27.3% | 3.3% | 1.59 | $257 | -$7,664 (-12.8%) | $280 |
| alert fills, min 1 | $2.50 | 53 | $58,632 | +17.3% | 2.2% | 1.35 | $163 | -$7,574 (-13.3%) | $2,625 |
| alert fills, min 1 | $5.00 | 53 | $56,006 | +12.0% | 1.5% | 1.24 | $113 | -$8,235 (-14.6%) | $5,250 |
| day-trading mode, skip >2% | $2.50 | 23 | $60,436 | +20.9% | 2.6% | 4.16 | $454 | -$3,069 (-5.0%) | $1,440 |
| no schedule, skip >2% | $2.50 | 26 | $62,554 | +25.1% | 3.0% | 3.98 | $483 | -$2,732 (-4.5%) | $72 |
| alert fills, skip >2% | $2.50 | 21 | $58,818 | +17.6% | 2.2% | 3.37 | $420 | -$3,145 (-5.2%) | $1,355 |

Main case detail: win rate 55%, average win $1,186, average loss -$995, worst losing streak 4,
drawdown Nov 2021 to Jan 2023, recovered Feb 2024 (809 days under water), 47% of months positive.
Net without the best trade +$826, without the best two -$2,940. Bootstrap 95% interval on expectancy
-$227 to +$716, P(mean <= 0) = 21.5%.

Holding 1 MNQ over the same period: +$36,901, max drawdown -$12,128 (-17.9% of a $50k account).

## By year, main case

| year | signals | wins | P&L | return | worst drawdown in year |
|---|---|---|---|---|---|
| 2019 (from Jun) | 4 | 3 | +$1,358 | +3.2% | -1.7% |
| 2020 | 8 | 6 | +$2,186 | +4.7% | -6.4% |
| 2021 | 7 | 4 | +$1,470 | +3.9% | -3.8% |
| 2022 | 7 | 2 | -$4,698 | -10.3% | -11.3% |
| 2023 | 6 | 5 | +$5,784 | +12.6% | -3.0% |
| 2024 | 9 | 4 | -$1,544 | -3.7% | -8.4% |
| 2025 | 7 | 3 | -$201 | -0.4% | -7.6% |
| 2026 (to Oct 20) | 5 | 2 | +$6,160 | +11.3% | -6.5% |

## Reading it
- Dollar P&L is almost the same as $10k, because it is almost the same trades at 1 contract. The account is
  five times larger, so percent return and drawdown are about a fifth.
- The skip rows look far better per trade (PF 3.4 to 4.2) but this is a hindsight observation, not evidence.
  Skipping on stop width is a volatility filter, and it was spotted after seeing these results. The skipped
  signals averaged -0.07R, the traded ones +0.61R, on 21 to 26 trades, and the skip count changes with
  equity. Record it as a separate variation and test it out of sample before using it.
- It still made less than holding one contract, though with a smaller drawdown.

## Files
`rep50k_<mode>_<min1|skip>_cost<x>_{summary.json,trades.csv,equity_daily.csv}`. Page data:
`python3 scripts/export_dashboard.py results/turtle_breakout_revelio/2019_2026 data/mnq/mnq_30m_continuous.csv scripts <out> 50k`
