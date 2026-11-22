"""Combine three $10k accounts on the common window into one $30k portfolio; emit sheet JSON."""
import pandas as pd, numpy as np, json, sys, itertools
W = sys.argv[1]; OUT = sys.argv[2]
NY = "America/New_York"
NAMES = dict(btc="Bitcoin (MBT), 10% risk", sp="S&P 500 (MES), 10% risk", mnq="Nasdaq (MNQ), 1 contract")
def stats_from(summary, trades, years):
    t = trades[trades.contracts > 0]; p = t.pnl_usd.values; w, l = p[p > 0], p[p <= 0]
    s = summary
    return dict(start=10000, end=s["ending_equity"], net=s["net_pnl"], ret=s["total_return_pct"], cagr=s["cagr_pct"], years=s["years"],
        period=[s["period"][0][:10], s["period"][1][:10]], signals=s["signals_total"], traded=s["signals_traded"], skipped=s["signals_skipped"],
        wins=int(len(w)), losses=int(len(l)), win_rate=100 * s["win_rate"], avg_win=s["avg_win"], avg_loss=s["avg_loss"], payoff=s["payoff_ratio"],
        exp_usd=s["expectancy_usd"], exp_r=s["expectancy_r"], median_r=float(t.r.median()), pf=s["profit_factor"],
        gross=s["gross_total"], costs=s["costs_total"], best=s["best_trade"], worst=s["worst_trade"], best_r=float(t.r.max()), worst_r=float(t.r.min()),
        wo_best=s["net_without_best"], wo_best2=s["net_without_best2"], top3=100 * s["top3_share_of_net"] if s["top3_share_of_net"] else None,
        lose_streak=s["max_losing_streak"], win_streak=s["max_winning_streak"], dd_usd=s["mtm_max_dd_usd"], dd_pct=s["mtm_max_dd_pct"],
        dd_peak=s["mtm_dd_peak"][:10], dd_trough=s["mtm_dd_trough"][:10], dd_rec=(s["mtm_dd_recovered"] or "not recovered")[:13].strip(),
        closed_dd=s["closed_trade_max_dd_usd"], uw_days=s["longest_underwater_days"], sharpe=s["monthly_sharpe"], months_pos=100 * s["pct_months_positive"],
        worst_month=s["worst_month_pct"], best_month=s["best_month_pct"], avg_risk=s["avg_actual_risk_pct"], max_risk=s["max_actual_risk_pct"],
        ci=s["bootstrap_expectancy_ci95"], p_le0=100 * s["bootstrap_p_mean_le_0"], hold=s["avg_hold_days"], trades_per_year=s["signals_traded"] / years,
        contracts=[int(t.contracts.min()), int(t.contracts.max())])
out = dict(individual_full={}, individual_window={}, trades=[], years={}, monthly_corr=None)
eqs = {}
for k in NAMES:
    for tag in ["full", "win"]:
        s = json.load(open(f"{W}/{tag}_{k}_summary.json")); tr = pd.read_csv(f"{W}/{tag}_{k}_trades.csv")
        out["individual_" + ("full" if tag == "full" else "window")][k] = stats_from(s, tr, s["years"])
        if tag == "win":
            e = pd.read_csv(f"{W}/win_{k}_equity_30m.csv"); e["t"] = pd.to_datetime(e.t, utc=True); eqs[k] = e.set_index("t").equity_mtm
            tr["mkt"] = k; out["trades"].append(tr)
            out["individual_window"][k]["by_year"] = s["by_year"]
# ---- portfolio equity on union of 30-min closes ----
E = pd.DataFrame(eqs).sort_index().ffill().fillna(10000.0); E["total"] = E.sum(axis=1)
m = E.total.values; pk = np.maximum.accumulate(m); dd = m - pk; ddp = dd / pk
it = int(np.argmin(ddp)); ip = int(np.argmax(m[:it + 1])); rec = np.where(m[it:] >= m[ip])[0]
uw = m < pk; best = (pd.Timedelta(0), None, None); st = None; idx = E.index
for i, u in enumerate(uw):
    if u and st is None: st = i
    if (not u or i == len(uw) - 1) and st is not None:
        if idx[i] - idx[st] > best[0]: best = (idx[i] - idx[st], st, i)
        st = None
daily = E.tz_convert(NY).resample("D").last().dropna(); monthly = daily.resample("ME").last()
mstart = pd.concat([pd.DataFrame([dict(btc=10000., sp=10000., mnq=10000., total=30000.)], index=[monthly.index[0] - pd.offsets.MonthEnd(1)]), monthly])
mret = mstart.pct_change().dropna()
yrs = (idx[-1] - idx[0]) / pd.Timedelta(days=365)
T = pd.concat(out.pop("trades")); T = T[T.contracts > 0].copy(); T["exit"] = pd.to_datetime(T.signal_exit_time, utc=True); T = T.sort_values("exit")
p = T.pnl_usd.values; w, l = p[p > 0], p[p <= 0]
streak = lambda c: max((len(list(g)) for kk, g in itertools.groupby(c) if kk), default=0)
rng = np.random.default_rng(11); rv = T.r.values
boot = np.array([rng.choice(rv, len(rv)).mean() for _ in range(20000)])
yrly = {}
ye = mstart.resample("YE").last() if False else None
yend = daily.resample("YE").last(); yprev = pd.concat([pd.DataFrame([dict(btc=10000., sp=10000., mnq=10000., total=30000.)], index=[yend.index[0] - pd.offsets.YearEnd(1)]), yend])
for y in yend.index.year:
    dy = daily[daily.index.year == y].total
    r = dict(total_ret=100 * (yprev.total.loc[str(y)].iloc[0] / yprev.total.shift(1).loc[str(y)].iloc[0] - 1),
             total_pnl=float(yprev.total.loc[str(y)].iloc[0] - yprev.total.shift(1).loc[str(y)].iloc[0]),
             total_dd=100 * float((dy / dy.cummax() - 1).min()))
    for k in NAMES:
        r[k + "_pnl"] = float(yprev[k].loc[str(y)].iloc[0] - yprev[k].shift(1).loc[str(y)].iloc[0])
        r[k + "_ret"] = 100 * (yprev[k].loc[str(y)].iloc[0] / yprev[k].shift(1).loc[str(y)].iloc[0] - 1)
    r["signals"] = int((pd.to_datetime(T.signal_time, utc=True).dt.tz_convert(NY).dt.year == y).sum())
    yrly[int(y)] = r
