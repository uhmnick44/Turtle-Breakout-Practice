"""Export the MGC $10k / 4% / min-1-contract backtest into the JSON files the dashboard reads.
Each file is {rows, meta}; meta carries this script and the two scripts that made its inputs.
Usage: python3 export_dashboard_mgc.py <results dir> <30m bars csv> <scripts dir> <out dir>"""
import sys, os, json
import pandas as pd, numpy as np
res, bars_csv, sdir, out = sys.argv[1:5]
NY = "America/New_York"
ACCOUNT, PV = 10000, 10
MAIN = "rep_dt_level_c1_min1_cost2.5"
code = lambda f: open(os.path.join(sdir, f)).read()
META = [dict(label="export_dashboard_mgc.py", value=code("export_dashboard_mgc.py"), type="code", lang="python"),
        dict(label="report.py", value=code("report.py"), type="code", lang="python"),
        dict(label="backtest.py", value=code("backtest.py"), type="code", lang="python"),
        dict(label="Data", value="Databento GLBX.MDP3 ohlcv-1m MGC.FUT, all 60 outrights, 2016-10-23 to 2026-11-20, volume-rolled, back-adjusted, 30-minute candles"),
        dict(label="Case", value="Day-trading mode, fills at the indicator's modeled levels, 4% of closed equity per signal rounded down with a minimum of 1 contract, $2.50 per contract round trip")]
def clean(v):
    if isinstance(v, (np.floating, float)): return None if np.isnan(v) else round(float(v), 4)
    if isinstance(v, np.integer): return int(v)
    return v
def write(name, rows):
    json.dump(dict(rows=[{k: clean(v) for k, v in r.items()} for r in rows], meta=META), open(os.path.join(out, name + ".json"), "w"))
S = lambda n: json.load(open(os.path.join(res, n + "_summary.json")))
s = S(MAIN)
tr = pd.read_csv(os.path.join(res, MAIN + "_trades.csv"))
et = lambda c: pd.to_datetime(tr[c], utc=True).dt.tz_convert(NY).dt.strftime("%Y-%m-%d")
tr["start"], tr["end"] = et("signal_time"), et("signal_exit_time")
tr["r_net"] = tr.pnl_usd / tr.risk_usd
sig = pd.read_csv(os.path.join(res, "bt_dt_level_signals.csv"))

# equity: strategy MTM vs holding 1 MGC
eq = pd.read_csv(os.path.join(res, MAIN + "_equity_daily.csv"))
eq["t"] = pd.to_datetime(eq.iloc[:, 0], utc=True).dt.tz_convert(NY)
b = pd.read_csv(bars_csv, usecols=["time_open", "close_adj"])
b["t"] = pd.to_datetime(b.time_open, utc=True).dt.tz_convert(NY) + pd.Timedelta(minutes=30)
bd = b.set_index("t").close_adj.resample("D").last().dropna()
bh = ACCOUNT + (bd - b.close_adj.iloc[0]) * PV
e = eq.set_index(eq.t.dt.normalize()).equity_mtm
e.index = e.index.tz_localize(None); bh.index = bh.index.tz_localize(None).normalize()
df = pd.DataFrame(dict(strategy=e)).join(bh.rename("buyhold"), how="left").ffill()
df["dd_pct"] = 100 * (df.strategy / df.strategy.cummax() - 1)
write("equity", [dict(date=d.strftime("%Y-%m-%d"), strategy=r.strategy, buyhold=r.buyhold, dd_pct=r.dd_pct) for d, r in df.iterrows()])
bhfull = ACCOUNT + (b.close_adj - b.close_adj.iloc[0]) * PV
bh_dd = bhfull - bhfull.cummax()

