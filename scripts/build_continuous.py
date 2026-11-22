import sys, os
import pandas as pd, numpy as np

src, outdir = sys.argv[1], sys.argv[2]
df = pd.read_parquet(src)
df["ts"] = pd.to_datetime(df.ts_event_ns, utc=True).dt.tz_convert("America/New_York")
# Trading day = 17:00 to 17:00 ET; label by the calendar date on which the day ENDS.
df["tday"] = (df.ts + pd.Timedelta(hours=7)).dt.normalize().dt.tz_localize(None)

# Expiry order from symbol: root + CME month letter + year.
# 1-digit year (MNQ files): Z2=2022 .. Z9=2019. 4-digit year: from label_expiry.py (MGC).
mcode = dict(zip("FGHJKMNQUVXZ", range(1, 13)))
NAME = os.environ.get("NAME", "mnq")
def key(sym):
    import re
    m, y = re.match(r"^[A-Z]+?([FGHJKMNQUVXZ])(\d+)$", sym).groups()
    y = int(y)
    if y < 10:
        y += 2020 if y < 9 else 2010
    return y*100 + mcode[m]
df["ckey"] = df.symbol.map(key)

dv = df.groupby(["tday","symbol","ckey"]).volume.sum().reset_index()
days = sorted(dv.tday.unique())
front = {}
cur = None
for i, d in enumerate(days):
    if i == 0:
        row = dv[dv.tday == d].sort_values("volume").iloc[-1]
        cur = (row.symbol, row.ckey); front[d] = cur[0]; continue
    prev = dv[dv.tday == days[i-1]]
    curv = prev[prev.symbol == cur[0]].volume.sum()
    nxt = prev[prev.ckey > cur[1]].sort_values("volume")
    if len(nxt) and nxt.iloc[-1].volume > curv:
        cur = (nxt.iloc[-1].symbol, nxt.iloc[-1].ckey)
    front[d] = cur[0]
fr = pd.Series(front, name="front"); fr.index.name = "tday"
rolls = fr[fr != fr.shift()].iloc[1:]
print("Rolls (first day on new contract):", file=sys.stderr)
# Adjustment: at each roll, offset = new.close - old.close on the last minute both traded on the day before the roll
offsets = []
for d, newsym in rolls.items():
    prevday = days[days.index(d)-1]
    oldsym = fr[prevday]
    a = df[(df.tday == prevday) & (df.symbol == oldsym)].set_index("ts_event_ns").close
    b = df[(df.tday == prevday) & (df.symbol == newsym)].set_index("ts_event_ns").close
    common = a.index.intersection(b.index)
    t = common.max()
    off = b[t] - a[t]
    offsets.append((d, oldsym, newsym, off))
    print(f"  {d.date()} {oldsym}->{newsym} gap {off:+.2f} at {pd.to_datetime(t, utc=True).tz_convert('America/New_York')}", file=sys.stderr)

cont = df.merge(fr.reset_index(), on="tday")
cont = cont[cont.symbol == cont.front].drop(columns=["front"]).sort_values("ts_event_ns")
# back-adjust: all data before roll k gets + sum of offsets from k onwards
adj = pd.Series(0.0, index=cont.index)
cum = 0.0
offs = pd.DataFrame(offsets, columns=["tday","old","new","off"])
for d, off in zip(offs.tday[::-1], offs.off[::-1]):
    cum += off
    adj[cont.tday < d] = cum
cont["adj"] = adj.values
assert cont.ts_event_ns.is_unique
for c in ["open","high","low","close"]:
    cont[c+"_adj"] = cont[c] + cont.adj
cont = cont.drop(columns=["ckey"])
cont.to_parquet(os.path.join(outdir, f"{NAME}_1m_continuous.parquet"), index=False)
offs.to_csv(os.path.join(outdir, f"{NAME}_rolls.csv"), index=False)
# diagnostics
dd = cont.groupby("tday").agg(bars=("close","size"), first=("ts","min"), last=("ts","max"))
print("days", len(dd), "bars/day median", dd.bars.median(), "min", dd.bars.min(), file=sys.stderr)
print("days with <900 bars:", file=sys.stderr)
print(dd[dd.bars < 900].to_string(), file=sys.stderr)
print("range", cont.ts.min(), cont.ts.max(), "rows", len(cont), file=sys.stderr)
