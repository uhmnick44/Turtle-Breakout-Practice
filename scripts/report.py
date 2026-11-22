"""Sized, mark-to-market report for backtest.py output.
Sizing: contracts = floor(risk$ / (initial stop pts * $2)), decided at the breakout candle.
  --policy skip : 0 contracts -> signal not traded
  --policy min1 : at least 1 contract, even when that risks more than the budget
  --compound 1  : risk$ = risk_pct of closed equity at the breakout; 0 = of starting account
Costs: --cost_rt dollars per contract per round trip (commission + fees + slippage), applied per segment.
Rolls: --rolls <rolls.csv> charges one extra --cost_rt per contract for every roll a held segment spans
  (sell the expiring contract, buy the next). Roll time = 18:00 ET on the day before the roll's trading day,
  the open of the first session on the new contract. Charged at that time in the mark-to-market curve."""
import argparse, json, math, itertools
import pandas as pd, numpy as np
p = argparse.ArgumentParser()
p.add_argument("prefix"); p.add_argument("bars"); p.add_argument("--out", required=True)
p.add_argument("--account", type=float, default=100000); p.add_argument("--risk_pct", type=float, default=2.0)
p.add_argument("--compound", type=int, default=1); p.add_argument("--policy", choices=["skip","min1"], default="skip")
p.add_argument("--cost_rt", type=float, default=0.0); p.add_argument("--pv", type=float, default=2.0)
p.add_argument("--rolls", default=None)
a = p.parse_args()
sig = pd.read_csv(a.prefix + "_signals.csv"); seg = pd.read_csv(a.prefix + "_segments.csv")
for c in ["signal_time","signal_exit_time"]: sig[c] = pd.to_datetime(sig[c], utc=True)
for c in ["signal_time","entry_time","exit_time"]: seg[c] = pd.to_datetime(seg[c], utc=True)
ROLL_T = []
if a.rolls:
    rd = pd.to_datetime(pd.read_csv(a.rolls).tday) - pd.Timedelta(days=1) + pd.Timedelta(hours=18)
    ROLL_T = list(rd.dt.tz_localize("America/New_York").dt.tz_convert("UTC"))
seg["rolls"] = [sum(1 for r in ROLL_T if e < r < x) for e, x in zip(seg.entry_time, seg.exit_time)]
sig = sig.sort_values("signal_time").reset_index(drop=True)
bars = pd.read_csv(a.bars, usecols=["time_open","close_adj","open_adj","close"])
bars["t_close"] = pd.to_datetime(bars.time_open, utc=True) + pd.Timedelta(minutes=30)
T = bars.t_close.values; CL = bars.close_adj.values

eq = a.account; rows = []
for _, s in sig.iterrows():
    base = eq if a.compound else a.account
    budget = base * a.risk_pct / 100; per_ct = s.risk_pts * a.pv
    n = math.floor(budget / per_ct)
    if n == 0 and a.policy == "min1": n = 1
    sg = seg[seg.signal_time == s.signal_time]
    gross = n * (sg.exit_price - sg.entry_price).sum() * a.pv
    roll_cost = n * int(sg.rolls.sum()) * a.cost_rt
    cost = n * len(sg) * a.cost_rt + roll_cost
    pnl = gross - cost
    rows.append(dict(signal_time=s.signal_time, signal_exit_time=s.signal_exit_time, contracts=n, stop_pts=s.risk_pts,
                     budget_usd=budget, risk_usd=n * per_ct, risk_pct_actual=100 * n * per_ct / eq, segments=len(sg), rolls=int(sg.rolls.sum()), roll_cost_usd=roll_cost,
                     gross_usd=gross, cost_usd=cost, pnl_usd=pnl, r=s.r_multiple, mae_pts=s.mae, mfe_pts=s.mfe,
                     hold_days=s.hold_days, exit_reason=s.exit_reason, equity_before=eq, equity_after=eq + pnl))
    eq += pnl
tr = pd.DataFrame(rows)

# ---- mark-to-market equity on every 30-minute close ----
ncts = dict(zip(tr.signal_time, tr.contracts))
realized = np.zeros(len(T)); openpnl = np.zeros(len(T))
for _, g in seg.iterrows():
    n = ncts[g.signal_time]
    if n == 0: continue
    et, xt = g.entry_time.to_datetime64(), g.exit_time.to_datetime64()
    i0 = np.searchsorted(T, et, side="right"); i1 = np.searchsorted(T, xt, side="left")  # open at T where et < T < xt
    openpnl[i0:i1] += n * (CL[i0:i1] - g.entry_price) * a.pv
    k = min(np.searchsorted(T, xt, side="left"), len(T) - 1)
    realized[k] += n * ((g.exit_price - g.entry_price) * a.pv - a.cost_rt)
    for r in ROLL_T:
        if g.entry_time < r < g.exit_time:
            realized[min(np.searchsorted(T, r.to_datetime64(), side="left"), len(T) - 1)] -= n * a.cost_rt
mtm = a.account + np.cumsum(realized) + openpnl
peak = np.maximum.accumulate(mtm); dd = mtm - peak; ddp = dd / peak
i_trough = int(np.argmin(ddp)); i_peak = int(np.argmax(mtm[:i_trough + 1]))
after = np.where(mtm[i_trough:] >= mtm[i_peak])[0]
i_rec = i_trough + after[0] if len(after) else None
# longest time under water
uw = mtm < peak; longest = (0, None, None); start = None
for i, u in enumerate(uw):
    if u and start is None: start = i
    if (not u or i == len(uw) - 1) and start is not None:
        dur = T[i] - T[start]
        if dur > (longest[0] if longest[1] is not None else np.timedelta64(0, "ns")): longest = (dur, start, i)
        start = None