pnl = tr.pnl_usd
pure = S("rep_pure_level_c1_min1_cost2.5")
m = dict(
    signals=s["signals_total"], traded=s["signals_traded"], years=s["years"],
    ending_equity=s["ending_equity"], net_pnl=s["net_pnl"], total_return_pct=s["total_return_pct"], cagr_pct=s["cagr_pct"],
    mtm_dd_usd=s["mtm_max_dd_usd"], mtm_dd_pct=s["mtm_max_dd_pct"], closed_dd_usd=s["closed_trade_max_dd_usd"],
    dd_peak=pd.Timestamp(s["mtm_dd_peak"]).tz_convert(NY).strftime("%B %-d, %Y"),
    dd_trough=pd.Timestamp(s["mtm_dd_trough"]).tz_convert(NY).strftime("%B %-d, %Y"),
    underwater_days=s["longest_underwater_days"], months_positive_pct=100 * s["pct_months_positive"], losing_streak=s["max_losing_streak"],
    expectancy=s["expectancy_usd"], expectancy_r=float(tr.r_net.mean()), median_r=float(tr.r_net.median()),
    profit_factor=s["profit_factor"], win_rate_pct=100 * s["win_rate"], avg_win=s["avg_win"], avg_loss=s["avg_loss"],
    avg_risk_pct=s["avg_actual_risk_pct"], max_risk_pct=s["max_actual_risk_pct"],
    worst_trade=float(pnl.min()), worst_trade_pct=float(100 * (tr.pnl_usd / tr.equity_before).min()),
    best_trade=s["best_trade"], net_without_best=s["net_without_best"],
    n_over_budget=int((tr.risk_usd > 0.04 * tr.equity_before).sum()), n_over_10=int((tr.risk_pct_actual > 10).sum()),
    n_over_20=int((tr.risk_pct_actual > 20).sum()),
    costs_total=s["costs_total"], net_before_costs=S("rep_dt_level_c1_min1")["net_pnl"],
    avg_round_trips=float(tr.segments.mean()), mfe_mean_pts=float(sig.mfe.mean()), kept_mean_pts=float(sig.pnl_pts.mean()),
    ci_low=s["bootstrap_expectancy_ci95"][0], ci_high=s["bootstrap_expectancy_ci95"][1], p_le_0_pct=100 * s["bootstrap_p_mean_le_0"],
    pure_net=pure["net_pnl"], pure_return_pct=pure["total_return_pct"], pure_p_le_0_pct=100 * pure["bootstrap_p_mean_le_0"],
    bh_pnl=float(bhfull.iloc[-1] - ACCOUNT), bh_dd_usd=float(bh_dd.min()), bh_dd_pct=float(100 * (bh_dd / bhfull.cummax()).min()))
write("metrics", [m])

write("trades", [dict(n=i + 1, start=r.start, end=r.end, contracts=r.contracts, stop_pts=r.stop_pts, risk_usd=r.risk_usd,
                      risk_pct=r.risk_pct_actual, round_trips=r.segments, cost=r.cost_usd, pnl=r.pnl_usd, r=r.r_net, mfe_pts=r.mfe_pts,
                      exit=r.exit_reason, equity=r.equity_after, traded="yes") for i, r in tr.iterrows()])

write("years", [dict(year=("2017 (from Oct 2016)" if y == "2017" else "2026 (to Nov 20)" if y == "2026" else y), signals=v["signals"], wins=v["wins"],
                     pnl=v["pnl"], return_pct=v["return_pct"], max_dd_pct=v["max_dd_pct"]) for y, v in s["by_year"].items()])

VARS = [("Main: day-trading, level fills, $2.50", "rep_dt_level_c1_min1_cost2.5", "yes"),
        ("Day-trading, level fills, $0", "rep_dt_level_c1_min1", ""),
        ("Day-trading, level fills, $5.00", "rep_dt_level_c1_min1_cost5", ""),
        ("Day-trading, close fills, $2.50", "rep_dt_close_c1_min1_cost2.5", ""),
        ("Day-trading, close fills, $5.00", "rep_dt_close_c1_min1_cost5", ""),
        ("Pure system, level fills, $2.50", "rep_pure_level_c1_min1_cost2.5", ""),
        ("Pure system, level fills, $5.00", "rep_pure_level_c1_min1_cost5", ""),
        ("Pure system, close fills, $2.50", "rep_pure_close_c1_min1_cost2.5", ""),
        ("Skip signals over 4% (reference)", "rep_dt_level_c1_skip_cost2.5", "")]
rows = []
for lab, n, main in VARS:
    v = S(n)
    rows.append(dict(variant=lab, main=main, traded=v["signals_traded"], ending_equity=v["ending_equity"], return_pct=v["total_return_pct"],
                     profit_factor=v["profit_factor"], mtm_dd_pct=v["mtm_max_dd_pct"], max_risk_pct=v["max_actual_risk_pct"],
                     costs=v["costs_total"], p_le_0_pct=100 * v["bootstrap_p_mean_le_0"]))
write("variants", rows)
print(json.dumps(m, indent=0))
