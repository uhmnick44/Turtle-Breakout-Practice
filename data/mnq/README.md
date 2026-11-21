# MNQ data

## Source
Databento, dataset GLBX.MDP3, schema ohlcv-1m, symbol MNQ.FUT (all outrights and
calendar spreads), two jobs: 2022-10-01 to 2025-10-01 and 2025-10-01 to 2026-10-20.
Raw DBN files are not committed (about 50 MB). They decode with `scripts/decode.py`.

## Files
- `mnq_30m_continuous.csv`  30-minute candles, continuous front-month series.
  `time_open` is the candle OPEN time in America/New_York. Columns `open..close`
  are unadjusted; `open_adj..close_adj` are back-adjusted (see below). `symbol`
  is the contract each candle came from.
- `mnq_rolls.csv`  roll dates and the price gap applied at each roll.

## Continuous series construction
- Trading day is 17:00 to 17:00 ET, matching the Pine Script.
- Roll rule: switch to the next contract on the first trading day after that
  contract's daily volume exceeds the current contract's. Decided from the
  prior day, so no lookahead. Rolls landed on the Tuesday of each expiry week.
- Back-adjustment: additive. At each roll the offset is new close minus old close
  on the last minute both contracts traded the day before the roll (16:59 ET).
  All earlier data is shifted up by the cumulative offsets. Every roll gap was
  positive (+116 to +300 points), so the unadjusted series contains a fake
  upward jump each quarter. Use the `_adj` columns for signal logic and P&L.
- Minutes with no trades are absent in the 1-minute source, so bar counts per
  day vary. Holiday early closes are present as shorter days.

## Rebuild
    python3 scripts/decode.py <dir1> <dir2>            # OUT=... env var for parquet path
    python3 scripts/build_continuous.py raw.parquet outdir
    python3 scripts/resample.py outdir/mnq_1m_continuous.parquet out.csv x raw.parquet

## Update 2026-11-21: extended to 2019-05
A third Databento job (GLBX-20261119-NUJUXSDTE3, CSV encoding, MNQ.FUT, requested from
2016-11-18 to 2023-09-30) was decoded with `scripts/decode_csv.py` and joined to the
earlier jobs. MNQ began trading on 2019-05-06, so the series now starts 2019-05-05 18:00 ET.
The overlap (2022-10-02 to 2023-09-29) matched the earlier DBN data on every candle.
`mnq_30m_continuous.csv` and `mnq_rolls.csv` now cover 2019-05 to 2026-10.
