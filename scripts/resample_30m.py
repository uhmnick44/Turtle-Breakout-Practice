"""1-minute continuous parquet -> 30-minute CSV in the format backtest.py reads.
Usage: python3 resample_30m.py continuous_1m.parquet out.csv"""
import sys, pandas as pd
c = pd.read_parquet(sys.argv[1])
c["ts"] = pd.to_datetime(c.ts_event_ns, utc=True).dt.tz_convert("America/New_York")
c = c.set_index("ts")
spec = {}
for px in ["", "_adj"]:
    spec.update({f"open{px}": (f"open{px}", "first"), f"high{px}": (f"high{px}", "max"),
                 f"low{px}": (f"low{px}", "min"), f"close{px}": (f"close{px}", "last")})
spec.update(volume=("volume", "sum"), symbol=("symbol", "first"))
r = c.resample("30min", label="left", closed="left").agg(**spec).dropna(subset=["open"]).reset_index().rename(columns={"ts": "time_open"})
r["time_open"] = r.time_open.dt.strftime("%Y-%m-%d %H:%M:%S%z")
r.to_csv(sys.argv[2], index=False)
print(len(r), r.time_open.iloc[0], r.time_open.iloc[-1])
