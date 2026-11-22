"""Give each contract a 4-digit expiry year: MGCZ6 -> MGCZ2016 or MGCZ2026.
Databento's split_symbols files reuse the 1-digit CME code for contracts ten years apart
(e.g. MGCZ6 holds both Dec 2016 and Dec 2026), so they are separated by instrument_id.
Expiry year = smallest year >= the year of the instrument's last candle whose last digit matches.
Usage: python3 label_expiry.py in.parquet out.parquet"""
import sys, re
import pandas as pd
src, dst = sys.argv[1:3]
df = pd.read_parquet(src)
last = df.groupby(["symbol", "instrument_id"]).ts_event_ns.max()
lab = {}
for (sym, iid), t in last.items():
    root, m, d = re.match(r"^([A-Z]+?)([FGHJKMNQUVXZ])(\d)$", sym).groups()
    y = pd.to_datetime(t, utc=True).year
    while y % 10 != int(d): y += 1
    lab[(sym, iid)] = f"{root}{m}{y}"
df["symbol"] = [lab[k] for k in zip(df.symbol, df.instrument_id)]
assert df.groupby("symbol").instrument_id.nunique().max() == 1
df.to_parquet(dst, index=False)
print(df.groupby("symbol").ts_event_ns.agg(["min", "max", "size"]).assign(
    min=lambda x: pd.to_datetime(x["min"]).dt.date, max=lambda x: pd.to_datetime(x["max"]).dt.date).to_string(), file=sys.stderr)
