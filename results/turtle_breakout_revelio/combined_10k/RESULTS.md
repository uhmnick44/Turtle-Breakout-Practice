# Turtle Breakout - Revelio: three $10,000 accounts on a common window

Backtest only. Not forward-tested, not live. Run 2026-11-22.
Sheet: https://claude.ai/artifact/PHTLAhYwPqponSLdthrSDL

Cases (each re-run unchanged from its own branch, day-trading schedule off, level fills):
- Bitcoin: MBT, 10% of closed equity, skip, $7 RT (`claude/turtle-break-backtest-0mczq8`, `rep_mbt_pure_level_cost7_risk10`)
- S&P 500: MES, 10% of closed equity, skip, $4 RT + rolls (`claude/gallant-einstein-ls8ow1`, `rep10k_mes_pure_skip_cost4`)
- MNQ: 1 contract on every signal, $2.50 RT (`claude/tender-archimedes-tdtqme`, `rep10k_pure_level_min1_cost2.5`)

Common window 2019-05-05 to 2026-10-20 (7.47 years), the only span where all three have data.
Each account starts at $10,000 on 2019-05-05; signals that began earlier are dropped (BTC 4, S&P 15).

| | Combined ($30k) | Bitcoin | S&P 500 | MNQ |
|---|---|---|---|---|
| ending equity | $196,657 | $149,930 | $23,590 | $23,138 |
| CAGR | 28.6% | 43.7% | 12.2% | 11.9% |
| trades | 141 | 38 | 50 | 53 |
| win rate / PF | 55% / 1.86 | 50% / 1.94 | 60% / 1.60 | 55% / 1.57 |
| expectancy (R, before costs) | +0.51 | +1.18 | +0.29 | +0.24 |
| max DD, mark-to-market | -35.1% | -41.6% | -29.2% | -39.9% |

Bitcoin is 84% of combined net profit. Combined was still in drawdown at the end (peak 2025-07-14).

Rebuild: `python3 scripts/combined_window_run.py <dir holding the three branch worktrees>` (expects the MNQ pure
signals at `<dir>/work/mnq_bt_pure_level_*`, from `scripts/backtest.py --daytrading 0`), then
`python3 scripts/combined_stats.py <dir>/work/rep <out.json>` and `python3 scripts/combined_r_bootstrap.py <dir>/work/rep <out.json>`.
