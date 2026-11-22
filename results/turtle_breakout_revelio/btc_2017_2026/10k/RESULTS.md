# Turtle Breakout on CME Bitcoin futures, $10,000 account: choosing the risk per signal

Backtest only. Run 2026-11-22. Same signals as `../RESULTS.md`: pure system (day-trading schedule off),
fills at the indicator's levels, Micro Bitcoin sizing (0.1 BTC, $0.10 per point, synthetic before 2021-05),
$7 per contract per round trip assumed costs. Contracts = floor(risk% of closed equity / (stop pts x $0.10));
0 contracts = signal skipped, so risk never exceeds the chosen percent.

## Historical path, by risk per signal

| risk | traded / 42 | end equity | CAGR | MTM max DD | days below a high | PF | CAGR / DD |
|---|---|---|---|---|---|---|---|
| 0.5% | 1 | $10,375 | 0.4% | -1.5% | 2,731 | - | 0.28 |
| 1% | 9 | $13,292 | 3.2% | -8.2% | 2,142 | 25.1 | 0.39 |
| 1.5% | 17 | $17,827 | 6.7% | -14.0% | 1,061 | 13.3 | 0.48 |
| 2% | 21 | $23,505 | 10.0% | -18.0% | 1,060 | 9.5 | 0.56 |
| 2.5% | 34 | $28,374 | 12.4% | -20.3% | 1,059 | 4.3 | 0.61 |
| 3% | 41 | $34,356 | 14.8% | -20.8% | 1,028 | 3.45 | 0.71 |
| 4% | 42 | $50,289 | 19.8% | -23.7% | 1,018 | 2.96 | 0.84 |
| 5% | 42 | $70,008 | 24.3% | -28.5% | 1,018 | 2.68 | 0.85 |
| 6% | 42 | $96,181 | 28.8% | -32.4% | 1,018 | 2.43 | 0.89 |
| 8% | 42 | $169,847 | 37.3% | -35.7% | 1,018 | 2.15 | 1.04 |
| 10% | 42 | $272,397 | 44.8% | -42.0% | 2025-07 to end, not recovered | 1.94 | 1.07 |

On one historical path more risk always looked better. That is what a sample with a +22.7R outlier does;
it is not a reason to pick 10%.

## The $10k problem: below about 3%, the account cannot take the signals
- Per-contract stop on MBT: median $440, widest $957. At 2% of $10,000 ($200) only narrow-stop signals fit.
- At 2%, 21 of 42 were skipped: every signal in 2021 and most from 2024 on, when bitcoin's price (and so
  its dollar ATR) was high. The traded half averaged +2.58R, the skipped half +0.03R. That gap is luck in
  which signals happened to have narrow stops, not something the rule could know. The 2% row's PF of 9.5
  comes from that selection.
- To take the widest stop at 2% you need about $47,800. At 4% every signal was taken only because equity
  had grown by the time the wide-stop signals came.

## Monte Carlo (`mc_risk_10k.json`, 20,000 paths of 42 signals resampled with replacement)
Three pools: all 42 signals, without the best 3, without the best 5 (testing whether it survives without
the outliers). Drawdowns here are closed-trade; the historical mark-to-market drawdown ran 7 to 15 points
deeper because open profit is given back before the trailing exit (see table above vs closed-trade).

| risk | all: median end | all: 95th pct DD | w/o best 5: median end | w/o best 5: P(end < $10k) | w/o best 5: 95th pct DD | w/o best 5: P(DD > 30%) |
|---|---|---|---|---|---|---|
| 2% | $19,784 | -6.5% | $10,753 | 15% | -8.2% | 0% |
| 3% | $30,058 | -12.9% | $12,014 | 6% | -10.0% | 0% |
| 4% | $45,529 | -20.1% | $13,148 | 7% | -17.7% | 0% |
| 5% | $63,744 | -26.6% | $13,466 | 12% | -26.2% | 2% |
| 6% | $87,826 | -32.9% | $13,243 | 15% | -34.3% | 12% |
| 8% | $149,079 | -43.6% | $13,060 | 28% | -47.9% | 52% |
| 10% | $236,414 | -52.9% | $13,139 | 33% | -58.9% | 81% |

Log-growth (Kelly) optimum on the observed R multiples: 33.5% with all signals, 19.5% without the best 3,
8% without the best 5. That it moves from 33.5% to 8% by removing five trades is the point: from 42
trades the edge's size is not known well enough to size toward it.

## Reading it
- Without its outliers the system's median end equity stops rising at about 4-5% and falls after that,
  while drawdown and the chance of ending below $10k keep rising. Above 5% you pay much more drawdown
  for growth that only exists if the outliers repeat.
- 3-4% is where every signal gets taken on $10k and the pessimistic cases stay out of 30% drawdowns
  (closed-trade). Expect about 25-30% mark-to-market at 4%, and close to 3 years below a high.
- That is above your 2% maximum. Raising it is a rule change: record it as a new variant
  (pure system, 4%), decide it before trading, and do not adjust it after a run of wins or losses.
- The other ways out of the gap: more capital (about $48k at 2%), or a smaller contract unit than MBT,
  if one with real liquidity is available to you. Check its contract specs before testing it.
