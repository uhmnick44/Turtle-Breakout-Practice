import sys, pandas as pd
src, out30, out_sanity = sys.argv[1:4]
raw = pd.read_parquet(sys.argv[4]); raw["ts"] = pd.to_datetime(raw.ts_event_ns, utc=True).dt.tz_convert("America/New_York")
raw["tday"] = (raw.ts + pd.Timedelta(hours=7)).dt.normalize().dt.tz_localize(None)
v = raw[(raw.tday >= "2022-12-06") & (raw.tday <= "2022-12-16") & raw.symbol.isin(["MNQZ2","MNQH3"])].groupby(["tday","symbol"]).volume.sum().unstack()
print(v.to_string())
c = pd.read_parquet(src)
c["ts"] = pd.to_datetime(c.ts_event_ns, utc=True).dt.tz_convert("America/New_York")
c = c.set_index("ts")
def agg(px):
    o = {f"open{px}":("open"+px,"first"), f"high{px}":("high"+px,"max"), f"low{px}":("low"+px,"min"), f"close{px}":("close"+px,"last")}
    return o
spec = {**agg(""), **agg("_adj"), "volume":("volume","sum"), "symbol":("symbol","first")}
# 1-min bars are stamped by open time; a 30m bar [t, t+30) contains them.
r = c.resample("30min", label="left", closed="left").agg(**spec).dropna(subset=["open"])
r = r.reset_index().rename(columns={"ts":"time_open"})
r["time_open"] = r.time_open.dt.strftime("%Y-%m-%d %H:%M:%S%z")
for col in ["open","high","low","close","open_adj","high_adj","low_adj","close_adj"]:
    r[col] = r[col].round(2)
r.to_csv(out30, index=False)
print(len(r), r.time_open.iloc[0], r.time_open.iloc[-1])
print(r.head(3).to_string()); print(r.tail(3).to_string())
