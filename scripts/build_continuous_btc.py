"""Continuous front-month series for CME Bitcoin futures (BTC, monthly contracts).
Same method as build_continuous.py: 17:00-17:00 ET trading day, calendar roll 5 trading days
before each contract's last trading day, additive back-adjustment at the last common minute.
Contract year is inferred from the single-digit code and the contract's first traded day.
Usage: python3 build_continuous_btc.py raw.parquet outdir"""
import sys, os
import pandas as pd, numpy as np
src, outdir = sys.argv[1], sys.argv[2]
df = pd.read_parquet(src)
df = df[~df.symbol.str.contains("-")]
df["ts"] = pd.to_datetime(df.ts_event_ns, utc=True).dt.tz_convert("America/New_York")
# Keep the classic CME schedule (Sun 18:00 to Fri 17:00 ET, daily break 17:00-18:00) for the whole sample.
# CME BTC data from late May 2026 also has weekend and daily-break candles (24/7 crypto trading);
# keeping them would change what a "day" is partway through the test.
dow, hr = df.ts.dt.dayofweek, df.ts.dt.hour
weekend = (dow == 5) | ((dow == 6) & (hr < 18)) | ((dow == 4) & (hr >= 17))
brk = hr == 17
print("dropped weekend 1m bars", int(weekend.sum()), "daily-break 1m bars", int((brk & ~weekend).sum()))
df = df[~(weekend | brk)]
df["tday"] = (df.ts + pd.Timedelta(hours=7)).dt.normalize().dt.tz_localize(None)
MONTH = dict(zip("FGHJKMNQUVXZ", range(1, 13)))
first_year = df.groupby("symbol").ts.min().dt.year
df_first = df.groupby("symbol").tday.min()
def key(sym):
    m, d = MONTH[sym[3]], int(sym[4]); y0 = first_year[sym]
    y = y0 - y0 % 10 + d
    if y < y0: y += 10
    return y * 100 + m
ckeys = {s: key(s) for s in df.symbol.unique()}
assert len(set(ckeys.values())) == len(ckeys), "two symbols map to the same expiry"
df["ckey"] = df.symbol.map(ckeys)
# Roll rule: hold the nearest contract until 5 trading days before its last trading day, then the next.
# Last trading days follow CME's published calendar (last Friday of the month), so no lookahead.
# A volume roll lands on expiry day for BTC (liquidity stays in the front month to the end), which
# would leave the expiry afternoon without candles after the 11:00 ET final settlement.
ROLL_DAYS = 5
days = sorted(df.tday.unique()); idx = {d: i for i, d in enumerate(days)}
last_day = df.groupby("symbol").tday.max()
# Contracts still trading at the end of the data: use the last Friday of the contract month.
def last_friday(k):
    y, m = divmod(k, 100); d = pd.Timestamp(y, m, 1) + pd.offsets.MonthEnd(0)
    return d - pd.Timedelta(days=(d.weekday() - 4) % 7)
for s_ in last_day.index:
    if last_day[s_] == days[-1]:
        lf = last_friday(ckeys[s_]); later = [d for d in days if d <= lf]
        idx.setdefault(lf, idx[later[-1]] + int(np.busday_count(later[-1].date(), lf.date())))
        last_day[s_] = lf
order = sorted(ckeys, key=ckeys.get)
front = {}
for d in days:
    i = idx[d]
    cands = [s for s in order if idx[last_day[s]] - i >= ROLL_DAYS and df_first[s] <= d]
    front[d] = cands[0]
fr = pd.Series(front, name="front"); fr.index.name = "tday"
rolls = fr[fr != fr.shift()].iloc[1:]
offsets = []
for d, newsym in rolls.items():
    prevday = days[days.index(d) - 1]; oldsym = fr[prevday]
    a = df[(df.tday == prevday) & (df.symbol == oldsym)].set_index("ts_event_ns").close
    b = df[(df.tday == prevday) & (df.symbol == newsym)].set_index("ts_event_ns").close
    common = a.index.intersection(b.index); t = common.max()
    offsets.append((d, oldsym, newsym, b[t] - a[t], str(pd.to_datetime(t, utc=True).tz_convert("America/New_York"))))
offs = pd.DataFrame(offsets, columns=["tday", "old", "new", "off", "at"])
cont = df.merge(fr.reset_index(), on="tday")
cont = cont[cont.symbol == cont.front].drop(columns=["front"]).sort_values("ts_event_ns")
adj = pd.Series(0.0, index=cont.index); cum = 0.0
for d, off in zip(offs.tday[::-1], offs.off[::-1]):
    cum += off; adj[cont.tday < d] = cum
cont["adj"] = adj.values
assert cont.ts_event_ns.is_unique
for c in ["open", "high", "low", "close"]: cont[c + "_adj"] = cont[c] + cont.adj
cont.drop(columns=["ckey"]).to_parquet(os.path.join(outdir, "btc_1m_continuous.parquet"), index=False)
offs.to_csv(os.path.join(outdir, "btc_rolls.csv"), index=False)
dd = cont.groupby("tday").agg(bars=("close", "size"))
print("rolls", len(offs), "gap sum", round(offs.off.sum(), 1), "min/max gap", offs.off.min(), offs.off.max())
print("days", len(dd), "bars/day median", dd.bars.median(), "days <600 bars", int((dd.bars < 600).sum()))
print("min adj low", cont.low_adj.min(), "range", cont.ts.min(), cont.ts.max(), "rows", len(cont))
