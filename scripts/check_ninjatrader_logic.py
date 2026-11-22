"""Python replica of strategies/turtle_breakout_revelio/ninjatrader/TurtleBreakoutRevelio.cs order flow, compared with backtest.py signals.
Usage: python3 check_ninjatrader_logic.py <30m bars csv> <bt_pure_level_signals.csv> <tick size>"""
import sys, pandas as pd, numpy as np
from datetime import timedelta
csv, sigcsv, TICK = sys.argv[1], sys.argv[2], float(sys.argv[3])
import math
TA = lambda x: (math.floor(x / TICK + 1e-9) + 1) * TICK
TB = lambda x: (math.ceil(x / TICK - 1e-9) - 1) * TICK
N, M, AL, K = 20, 10, 20, 2.0
df = pd.read_csv(csv); O, H, L, C = (df[c + "_adj"].values for c in ["open", "high", "low", "close"])
t_open = pd.to_datetime(df.time_open, utc=True).dt.tz_convert("America/New_York").dt.tz_localize(None)  # naive New York clock, like the C# code
highs, lows = [], []; atr = None; seed = 0; cnt = 0; prev = None
dH = dL = dC = None; cur = None; done = False; skip = True
sig_long = False; stop = None
pos = False; entry_px = None; order = None  # ('stop', level) or ('mkt',)
xorder = None; trades = []; ent_t = None
def complete():
    global skip, atr, seed, cnt, prev, highs, lows
    if skip: skip = False; return
    highs = (highs + [dH])[-N:]; lows = (lows + [dL])[-M:]
    tr = dH - dL if prev is None else max(dH - dL, abs(dH - prev), abs(dL - prev))
    if atr is None:
        seed += tr; cnt += 1
        if cnt == AL: atr = seed / AL
    else: atr = (atr * (AL - 1) + tr) / AL
    prev = dC
for i in range(len(df)):
    o, h, l, c = O[i], H[i], L[i], C[i]; to = t_open.iloc[i]
    # ---- intrabar fills of orders placed at the previous close ----
    if not pos and order:
        if order[0] == 'mkt': pos, entry_px = True, o
        elif h >= order[1]: pos, entry_px = True, max(order[1], o)
        if pos:
            ent_t = to; lvl = max(highs) if len(highs) == N else entry_px
            if not sig_long: stop_prov = max(lvl, entry_px) - K * atr
            else: stop_prov = stop
            act = TB(max(stop_prov, min(lows)))
            if l <= act:  # protective stop hit in the fill candle (order of prices inside a candle is unknown)
                trades.append((ent_t, to, entry_px, min(o, act) if False else act)); pos = False
        order = None
    elif pos and xorder is not None:
        if xorder[0] == 'mkt': trades.append((ent_t, to, entry_px, o)); pos = False
        elif l <= xorder[1]: trades.append((ent_t, to, entry_px, min(o, xorder[1]))); pos = False
        xorder = None
    # ---- candle close ----
    sess = (to.normalize() - timedelta(days=1)) if to.hour < 17 else to.normalize()
    sess_end = sess + timedelta(days=1, hours=17); tc = to + timedelta(minutes=30)
    if sess != cur:
        if dH is not None and not done: complete()
        dH, dL, dC = h, l, c; cur = sess; done = False
    else: dH = max(dH, h); dL = min(dL, l); dC = c
    ready = len(highs) == N and len(lows) == M and atr is not None
    if ready:
        el, xl = max(highs), min(lows); was = sig_long; brk = (not was) and h > el; ex = False
        if brk: stop = max(el, o) - K * atr; sig_long = True; ex = l < stop
        elif was: ex = l < max(stop, xl)
        if ex: sig_long = False
    if tc >= sess_end and not done: complete(); done = True
    ready = len(highs) == N and len(lows) == M and atr is not None
    if not ready: continue
    el, xl = max(highs), min(lows)
    if pos:
        act = TB(max(stop, xl)) if sig_long else None
        xorder = ('mkt',) if (not sig_long or c <= act) else ('stop', act)
    else:
        if sig_long: order = None
        else: order = ('mkt',) if c >= TA(el) else ('stop', TA(el))
tr = pd.DataFrame(trades, columns=["entry_t", "exit_t", "entry", "exit"])
bt = pd.read_csv(sigcsv); bt["signal_time"] = pd.to_datetime(bt.signal_time, utc=True)
tr["entry_t"] = pd.to_datetime(tr.entry_t).dt.tz_localize("America/New_York", ambiguous="NaT").dt.tz_convert("UTC")
m = tr.merge(bt[["signal_time", "signal_entry", "signal_exit_price", "pnl_pts"]], left_on="entry_t", right_on="signal_time", how="outer", indicator=True)
m["pts"] = m.exit - m.entry; m["diff"] = m.pts - m.pnl_pts
m["ticks_worse"] = (-m["diff"] / TICK).round(2)
both = m[m._merge == "both"]
print(f"replica trades {len(tr)}, backtest signals {len(bt)}, same entry candle {len(both)}, "
      f"P&L within 2 ticks {(both['diff'].abs() <= 2 * TICK + 1e-6).sum()}, total pts replica {tr.eval('exit-entry').sum():.2f} vs backtest {bt.pnl_pts.sum():.2f}")
print("ticks worse per trade:", both.ticks_worse.describe()[["mean","min","max"]].round(2).to_dict())
print(m[(m._merge != "both") | (m['diff'].abs() > 2 * TICK + 1e-6)][["entry_t", "signal_time", "entry", "signal_entry", "exit", "signal_exit_price", "diff", "_merge"]].to_string())
