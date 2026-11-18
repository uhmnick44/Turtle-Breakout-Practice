# Turtle Breakout - Revelio on MNQ, backtest (not forward, not live)

Run on 2026-11-18. Data: MNQ 30-minute continuous, back-adjusted, 2022-10-02 to
2026-10-20 (see `data/mnq/README.md`). One contract, $2 per point. No commissions,
fees or slippage unless stated. Rules exactly as in the Pine Script defaults:
N=20, M=10, ATR 20 Wilder, stop 2 ATR, day-trading close 16:30 / re-enter 18:00.

`scripts/backtest.py` replicates the indicator's state machine bar by bar.
Verified invariants: every entry above the entry band, scheduled closes only at
16:30 Mon-Fri, re-entries only at 18:00, no fills inside the 16:30-18:00 break,
holiday early-closes produce the same "missed close" behaviour as the Pine.

## Headline (one signal = one breakout to its signal exit)

| run | fills | n | win rate | avg win | avg loss | expectancy | PF | total | max DD | worst streak |
|---|---|---|---|---|---|---|---|---|---|---|
| pure system | at level | 30 | 47% | $1,785 | -$1,049 | $273 | 1.49 | $8,197 | -$5,152 | 4 |
| day-trading mode | at level | 30 | 47% | $1,844 | -$1,077 | $286 | 1.50 | $8,575 | -$5,271 | 4 |
| day-trading mode | at candle close (alert-driven) | 30 | 43% | $1,809 | -$979 | $229 | 1.41 | $6,882 | -$4,855 | 4 |
| pure system | at level, UNADJUSTED prices | 29 | 52% | $1,979 | -$1,253 | $419 | 1.69 | $12,139 | -$4,374 | 4 |

Average initial risk per signal: 699 points = $1,398 per MNQ contract.
Average result: +0.19 R. Average hold: 24 days. Time in market: 47%.
Day-trading mode averages 18 round trips per signal.

## What the sample actually says

- 30 signals in four years. Bootstrap 95% interval on expectancy (day-trading
  mode): -$410 to +$1,172 per signal. Probability the true mean is <= 0: about 25%.
- The best signal (Apr-Jun 2026, +$9,794) is 114% of the total. Remove it and the
  system is net negative over the sample. Three signals account for all the profit.
- R-multiples: 16 losers between -0.1R and -1.0R, 12 winners between +0.3R and
  +1.6R, and two at +4.4R and +4.5R. This is the normal shape of a trend-following
  system: the edge, if any, is entirely in the right tail, so skipping signals is
  the fastest way to remove it.
- Only 4 of 30 exits were the 2 ATR stop. 26 were the 10-day trailing low.
- Year by year (day-trading mode, $): 2022 -2,911 (3), 2023 +6,179 (6),
  2024 -1,139 (9), 2025 +97 (7), 2026 +6,350 (5).

## Schedule and execution findings

- Being flat 16:30-18:00 and over weekends changed almost nothing (+$378 over
  four years) but adds ~18 round trips per signal. At $2.50 all-in per round trip
  that costs $45 per signal; at $5.00, $90. Not fatal, but it is pure cost.
- Day-trading mode still holds overnight 18:00 to 16:30.
- Acting on alerts at candle close instead of resting orders at the level cost
  about $56 per signal, roughly 20% of the gross expectancy.
- The unadjusted series overstates the result by about $3,900 because every
  quarterly roll gap was positive. Do not trust a TradingView backtest of this
  indicator on an unadjusted continuous symbol.

## Not tested
Position sizing, pyramiding, the Turtle "skip after a winning breakout" filter,
shorts, other N/M values, ES/MES. The Pine's "video" result is unknown to us.

## Sized run: $100,000 account, 5% risk per signal (added 2026-11-18)

`scripts/size.py`. Contracts = floor(risk dollars / (initial stop distance x $2)),
decided at the breakout candle from the indicator's modeled entry and stop.
Whole-contract rounding means actual risk averaged 4.3% (compounding) or 3.8% (fixed $5,000).
No costs. Files: `sized_*_5pct_{compound,fixed}.{csv,json}`.

| run | sizing | contracts | ending equity | return | expectancy/signal | PF | max DD (closed trades) | worst loss | best win | net without best |
|---|---|---|---|---|---|---|---|---|---|---|
| day-trading, at level | 5% compounding | 2-6 | $125,384 | +25.4% | $846 | 1.43 | -$19,174 (-15.1%) | -$6,345 | +$19,678 | +$5,704 |
| day-trading, at level | fixed $5,000 | 1-5 | $123,726 | +23.7% | $791 | 1.45 | -$19,189 (-15.5%) | -$5,076 | +$19,678 | +$4,047 |
| pure, at level | 5% compounding | 2-6 | $125,791 | +25.8% | $860 | 1.43 | -$18,600 (-14.5%) | -$6,213 | +$19,520 | +$6,270 |
| pure, at level | fixed $5,000 | 1-5 | $124,894 | +24.9% | $830 | 1.49 | -$16,394 (-13.2%) | -$4,970 | +$19,520 | +$5,374 |
| day-trading, alert fills | 5% compounding | 2-6 | $122,126 | +22.1% | $738 | 1.39 | -$20,208 (-15.7%) | -$6,432 | +$20,620 | +$1,509 |
| day-trading, alert fills | fixed $5,000 | 1-5 | $120,884 | +20.9% | $696 | 1.41 | -$20,960 (-16.7%) | -$5,764 | +$20,620 | +$265 |

Roughly +25% over four years is about 5.8% a year compounded, against a 15%
closed-trade drawdown. The drawdown is from the Aug 2025 to Jan 2026 stretch:
five losers in six signals, each about -4% of equity. Max drawdown is measured on
closed trades; open-trade drawdown is deeper by up to one stop distance.
