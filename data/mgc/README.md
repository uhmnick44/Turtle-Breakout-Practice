# MGC (Micro Gold) data

## Source
Databento, dataset GLBX.MDP3, schema ohlcv-1m, symbol MGC.FUT (parent), job
GLBX-20261122-FLQH67SQMY, 2016-10-22 to 2026-11-21, DBN + zstd, split by symbol.
All 60 outrights were used (G J M Q V Z, years 0-9); calendar spreads were ignored.
Raw DBN files are not committed.

## Files
- `mgc_30m_continuous.csv`  30-minute candles, continuous front month. Same columns as
  `data/mnq/mnq_30m_continuous.csv`. `symbol` uses 4-digit years, e.g. `MGCZ2026`.
- `mgc_rolls.csv`  roll dates and the gap applied at each roll.

## Construction
- The split files reuse 1-digit years: `MGCZ6` holds both Dec 2016 and Dec 2026 under different
  `instrument_id`s. `scripts/label_expiry.py` assigns each instrument its expiry year.
- Trading day 17:00 to 17:00 ET. Volume roll decided from the prior day, as for MNQ.
  Gold's volume rolls Feb -> Apr -> Jun -> Aug -> Dec -> Feb; Oct (V) was never the front.
- Additive back-adjustment at each roll. All 51 gaps were positive (+$2.00 to +$60.60),
  so unadjusted data has fake upward jumps. Use the `_adj` columns.
- One weekend print (Fri 2018-07-20 17:00 ET) was dropped so it cannot form a fake trading day.
- Liquidity: median 1-minute candles per day was about 700 (2016-17), 900 (2018), 1,226 (2019),
  and about 1,360-1,380 from 2020. Ten roll-eve days in 2017-18 had under 300.

## Rebuild
    OUT=raw.parquet python3 scripts/decode.py <unzipped dirs...>
    python3 scripts/label_expiry.py raw.parquet labeled.parquet
    NAME=mgc python3 scripts/build_continuous.py labeled.parquet outdir
    python3 scripts/resample.py outdir/mgc_1m_continuous.parquet data/mgc/mgc_30m_continuous.csv x