out["years"] = yrly
corr = mret[list(NAMES)].corr()
out["monthly_corr"] = {f"{a}-{b}": float(corr.loc[a, b]) for a, b in [("btc", "sp"), ("btc", "mnq"), ("sp", "mnq")]}
dd_each = {k: float(100 * (E[k] / E[k].cummax() - 1).min()) for k in NAMES}
out["portfolio"] = dict(start=30000, end=float(m[-1]), net=float(m[-1] - 30000), ret=100 * (m[-1] / 30000 - 1), cagr=100 * ((m[-1] / 30000) ** (1 / yrs) - 1), years=yrs,
    period=[str(idx[0].tz_convert(NY))[:10], str(idx[-1].tz_convert(NY))[:10]],
    signals=int(sum(v["signals"] for v in out["individual_window"].values())), traded=int(len(T)),
    skipped=int(sum(v["skipped"] for v in out["individual_window"].values())),
    wins=int(len(w)), losses=int(len(l)), win_rate=100 * len(w) / len(p), avg_win=float(w.mean()), avg_loss=float(l.mean()), payoff=float(w.mean() / -l.mean()),
    exp_usd=float(p.mean()), exp_r=float(T.r.mean()), median_r=float(T.r.median()), pf=float(w.sum() / -l.sum()),
    gross=float(T.gross_usd.sum()), costs=float(T.cost_usd.sum()), best=float(p.max()), worst=float(p.min()), best_r=float(T.r.max()), worst_r=float(T.r.min()),
    wo_best=float(np.sort(p)[:-1].sum()), wo_best2=float(np.sort(p)[:-2].sum()), top3=100 * float(np.sort(p)[-3:].sum() / p.sum()),
    lose_streak=streak(p <= 0), win_streak=streak(p > 0), dd_usd=float(dd.min()), dd_pct=100 * float(ddp.min()),
    dd_peak=str(idx[ip].tz_convert(NY))[:10], dd_trough=str(idx[it].tz_convert(NY))[:10], dd_rec=str(idx[it + rec[0]].tz_convert(NY))[:10] if len(rec) else "not recovered",
    closed_dd=float((np.cumsum(p) - np.maximum.accumulate(np.concatenate([[0], np.cumsum(p)]))[1:]).min()),
    uw_days=best[0] / pd.Timedelta(days=1), sharpe=float(mret.total.mean() / mret.total.std() * np.sqrt(12)), months_pos=100 * float((mret.total > 0).mean()),
    worst_month=100 * float(mret.total.min()), best_month=100 * float(mret.total.max()),
    avg_risk=None, max_risk=None, ci_r=[float(np.percentile(boot, 2.5)), float(np.percentile(boot, 97.5))], p_le0_r=100 * float((boot <= 0).mean()),
    hold=float(T.hold_days.mean()), trades_per_year=len(T) / yrs, dd_each_on_union=dd_each,
    end_each={k: float(E[k].iloc[-1]) for k in NAMES}, share_of_net={k: 100 * float((E[k].iloc[-1] - 10000) / (m[-1] - 30000)) for k in NAMES})
eqd = daily.copy(); eqd["dd"] = 100 * (eqd.total / eqd.total.cummax() - 1)
out["equity"] = [dict(d=i.strftime("%Y-%m-%d"), btc=round(r.btc), sp=round(r.sp), mnq=round(r.mnq), total=round(r.total), dd=round(r.dd, 2)) for i, r in eqd.iterrows()][::3] + \
    [dict(d=eqd.index[-1].strftime("%Y-%m-%d"), btc=round(eqd.btc.iloc[-1]), sp=round(eqd.sp.iloc[-1]), mnq=round(eqd.mnq.iloc[-1]), total=round(eqd.total.iloc[-1]), dd=round(eqd.dd.iloc[-1], 2))]
out["tradelist"] = [dict(m=r.mkt, s=str(pd.Timestamp(r.signal_time).tz_convert(NY))[:10], e=str(r.exit.tz_convert(NY))[:10], c=int(r.contracts),
    risk=round(r.risk_pct_actual, 1), pnl=round(r.pnl_usd), r=round(r.r, 2), x="10-day low" if r.exit_reason == "trail" else "initial stop") for r in T.sort_values("signal_time").itertuples()]
json.dump(out, open(OUT, "w"), default=float)
P = out["portfolio"]; print({k: (round(v, 2) if isinstance(v, float) else v) for k, v in P.items()}); print(out["monthly_corr"])
for y, v in yrly.items(): print(y, {k: round(x, 1) for k, x in v.items()})
