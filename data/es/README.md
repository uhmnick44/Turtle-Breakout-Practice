# ES data

## Source
Databento, dataset GLBX.MDP3, schema ohlcv-1m, ES.FUT (parent symbology: all outrights and
calendar spreads), CSV encoding, requested 2016-10-22 to 2026-11-21. Uploaded 2026-11-22 as three zips.
`condition.json` flags 27 of 3,207 days as "degraded" (Databento's label; not inspected further).
Raw files and parquet are not committed (about 70 MB). Rebuild with `scripts/run_sp500.sh`.

## Files
- `es_30m_continuous.csv`  30-minute candles, continuous front month, same schema as `data/mnq`.
- `es_rolls.csv`  40 rolls and the gap applied at each.

## Differences from the MNQ build
- Contract codes repeat every 10 years (ESZ6 = Dec 2016 and Dec 2026). `decode_csv.py` now gives
  each instrument_id a 2-digit year (ESZ16, ESZ26) from its first traded year.
- 78 prints stamped in the 17:00-17:59 ET halt were dropped (`DROP_HALT=1`). On Fridays each one
  would have created a one-bar "Saturday" session and polluted the 20-day high / ATR.
- Same volume roll rule and additive back-adjustment. Roll gaps: about -11 to +5 points through
  mid-2022, then +18 to +73 points.
- Series: 2016-10-23 18:00 ET to 2026-11-20 16:59 ET, 2,604 trading days.
