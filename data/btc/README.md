# CME Bitcoin futures data

## Source
Databento job GLBX-20261122-Q7J6YQTGQS: dataset GLBX.MDP3, schema ohlcv-1m, parent symbol
BTC.FUT, requested 2016-10-21 to 2026-11-20, split by symbol, uploaded as two zips.
CME Bitcoin futures began trading on 2017-12-17 (18:00 ET), so the data starts there:
about 8.9 years, not 10. Raw DBN files are not committed. Calendar spreads are ignored.

Contract: 5 bitcoin, minimum tick $5 per bitcoin = $25 per contract. Micro Bitcoin (MBT):
0.1 bitcoin, $0.50 per tick, listed 2021-05-03. MBT has the same index and expiry calendar
but its own order book; it is not in this data. (CME contract pages, checked 2026-11-22.)

## Files
- `btc_30m_continuous.csv`: 30-minute candles, same columns as `data/mnq/mnq_30m_continuous.csv`.
  `time_open` is the candle open in America/New_York; `*_adj` columns are back-adjusted.
- `btc_rolls.csv`: each roll, the contracts, the gap, and the minute it was measured.

## Continuous series construction (differs from MNQ)
- Roll: calendar, 5 trading days before each contract's last trading day (last Friday of the
  month). The MNQ volume roll would roll BTC on expiry day itself, because volume stays in the
  front month until final settlement at 11:00 ET; that leaves the expiry afternoon empty.
- Back-adjustment: additive, at the last minute both contracts traded on the day before the roll.
  106 rolls, gaps -275 to +1,000 points, cumulative +26,995. Early adjusted prices are therefore
  about 27,000 points above the traded prices. Point differences (ATR, stops, P&L) are unaffected;
  percentages computed from `_adj` prices are not meaningful.
- Schedule: from late May 2026 the data has weekend and 17:00-18:00 ET candles (CME 24/7 crypto
  trading). They are dropped (3,720 weekend + 735 daily-break one-minute candles) so that a
  trading day means Sun 18:00 to Fri 17:00 ET for the whole sample.
- Early years are thin: minutes with no trades are absent, 514 of 2,307 days have fewer than
  600 one-minute candles.

## Rebuild
    OUT=raw.parquet python3 scripts/decode.py <unzipped dir 1> <unzipped dir 2>
    python3 scripts/build_continuous_btc.py raw.parquet outdir
    python3 scripts/resample_30m.py outdir/btc_1m_continuous.parquet data/btc/btc_30m_continuous.csv
