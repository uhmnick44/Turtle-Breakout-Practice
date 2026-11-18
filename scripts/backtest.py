"""Replicates the 'Turtle Breakout - Revelio' Pine Script v6 indicator on 30-minute candles.

Fill modes:
  level : the indicator's modeled fills (resting stop orders at the band / stop level; re-entry at the 18:00 open).
  close : alert-driven fills. Every event is acted on at the close of the candle that confirms it.
"""
import argparse, json, sys, math
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import pandas as pd, numpy as np

NY = ZoneInfo("America/New_York")
POINT_VALUE = 2.0  # MNQ: $2 per index point

p = argparse.ArgumentParser()
p.add_argument("csv"); p.add_argument("--out", required=True)
p.add_argument("--N", type=int, default=20); p.add_argument("--M", type=int, default=10)
p.add_argument("--atr", type=int, default=20); p.add_argument("--mult", type=float, default=2.0)
p.add_argument("--daytrading", type=int, default=1)
p.add_argument("--close", default="16:30"); p.add_argument("--open", default="18:00")
p.add_argument("--px", choices=["adj","raw"], default="adj")
p.add_argument("--fill", choices=["level","close"], default="level")
p.add_argument("--cost", type=float, default=0.0, help="$ per side per contract (commission+fees+slippage)")
a = p.parse_args()

df = pd.read_csv(a.csv)
sfx = "_adj" if a.px == "adj" else ""
O, H, L, C = (df[c+sfx].values for c in ["open","high","low","close"])
t_open = pd.to_datetime(df.time_open, utc=True).dt.tz_convert(NY)
bar_min = 30
t_close = t_open + pd.Timedelta(minutes=bar_min)
tl = list(t_open.dt.to_pydatetime())
tcl = list(t_close.dt.to_pydatetime())
ch, cm = map(int, a.close.split(":")); oh, om = map(int, a.open.split(":"))
CLOSE_M, OPEN_M = ch*60+cm, oh*60+om
ROLLOVER_M = 17*60

def ny_time(t, day_off, h, m):
    d = t.astimezone(NY)
    base = datetime(d.year, d.month, d.day, tzinfo=NY) + timedelta(days=day_off)
    return datetime(base.year, base.month, base.day, h, m, tzinfo=NY)

def deadline_for(t):
    mins = t.hour*60 + t.minute
    d = ny_time(t, 1 if mins >= CLOSE_M else 0, 0, 0)
    while d.weekday() in (5, 6):
        d = ny_time(d, 1, 0, 0)
    return ny_time(d, 0, ch, cm)

# ---- state ----
highs, lows = [], []
atr = None; atr_seed = 0.0; atr_count = 0
dHigh = dLow = dClose = prevClose = None
skip_first = True
session_prev = None
signal_long = False; held = False; stop = None; deadline = None
signal_marked = False
# fill tracking
open_fill = None  # dict for current held segment
cur_signal = None  # dict for current signal (breakout -> signal exit)
segments, signals = [], []
daily_bands = []

for i in range(len(df)):
    t, tc = tl[i], tcl[i]
    o, h, l, c = O[i], H[i], L[i], C[i]
    ny_min = t.hour*60 + t.minute
    dow = t.weekday()  # Mon=0 .. Sun=6
    session_start = ny_time(t, -1 if ny_min < ROLLOVER_M else 0, 17, 0)
    new_session = session_prev is None or session_start != session_prev
    session_prev = session_start
    # ---- daily aggregation (completed days only) ----
    if new_session:
        if dHigh is not None:
            if skip_first:
                skip_first = False
            else:
                highs.append(dHigh); highs = highs[-a.N:]
                lows.append(dLow); lows = lows[-a.M:]
                tr = (dHigh - dLow) if prevClose is None else max(dHigh - dLow, abs(dHigh - prevClose), abs(dLow - prevClose))
                if atr is None:
                    atr_seed += tr; atr_count += 1
                    if atr_count == a.atr:
                        atr = atr_seed / a.atr
                else:
                    atr = (atr * (a.atr - 1) + tr) / a.atr
                prevClose = dClose
        dHigh, dLow, dClose = h, l, c
    else:
        dHigh = max(dHigh, h); dLow = min(dLow, l); dClose = c
    entry_level = max(highs) if len(highs) == a.N else None
    exit_level = min(lows) if len(lows) == a.M else None
    allowed = (not a.daytrading) or ((ny_min < CLOSE_M or ny_min >= OPEN_M) and dow != 5
               and not (dow == 6 and ny_min < OPEN_M) and not (dow == 4 and ny_min >= CLOSE_M))
    if new_session and entry_level is not None:
        daily_bands.append((session_start, entry_level, exit_level, atr))
    if entry_level is None or exit_level is None or atr is None:
        continue

    # ---- signal logic (verbatim order from the Pine) ----
    was_long = signal_long
    breakout = (not was_long) and h > entry_level
    exit_event = False; signal_exit = None
    entry_event = reentry_event = close_event = False
    if breakout:
        signal_marked = False
        stop = max(entry_level, o) - a.mult * atr
        signal_long = True
        exit_event = l < stop
        cur_signal = dict(signal_time=t, signal_entry=max(entry_level, o), entry_level=entry_level, stop=stop, atr=atr,
                          exit_level_at_entry=exit_level, mae=0.0, mfe=0.0, segments=0, pnl_pts=0.0, cost=0.0)
    elif was_long:
        exit_event = l < max(stop, exit_level)
    if exit_event:
        signal_exit = min(o, max(stop, exit_level)) if was_long else stop
        signal_long = False
    if cur_signal is not None:
        e = cur_signal["signal_entry"]
        cur_signal["mae"] = min(cur_signal["mae"], l - e); cur_signal["mfe"] = max(cur_signal["mfe"], h - e)

    def close_segment(price, reason, when):
        global open_fill
        seg = open_fill; open_fill = None
        seg.update(exit_time=when, exit_price=price, exit_reason=reason)
        seg["pnl_pts"] = seg["exit_price"] - seg["entry_price"]
        segments.append(seg)
        cur_signal["segments"] += 1; cur_signal["pnl_pts"] += seg["pnl_pts"]; cur_signal["cost"] += 2*a.cost

    if a.daytrading and held and t >= deadline:
        close_segment(o, "missed_close", t)
        held = False; close_event = True
    if (not held) and allowed:
        entry_event = breakout
        reentry_event = was_long and o >= max(stop, exit_level)
        if entry_event or reentry_event:
            if not signal_marked:
                signal_marked = True
            modeled = max(entry_level, o) if breakout else o
            fill = modeled if a.fill == "level" else c
            open_fill = dict(signal_time=cur_signal["signal_time"], entry_time=t, entry_price=fill, modeled_entry=modeled,
                             kind="entry" if entry_event else "reentry", stop=stop)
            held = True
            deadline = deadline_for(t)
    if held:
        if exit_event:
            close_segment(signal_exit if a.fill == "level" else c, "signal_exit", tc)
            held = False
        elif a.daytrading and tc == deadline:
            close_segment(c, "scheduled_close", tc)
            held = False; close_event = True
    if exit_event and cur_signal is not None:
        cur_signal.update(signal_exit_time=tc, signal_exit_price=signal_exit, exit_reason="stop" if signal_exit <= stop + 1e-9 else "trail")
        signals.append(cur_signal); cur_signal = None

