import sys, re, glob, os, io
import zstandard as zstd
from databento_dbn import DBNDecoder
import pandas as pd

rows = []
for d in sys.argv[1:]:
    for f in sorted(glob.glob(os.path.join(d, "*.ohlcv-1m.*.dbn.zst"))):
        sym = re.search(r"ohlcv-1m\.([A-Z0-9]+)\.dbn", os.path.basename(f))
        if not sym:
            continue  # spreads have a hyphen; skip
        sym = sym.group(1)
        raw = zstd.ZstdDecompressor().stream_reader(open(f, "rb")).read()
        dec = DBNDecoder()
        dec.write(raw)
        recs = dec.decode()
        n = 0
        for r in recs:
            if not hasattr(r, "open"):
                continue  # metadata record
            rows.append((r.ts_event, sym, r.instrument_id, r.open/1e9, r.high/1e9, r.low/1e9, r.close/1e9, r.volume))
            n += 1
        print(sym, n, file=sys.stderr)
df = pd.DataFrame(rows, columns=["ts_event_ns","symbol","instrument_id","open","high","low","close","volume"])
df = df.sort_values(["ts_event_ns","symbol"]).drop_duplicates()
df.to_parquet(sys.stdout.buffer if False else os.environ["OUT"], index=False)
print(len(df), df.ts_event_ns.min(), df.ts_event_ns.max(), file=sys.stderr)
