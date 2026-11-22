# Turtle Breakout - Revelio on S&P 500 futures, 2016-10 to 2026-11

Backtest only. Not forward-tested, not live. Run 2026-11-22. Rules unchanged from the MNQ test.

## Setup
- Prices: ES continuous front month, 30-minute candles, back-adjusted (`data/es/README.md`).
- Rules: Pine defaults. N=20, M=10, ATR 20 Wilder, stop 2 ATR, long only, fills at modeled levels.
- Account $100,000. Risk 2% of closed equity per signal. Contracts = floor(2% / (stop pts x $/pt)),
  fixed at the breakout for every re-entry. Signals that cannot fit 1 contract in 2% are skipped.
- Costs per contract round trip (assumptions): MES $4 = $1.50 fees + 1 tick ($1.25) slippage each side;
  ES $30 = $5.00 fees + 1 tick ($12.50) each side. Paid on every round trip, including day-trading
  mode's scheduled 16:30 close and 18:00 re-entry.
- MES listed 2019-05. MES rows before that are ES prices at $5/pt (MES tracks ES; not identical fills).

## ES vs MES: the 2% rule only works on MES
| sizing | signals traded | avg risk taken |
|---|---|---|
| ES, skip if > 2% | 7 of 66 | 1.6% |
| ES, force 1 contract | 66 of 66 | 3.6% avg, over the 2% limit most of the time |
| MES, skip if > 2% | 66 of 66 | 1.8% avg, 2.0% max |

59 of 66 ES stops needed more than $2,000 for 1 contract. Everything below is MES.

## Main results (MES, with costs)

| metric | day-trading mode (Pine default) | pure system (hold overnight) |
|---|---|---|
| signals | 66 | 66 |
| ending equity | $137,144 | $161,375 |
| return / CAGR (10.1 yr) | +37.1% / 3.2% | +61.4% / 4.9% |
| win rate | 55% | 61% |
| avg win / avg loss | $2,034 / -$1,202 | $2,504 / -$1,491 |
| expectancy | $563 per signal | $930 per signal |
| profit factor | 2.03 | 2.58 |
| gross / costs | $68,240 / $31,096 | $62,803 / $1,428 |
| round trips per signal | 22 | 1 |
| max DD, mark-to-market | -$11,925 (-9.6%), Jan-Aug 2018 | -$11,580 (-8.7%), Jan-Aug 2018 |
| longest below prior high | 1,168 days (Sep 2020 - Nov 2023) | 602 days (Nov 2021 - Jul 2023) |
| worst losing streak | 4 | 4 |
| best trade | +$11,123 (Nov 2017, +6.6R) | +$13,542 |
| best 3 trades' share of net | 69% | 50% |
| net without best two | +$18,504 | +$37,995 |
| bootstrap 95% CI, expectancy | $9 to $1,188 (P<=0: 2.3%) | $248 to $1,692 (P<=0: 0.3%) |
| monthly Sharpe / months positive | 0.58 / 44% | 0.84 / 51% |
| exits | 59 trailing low, 7 initial stop | same |

Gross R per signal (no costs): +0.48R day-trading, +0.43R pure. Median +0.21R; 3 trades above +3R.

## Without costs (MES)
| case | end equity | return | PF | MTM DD |
|---|---|---|---|---|
| day-trading | $177,187 | +77.2% | 2.93 | -8.1% |
| pure | $163,600 | +63.6% | 2.66 | -8.6% |

Costs cut day-trading mode's net by 52% and the pure system's by 3%.

## By year, P&L by signal start year (MES, with costs)
| year | signals | DT P&L | pure P&L |
|---|---|---|---|
| 2016 (Nov-Dec) | 1 | +$1,370 | +$1,775 |
| 2017 | 7 | +$16,210 | +$21,103 |
| 2018 | 5 | -$1,854 | -$773 |
| 2019 | 6 | +$10,209 | +$12,413 |
| 2020 | 8 | -$179 | +$3,153 |
| 2021 | 10 | -$2,163 | -$603 |
| 2022 | 4 | +$170 | +$858 |
| 2023 | 5 | +$9,025 | +$11,802 |
| 2024 | 7 | +$8,072 | +$15,027 |
| 2025 | 8 | -$5,195 | -$2,881 |
| 2026 (to Nov 20) | 5 | +$1,478 | -$498 |

## Benchmark
Holding about $100k of S&P futures (9 MES from Oct 2016, rolled, back-adjusted): +$179,291,
max drawdown -35%. Holding 1 ES: +$199,212, max drawdown -37.5% of equity.
The strategy made a fifth (DT) to a third (pure) of that, with about a quarter of the drawdown.

## Reading it
- This is a second market with rules left unchanged after MNQ, which makes it a fair test of
  whether the result carries over. It did: PF above 2 on both. Both are US equity-index
  long-only in a rising decade, so they are not independent evidence.
- Long-only breakouts in a market that roughly tripled. Part of the result is beta, not edge.
- The right tail does the work: 3 trades above +3R, median trade +0.21R.
- Day-trading mode makes 22 round trips per signal; costs take more than half of its gross. The pure system is
  the cheaper version. Overnight and weekend gap risk is the trade-off, and is in the drawdown above.
- Slippage of 1 tick at the 16:30 close and the 18:00 re-entry is an assumption. Those are thinner times.
- Win rate is not the measure here: 4 losers in a row happened in both cases.

## Files
`rep_<es|mes>_<dt|pure>_<skip|min1>_cost<rt>_{summary.json,trades.csv,equity_daily.csv}`, raw signals
and segments in `bt_<dt|pure>_level_*`. Rebuild with `scripts/run_sp500.sh`.
