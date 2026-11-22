# Turtle Breakout on MNQ: $10,000 account, 10% risk, after costs

Backtest only. Not forward-tested, not live. Run 2026-11-22. Same signals as `../2019_2026`
(MNQ 30-minute, May 2019 to October 2026, Pine defaults, day-trading mode, level fills).

## Cost, roll and margin model (`scripts/report.py`)
| item | per contract, per side | basis |
|---|---|---|
| broker commission and clearing | $0.63 | assumption |
| CME exchange fee | $0.35 | Interactive Brokers' MNQ pass-through rate ($0.353) |
| NFA fee | $0.02 | NFA rate before July 2026 ($0.01 since) |
| slippage | 1 tick = $0.50 | assumption; 2 ticks in the stress run |

$3.00 per round trip. Rolls: prices are back-adjusted, and any position held across a roll
pays a close and a reopen. Margin: $4,021 per contract overnight at 29,904 (a broker's listed
MNQ initial margin), scaled by price over time; contracts are capped at floor(equity / margin).
No run hit the margin cap and no open position fell below maintenance (margin / 1.1).

## Main case: 10% of equity, skip signals that need more than 10% for one contract
| metric | value |
|---|---|
| ending equity | $13,431 (+34.3%, 4.0% a year) |
| signals traded / skipped | 36 / 17 |
| profit before costs / costs | $5,729 / $2,298 (40% of gross) |
| round trips per contract | 766 (day-trading schedule), 0 roll trades |
| win rate, PF | 58%, 1.27 |
| expectancy | +$95 per traded signal, +0.26R |
| max drawdown, mark-to-market | -$5,865 (-31.0%) |
| longest below a prior high | 832 days |
| net without best trade | -$301 |
| bootstrap 95% interval, expectancy | -$231 to +$442; P(mean <= 0) 29.5% |

The April 2026 signal (+4.48R) was skipped: one contract needed $2,184 of risk.

## Variants ($10,000 start, all with costs unless stated)
| variant | traded | ending | return | PF | max DD | costs | largest risk |
|---|---|---|---|---|---|---|---|
| main case | 36 | $13,431 | +34.3% | 1.27 | -31.0% | $2,298 | 9.9% |
| 10%, take 1 contract when the stop is wider | 53 | $20,149 | +101.5% | 1.42 | -46.4% | $3,192 | 21.2% |
| no schedule, 10%, skip | 38 | $13,773 | +37.7% | 1.25 | -34.9% | $165 | 9.7% |
| no schedule, take 1 contract | 53 | $24,921 | +149.2% | 1.63 | -37.9% | $237 | 15.0% |
| alert-driven fills | 31 | $13,405 | +34.1% | 1.33 | -30.3% | $2,109 | 9.9% |
| $1.50 a side + 2 ticks | 34 | $13,928 | +39.3% | 1.36 | -31.4% | $3,805 | 10.0% |
| no costs | 34 | $13,799 | +38.0% | 1.30 | -35.9% | $0 | 10.0% |
| 5% risk, skip | 3 | $10,680 | +6.8% | n/a | -5.9% | $141 | 4.7% |
| 2% risk, skip | 0 | $10,000 | 0% | n/a | n/a | $0 | n/a |

Holding 1 MNQ the whole time on $10,000: +$36,901, worst drawdown -43.6% (daily closes).

## Reading it
- At this size the result depends on which signals happen to fit under 10% at that moment.
  The no-cost and higher-cost runs ended above the main case only because they traded a
  different set of signals. Treat the main number as one outcome, not as the rules' edge.
- 2% risk can't trade at all: the smallest stop in the sample needed $365 per contract.
- Taking 1 contract on every signal means risking up to 21% (15% without the schedule) on a
  single trade.
- The day-trading schedule causes almost all costs. Without it costs fall from $2,298 to $165.
