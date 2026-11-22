"""Decode Databento ohlcv-1m CSV (pretty_px, pretty_ts, map_symbols) .csv.zst files
for outright contracts into the same parquet schema decode.py produces.
Usage: OUT=path.parquet python3 decode_csv.py dir1 [dir2 ...]"""
import sys, os, re, glob, io
import zstandard as zstd, pandas as pd
frames = []
for d in sys.argv[1:]:
    for f in sorted(glob.glob(os.path.join(d, "*.ohlcv-1m.*.csv.zst"))):
        m = re.search(r"ohlcv-1m\.([A-Z0-9]+)\.csv\.zst$", os.path.basename(f))
        if not m:
            continue  # calendar spreads contain a hyphen
        with open(f, "rb") as fh:
            df = pd.read_csv(io.TextIOWrapper(zstd.ZstdDecompressor().stream_reader(fh)))
        df = df[df.rtype == 33]
        df["ts_event_ns"] = pd.to_datetime(df.ts_event, utc=True).astype("int64")
        frames.append(df[["ts_event_ns","symbol","instrument_id","open","high","low","close","volume"]])
        print(m.group(1), len(df), file=sys.stderr)
out = pd.concat(frames)
# Contract codes repeat every 10 years (ESZ6 = Dec 2016 and Dec 2026). Each instrument_id is one
# contract, so give it a 2-digit year: the first year >= its first traded year ending in that digit.
first_year = pd.to_datetime(out.groupby("instrument_id").ts_event_ns.min(), utc=True).dt.year
def full(sym, iid):
    d, y0 = int(sym[-1]), int(first_year[iid])
    y = y0 + (d - y0 % 10) % 10
    return f"{sym[:-1]}{y % 100:02d}"
names = {(s, i): full(s, i) for s, i in out[["symbol","instrument_id"]].drop_duplicates().itertuples(index=False)}
out["symbol"] = [names[k] for k in zip(out.symbol, out.instrument_id)]
out = out.sort_values(["ts_event_ns","symbol"]).drop_duplicates()
out.to_parquet(os.environ["OUT"], index=False)
print(len(out), pd.to_datetime(out.ts_event_ns.min(), utc=True), pd.to_datetime(out.ts_event_ns.max(), utc=True), file=sys.stderr)