if open_fill is not None:
    close_segment(C[-1], "end_of_data", tcl[-1]); 
if cur_signal is not None:
    cur_signal.update(signal_exit_time=tcl[-1], signal_exit_price=C[-1], exit_reason="end_of_data"); signals.append(cur_signal)

seg = pd.DataFrame(segments); sig = pd.DataFrame(signals)
seg["pnl_usd"] = seg.pnl_pts * POINT_VALUE - 2*a.cost
sig["pnl_usd"] = sig.pnl_pts * POINT_VALUE - sig.cost
sig["risk_pts"] = sig.signal_entry - sig.stop
sig["r_multiple"] = sig.pnl_pts / sig.risk_pts
sig["year"] = pd.to_datetime(sig.signal_time, utc=True).dt.tz_convert(NY).dt.year
sig["hold_days"] = (pd.to_datetime(sig.signal_exit_time, utc=True) - pd.to_datetime(sig.signal_time, utc=True)).dt.total_seconds()/86400

def stats(pnl):
    pnl = np.asarray(pnl, dtype=float)
    w, lo = pnl[pnl > 0], pnl[pnl <= 0]
    eq = np.cumsum(pnl); dd = eq - np.maximum.accumulate(eq)
    streak = lambda cond: max((len(list(g)) for k, g in __import__("itertools").groupby(cond) if k), default=0)
    return dict(n=int(len(pnl)), win_rate=float(len(w)/len(pnl)) if len(pnl) else None,
                avg_win=float(w.mean()) if len(w) else None, avg_loss=float(lo.mean()) if len(lo) else None,
                expectancy=float(pnl.mean()) if len(pnl) else None, total=float(pnl.sum()),
                profit_factor=float(w.sum()/-lo.sum()) if len(lo) and lo.sum() < 0 else None,
                max_drawdown=float(dd.min()) if len(dd) else None,
                max_losing_streak=streak(pnl <= 0), max_winning_streak=streak(pnl > 0))

summary = dict(params=vars(a), bars=len(df), first_bar=str(tl[0]), last_bar=str(tl[-1]),
               signals_usd=stats(sig.pnl_usd), segments_usd=stats(seg.pnl_usd),
               by_year_usd={int(y): stats(g.pnl_usd) for y, g in sig.groupby("year")},
               exit_reasons=sig.exit_reason.value_counts().to_dict(),
               segment_exit_reasons=seg.exit_reason.value_counts().to_dict(),
               avg_risk_pts=float(sig.risk_pts.mean()), avg_risk_usd=float(sig.risk_pts.mean()*POINT_VALUE),
               avg_r=float(sig.r_multiple.mean()), avg_hold_days=float(sig.hold_days.mean()),
               avg_segments_per_signal=float(sig.segments.mean()),
               mae_pts_mean=float(sig.mae.mean()), mfe_pts_mean=float(sig.mfe.mean()))
seg.to_csv(a.out + "_segments.csv", index=False); sig.to_csv(a.out + "_signals.csv", index=False)
pd.DataFrame(daily_bands, columns=["session_start","entry_level","exit_level","atr"]).to_csv(a.out + "_bands.csv", index=False)
json.dump(summary, open(a.out + "_summary.json", "w"), indent=1, default=str)
print(json.dumps(summary, indent=1, default=str))