eqdf = pd.DataFrame(dict(t=pd.to_datetime(T, utc=True), equity_mtm=mtm, drawdown=dd, drawdown_pct=100 * ddp))
daily = eqdf.set_index("t").equity_mtm.tz_convert("America/New_York").resample("D").last().dropna()
monthly = daily.resample("ME").last()

traded = tr[tr.contracts > 0]; pnl = traded.pnl_usd.values
w, l = pnl[pnl > 0], pnl[pnl <= 0]
streak = lambda c: max((len(list(g)) for k, g in itertools.groupby(c) if k), default=0)
years = (T[-1] - T[0]) / np.timedelta64(365, "D") / 1.0
yrs = float(years)
mret = monthly.pct_change().dropna()
rng = np.random.default_rng(11)
boot = np.array([rng.choice(pnl, len(pnl)).mean() for _ in range(20000)])
by_year = {}
tr["year"] = tr.signal_time.dt.tz_convert("America/New_York").dt.year
for y, g in tr[tr.contracts > 0].groupby("year"):
    ys = daily[daily.index.year == y]
    prev = daily[daily.index.year < y]
    start_eq = prev.iloc[-1] if len(prev) else a.account
    by_year[int(y)] = dict(signals=int(len(g)), wins=int((g.pnl_usd > 0).sum()), pnl=float(g.pnl_usd.sum()),
                           return_pct=float(100 * (ys.iloc[-1] / start_eq - 1)) if len(ys) else None,
                           max_dd_pct=float(100 * ((ys / ys.cummax()) - 1).min()) if len(ys) else None)
summary = dict(
    params=vars(a), period=[str(pd.to_datetime(T[0], utc=True)), str(pd.to_datetime(T[-1], utc=True))], years=yrs,
    signals_total=int(len(tr)), signals_traded=int(len(traded)), signals_skipped=int((tr.contracts == 0).sum()),
    skipped=[dict(t=str(r.signal_time), stop_pts=round(r.stop_pts, 1), r=round(r.r, 2)) for r in tr[tr.contracts == 0].itertuples()],
    contracts_dist=tr.contracts.value_counts().sort_index().to_dict(),
    avg_actual_risk_pct=float(traded.risk_pct_actual.mean()), max_actual_risk_pct=float(traded.risk_pct_actual.max()),
    ending_equity=float(tr.equity_after.iloc[-1]), net_pnl=float(tr.equity_after.iloc[-1] - a.account),
    total_return_pct=float(100 * (tr.equity_after.iloc[-1] / a.account - 1)),
    cagr_pct=float(100 * ((tr.equity_after.iloc[-1] / a.account) ** (1 / yrs) - 1)),
    win_rate=float(len(w) / len(pnl)), avg_win=float(w.mean()), avg_loss=float(l.mean()),
    payoff_ratio=float(w.mean() / -l.mean()), expectancy_usd=float(pnl.mean()), expectancy_r=float(traded.r.mean()),
    profit_factor=float(w.sum() / -l.sum()), gross_total=float(traded.gross_usd.sum()), costs_total=float(traded.cost_usd.sum()),
    roll_costs_total=float(traded.roll_cost_usd.sum()), rolls_crossed=int(traded.rolls.sum()),
    best_trade=float(pnl.max()), worst_trade=float(pnl.min()),
    net_without_best=float(np.sort(pnl)[:-1].sum()), net_without_best2=float(np.sort(pnl)[:-2].sum()),
    top3_share_of_net=float(np.sort(pnl)[-3:].sum() / pnl.sum()) if pnl.sum() != 0 else None,
    max_losing_streak=streak(pnl <= 0), max_winning_streak=streak(pnl > 0),
    closed_trade_max_dd_usd=float((np.cumsum(pnl) - np.maximum.accumulate(np.concatenate([[0], np.cumsum(pnl)]))[1:]).min()),
    mtm_max_dd_usd=float(dd.min()), mtm_max_dd_pct=float(100 * ddp.min()),
    mtm_dd_peak=str(pd.to_datetime(T[i_peak], utc=True)), mtm_dd_trough=str(pd.to_datetime(T[i_trough], utc=True)),
    mtm_dd_recovered=str(pd.to_datetime(T[i_rec], utc=True)) if i_rec is not None else None,
    longest_underwater_days=float(longest[0] / np.timedelta64(1, "D")) if longest[1] is not None else 0,
    longest_underwater_from=str(pd.to_datetime(T[longest[1]], utc=True)) if longest[1] is not None else None,
    longest_underwater_to=str(pd.to_datetime(T[longest[2]], utc=True)) if longest[1] is not None else None,
    monthly_sharpe=float(mret.mean() / mret.std() * np.sqrt(12)), pct_months_positive=float((mret > 0).mean()),
    worst_month_pct=float(100 * mret.min()), best_month_pct=float(100 * mret.max()),
    bootstrap_expectancy_ci95=[float(np.percentile(boot, 2.5)), float(np.percentile(boot, 97.5))],
    bootstrap_p_mean_le_0=float((boot <= 0).mean()),
    by_year=by_year, exit_reasons=traded.exit_reason.value_counts().to_dict(),
    avg_hold_days=float(traded.hold_days.mean()), avg_segments=float(traded.segments.mean()),
    mae_pts_mean=float(traded.mae_pts.mean()), mfe_pts_mean=float(traded.mfe_pts.mean()))
tr.to_csv(a.out + "_trades.csv", index=False)
daily.rename("equity_mtm").to_csv(a.out + "_equity_daily.csv")
json.dump(summary, open(a.out + "_summary.json", "w"), indent=1, default=str)
print(json.dumps({k: v for k, v in summary.items() if k not in ("by_year", "skipped", "params")}, indent=0, default=str))
