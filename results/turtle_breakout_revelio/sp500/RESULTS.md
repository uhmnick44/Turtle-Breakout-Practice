# Turtle Breakout - Revelio on S&P 500 futures, 2016-10 to 2026-11

Backtest only. Not forward-tested, not live. Run 2026-11-22. Rules unchanged from the MNQ test.

## Setup
- Prices: ES continuous front month, 30-minute candles, back-adjusted (`data/es/README.md`).
- Rules: Pine defaults. N=20, M=10, ATR 20 Wilder, stop 2 ATR, long only, fills at modeled levels.
- Account $100,000. Risk 2% of closed equity per signal. Contracts = floor(2% / (stop pts x $/pt)),
  fixed at the breakout for every re-entry. Signals that cannot fit 1 contract in 2% are skipped.
- Costs per contract round trip (assumptions): MES $4 = $1.50 fees + 1 tick ($1.25) slippage each side;
  ES $30 = $5.00 fees + 1 tick ($12.50) each side. Paid on every round trip, including day-trading
  mode's scheduled 16:30 close and 18:00 re-entry, and once more for each quarterly roll a position
  is held through (sell expiring, buy next). Futures have no swap/overnight financing fee: carry is
  priced into the futures and is in the back-adjusted P&L.
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
| ending equity | $137,144 | $159,529 |
| return / CAGR (10.1 yr) | +37.1% / 3.2% | +59.5% / 4.7% |
| win rate | 55% | 61% |
| avg win / avg loss | $2,034 / -$1,202 | $2,460 / -$1,494 |
| expectancy | $563 per signal | $902 per signal |
| profit factor | 2.03 | 2.53 |
| gross / costs | $68,240 / $31,096 | $61,465 / $1,936 (incl. $512 for 20 rolls) |
| round trips per signal | 22 (flat at every roll, so no roll cost) | 1, plus 1 per roll held |
| max DD, mark-to-market | -$11,925 (-9.6%), Jan-Aug 2018 | -$11,592 (-8.8%), Jan-Aug 2018 |
| longest below prior high | 1,168 days (Sep 2020 - Nov 2023) | 602 days (Nov 2021 - Jul 2023) |
| worst losing streak | 4 | 4 |
| best trade | +$11,123 (Nov 2017, +6.6R) | +$13,486 |
| best 3 trades' share of net | 69% | 52% |
| net without best two | +$18,504 | +$36,229 |
| bootstrap 95% CI, expectancy | $9 to $1,188 (P<=0: 2.3%) | $232 to $1,656 (P<=0: 0.3%) |
| monthly Sharpe / months positive | 0.58 / 44% | 0.82 / 51% |
| exits | 59 trailing low, 7 initial stop | same |

Gross R per signal (no costs): +0.48R day-trading, +0.43R pure. Median +0.21R; 3 trades above +3R.

## Without costs (MES)
| case | end equity | return | PF | MTM DD |
|---|---|---|---|---|
| day-trading | $177,187 | +77.2% | 2.93 | -8.1% |
| pure | $163,600 | +63.6% | 2.66 | -8.6% |

Costs cut day-trading mode's net by 52% and the pure system's by 6% (roll costs included).

## Slippage at 2 ticks per side ($6.50 per MES round trip)
| case | end equity | return | PF |
|---|---|---|---|
| day-trading | $113,706 | +13.7% | 1.38 |
| pure | $157,346 | +57.3% | 2.50 |

## By year, P&L by signal start year (MES, with costs)
| year | signals | DT P&L | pure P&L |
|---|---|---|---|
| 2016 (Nov-Dec) | 1 | +$1,370 | +$1,746 |
| 2017 | 7 | +$16,210 | +$20,959 |
| 2018 | 5 | -$1,854 | -$857 |
| 2019 | 6 | +$10,209 | +$12,329 |
| 2020 | 8 | -$179 | +$3,141 |
| 2021 | 10 | -$2,163 | -$627 |
| 2022 | 4 | +$170 | +$858 |
| 2023 | 5 | +$9,025 | +$10,433 |
| 2024 | 7 | +$8,072 | +$14,962 |
| 2025 | 8 | -$5,195 | -$2,917 |
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

## Dashboard
https://claude.ai/artifact/Br4kVceaMqBmDYdk4atWKR (private until shared). Data exported by `scripts/export_sp500.py`.

## Files
`rep_<es|mes>_<dt|pure>_<skip|min1>_cost<rt>_{summary.json,trades.csv,equity_daily.csv}`, raw signals
and segments in `bt_<dt|pure>_level_*`. Rebuild with `scripts/run_sp500.sh`.

# $10,000 account, 10% risk per signal (MES, overnight, $4 per round trip + rolls)

Same 66 signals, same rules. Files: `rep10k_*`. Dashboard: https://claude.ai/artifact/Lrb2rKHRd352oHJe784xyi
(export: `python3 scripts/export_sp500.py results/turtle_breakout_revelio/sp500 data/es/es_30m_continuous.csv scripts <out> 10000 10 rep10k_`).

| metric | value |
|---|---|
| ending equity | $80,299 (+703%, 23.0% a year) |
| win rate / profit factor | 61% / 1.84 |
| avg win / avg loss | $3,843 / -$3,209 |
| net R per signal after costs | +0.41R, bootstrap 95% CI +0.13R to +0.73R |
| bootstrap 95% CI, $ expectancy | -$134 to +$2,369 (compounding: late large positions dominate) |
| max DD, mark-to-market | -$33,674 (-32.1%), Jan-Aug 2018 |
| worst month | -14.1% |
| longest below prior high | 603 days |
| risk taken | 9.3% average, 10.0% max; 2 to 17 MES |
| costs | $2,700, incl. $648 for 20 rolls |
| hold 1 MES (~$10.7k notional) | +$19,921, max DD -36.1% |

Profit factor falls from 2.53 (2%) to 1.84 here though R per trade is unchanged: dollar PF weights
each trade by its size, and the largest positions came late, including 2025's losses.

| variant ($10k, 10%) | end equity | return | PF | MTM DD |
|---|---|---|---|---|
| main case | $80,299 | +703% | 1.84 | -32.1% |
| overnight, no costs | $92,710 | +827% | 1.88 | -32.3% |
| overnight, 2 ticks slippage | $80,034 | +700% | 1.85 | -31.9% |
| day-trading, $4 | $34,770 | +248% | 1.54 | -34.3% |
| day-trading, no costs | $126,803 | +1,168% | 1.92 | -31.6% |
| day-trading, 2 ticks slippage | $15,632 | +56% | 1.23 | -38.2% |
| ES overnight, forced 1 contract (risk up to 32%) | $146,125 | +1,361% | 2.22 | -37.4% |

ES with a 10% limit trades nothing on $10,000: every stop needs more than $1,000 for one contract.

## Resampled drawdowns (main case net R, random order, 20,000 runs, closed trades only)
| risk | 4 losses in a row | median worst DD | bad case (5th pct) | P(DD <= -30%) | P(DD <= -50%) |
|---|---|---|---|---|---|
| 1% | -3.9% | -3.0% | -5.5% | 0% | 0% |
| 2% | -7.8% | -5.9% | -10.8% | 0% | 0% |
| 5% | -18.5% | -14.4% | -25.3% | 1.6% | 0% |
| 10% | -34.4% | -27.3% | -45.6% | 38.5% | 2.3% |
