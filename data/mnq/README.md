# MNQ data

Drop raw files here. Do not edit them by hand after export.

Preferred: intraday candles (1, 5, 15 or 30 minute), one row per candle,
CSV with a header. Columns in any order, any reasonable names:

    timestamp, open, high, low, close, volume

Please note in this file, or in the commit message:

- timezone of the timestamp column (UTC, Chicago, New York, or exchange)
- whether timestamp is candle OPEN time or candle CLOSE time
- continuous contract or a specific expiry, and how rollovers were handled
- source (TradingView export, broker, data vendor)
- candle size

Daily bars also work for the pure system, but the day-trading schedule
variant needs intraday data.
