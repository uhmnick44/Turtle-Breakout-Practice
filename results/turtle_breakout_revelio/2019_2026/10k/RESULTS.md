# Turtle Breakout - Revelio on MNQ, $10,000 account, with costs

Backtest only. Not forward-tested, not live. Run 2026-11-21. Same data, signals and rules as
`../RESULTS.md` (MNQ 30-minute candles, 2019-05 to 2026-10, N=20, M=10, 2 ATR stop, long only).
The 53 signals were regenerated with `scripts/backtest.py` and matched the committed ones exactly.

## Sizing: 1 contract is already too big
- Rule: contracts = floor(2% of closed equity / (stop pts x $2)), with a minimum of 1 (`--policy min1`).
- Risk at 1 MNQ ranged from $365 to $2,721 per signal, median $1,193. On $10k that is 3.6% to 27%.
- For a second contract to fit inside 2%, equity would need to be at least 100 x the 1-contract risk,
  so $36k or more. That never happened. **All 53 signals traded at exactly 1 MNQ.**
- With a strict 2% cap (`skip`), the result is **zero trades**. No signal fits 2% of $10k.
- Actual risk taken, main case: 9.0% average, 21.9% max, above 10% on 20 of 53 signals.

## Costs (assumptions, not a broker quote)
Charged per contract per round trip. Every scheduled close or re-entry in day-trading mode counts as a round trip.
- $2.50 base case: about $1.50 commission plus exchange and NFA fees, plus 1 tick ($0.50) of slippage per side.
- $5.00 stress case: higher commission and 2+ ticks of slippage per side.
- Published all-in micro rates seen 2026-11-21 ran from about $0.74 to $2.50 round trip depending on the broker. Check your own broker.

## Results, $10,000 start, 1 MNQ on every signal

| variant | cost/RT | end equity | return | CAGR | PF | expectancy/signal | MTM max DD | costs paid |
|---|---|---|---|---|---|---|---|---|
| day-trading mode, level fills | $0 | $22,318 | +123% | 11.4% | 1.53 | $232 | -$8,040 (-44.0%) | $0 |
| **day-trading mode, level fills (main)** | **$2.50** | **$19,811** | **+98%** | **9.6%** | **1.41** | **$185** | **-$8,250 (-47.8%)** | **$2,508** |
| day-trading mode, level fills | $5.00 | $17,303 | +73% | 7.6% | 1.30 | $138 | -$8,460 (-52.1%) | $5,015 |
| no day-trading schedule | $2.50 | $23,138 | +131% | 11.9% | 1.57 | $248 | -$7,641 (-39.9%) | $132 |
| no day-trading schedule | $5.00 | $23,005 | +130% | 11.8% | 1.57 | $245 | -$7,664 (-40.1%) | $265 |
| alert fills at candle close | $2.50 | $17,754 | +78% | 8.0% | 1.32 | $146 | -$7,574 (-47.0%) | $2,508 |
| alert fills at candle close | $5.00 | $15,247 | +53% | 5.8% | 1.21 | $99 | -$8,235 (-53.0%) | $5,015 |

Main case detail: win rate 55%, average win $1,162, average loss -$995, worst trade -$1,833,
best +$9,689, worst losing streak 4. Drawdown ran from a Nov 2021 peak to a Jan 2023 trough and
recovered in Feb 2024, 809 days under water. 47% of months positive.

## By year, main case ($2.50 per round trip)

| year | signals | wins | P&L | return | worst drawdown in year |
|---|---|---|---|---|---|
| 2019 (from Jun) | 4 | 3 | +$1,002 | +11.3% | -8.1% |
| 2020 | 8 | 6 | +$1,838 | +19.6% | -22.4% |
| 2021 | 7 | 4 | +$1,470 | +15.7% | -14.4% |
| 2022 | 7 | 2 | -$4,698 | -37.6% | -40.0% |
| 2023 | 6 | 5 | +$5,784 | +66.2% | -11.5% |
| 2024 | 9 | 4 | -$1,544 | -13.3% | -27.9% |
| 2025 | 7 | 3 | -$201 | -1.4% | -24.7% |
| 2026 (to Oct 20) | 5 | 2 | +$6,160 | +45.1% | -17.7% |

## Reading it
- The return looks bigger than the $100k test only because 1 fixed contract is a far larger share of $10k.
  This is roughly 4 to 5 times the risk per trade of the $100k version, not a better system.
- Edge is thin and concentrated: main case net without the best two trades is -$3,644.
  Bootstrap 95% interval on expectancy is -$241 to +$704, P(mean <= 0) = 23%. 53 signals is not enough to call it proven.
- Starting in Nov 2021 would have meant a ~48% drawdown on the account before any recovery.
  The start date was lucky. Early gains cushioned the 2022 losses.
- Costs: day-trading mode makes about 19 round trips per signal, so $5/RT costs $5,015 here.
  The no-schedule version pays about $132 to $265 total and finished highest in this sample.
- Not modeled: margin. Both modes hold through the overnight session, so overnight/initial margin applies.
  Check your broker's MNQ figure against $10k. Also not modeled: gap slippage beyond the fixed per-side assumption.

## Files
`rep10k_<mode>_min1_cost<x>_{summary.json,trades.csv,equity_daily.csv}`. Rebuild:

    python3 scripts/backtest.py data/mnq/mnq_30m_continuous.csv [--daytrading 0] [--fill close] --out <dir>/bt_<mode>
    python3 scripts/report.py <dir>/bt_<mode> data/mnq/mnq_30m_continuous.csv --account 10000 \
        --risk_pct 2 --compound 1 --policy min1 --cost_rt 2.5 --out <prefix>
