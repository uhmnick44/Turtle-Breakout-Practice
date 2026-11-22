"""Export the $10,000 BTC/MBT risk-choice backtest into the JSON files the report page reads.
Main case risk per signal from argv (default 4), compared with a second level (default 3); the risk table carries every grid level and the Monte Carlo results.
Each file is {rows, meta}; meta carries this script and the scripts that made its inputs.
Usage: python3 export_dashboard_btc10k.py <10k results dir> <signals csv> <30m bars csv> <scripts dir> <out dir> [main risk] [compare risk]"""
import sys, os, json
import pandas as pd, numpy as np
res, sig_csv, bars_csv, sdir, out = sys.argv[1:6]
MAIN = sys.argv[6] if len(sys.argv) > 6 else "4"; CMP = sys.argv[7] if len(sys.argv) > 7 else "3"
NY = "America/New_York"; PV = 0.1; START = 10000
code = lambda f: open(os.path.join(sdir, f)).read()
META = [dict(label="export_dashboard_btc10k.py", value=code("export_dashboard_btc10k.py"), type="code", lang="python"),
        dict(label="report.py", value=code("report.py"), type="code", lang="python"),
        dict(label="mc_risk.py", value=code("mc_risk.py"), type="code", lang="python"),
        dict(label="backtest.py", value=code("backtest.py"), type="code", lang="python"),
        dict(label="Data", value="Databento GLBX.MDP3 ohlcv-1m BTC.FUT, 2017-12-17 to 2026-11-20, calendar roll 5 trading days before expiry, back-adjusted, 30-minute candles, classic CME hours"),
        dict(label="Case", value=f"$10,000, {MAIN}% of closed equity per signal, day-trading mode off, fills at the indicator's modeled levels, Micro Bitcoin sizing (0.1 BTC, $0.10 per point), $7 per contract per round trip assumed costs")]
def write(name, rows, extra=None):
    rows = [{k: (None if isinstance(v, float) and np.isnan(v) else v) for k, v in r.items()} for r in rows]
    json.dump(dict(rows=rows, meta=META + (extra or [])), open(os.path.join(out, name + ".json"), "w"))
rep = lambda r: os.path.join(res, f"rep_mbt_pure_level_cost7_risk{r}")
s = json.load(open(rep(MAIN) + "_summary.json")); s3 = json.load(open(rep(CMP) + "_summary.json")); s2 = json.load(open(rep("2") + "_summary.json"))
tr = pd.read_csv(rep(MAIN) + "_trades.csv"); eq = pd.read_csv(rep(MAIN) + "_equity_daily.csv")
eq["t"] = pd.to_datetime(eq.iloc[:, 0], utc=True).dt.tz_convert(NY)
b = pd.read_csv(bars_csv, usecols=["time_open", "close_adj", "close"])
b["t"] = pd.to_datetime(b.time_open, utc=True).dt.tz_convert(NY) + pd.Timedelta(minutes=30)
n_bh = int(START / (PV * b.close.iloc[0]))
bd = b.set_index("t").close_adj.resample("D").last().dropna()
bh = START + (bd - b.close_adj.iloc[0]) * PV * n_bh
e = eq.set_index(eq.t.dt.normalize()).equity_mtm
e.index = e.index.tz_localize(None); bh.index = bh.index.tz_localize(None).normalize()
df = pd.DataFrame(dict(strategy=e)).join(bh.rename("buyhold"), how="left").ffill()
df["dd_pct"] = 100 * (df.strategy / df.strategy.cummax() - 1)
write("equity", [dict(date=d.strftime("%Y-%m-%d"), strategy=round(r.strategy, 2), buyhold=round(r.buyhold, 2), dd_pct=round(r.dd_pct, 3)) for d, r in df.iterrows()])
mc = json.load(open(os.path.join(res, "mc_risk_10k.json")))
sig = pd.read_csv(sig_csv)
t2 = pd.read_csv(rep("2") + "_trades.csv")
write("metrics", [dict(
    start_equity=START, ending_equity=round(s["ending_equity"]), net_pnl=round(s["net_pnl"]), total_return_pct=round(s["total_return_pct"], 1),
    cagr_pct=round(s["cagr_pct"], 1), years=round(s["years"], 1), signals=s["signals_total"], traded=s["signals_traded"], skipped=s["signals_skipped"],
    win_rate_pct=round(100 * s["win_rate"]), avg_win=round(s["avg_win"]), avg_loss=round(s["avg_loss"]), expectancy=round(s["expectancy_usd"]),
    expectancy_r=round(s["expectancy_r"], 2), median_r=round(float(tr.r.median()), 2), profit_factor=round(s["profit_factor"], 2),
    mtm_dd_usd=round(s["mtm_max_dd_usd"]), mtm_dd_pct=round(s["mtm_max_dd_pct"], 1), underwater_days=round(s["longest_underwater_days"]),
    losing_streak=s["max_losing_streak"], best_trade=round(s["best_trade"]), net_without_best=round(s["net_without_best"]),
    net_without_best2=round(s["net_without_best2"]), top3_share_pct=round(100 * s["top3_share_of_net"]),
    ci_low=round(s["bootstrap_expectancy_ci95"][0]), ci_high=round(s["bootstrap_expectancy_ci95"][1]), p_le_0_pct=round(100 * s["bootstrap_p_mean_le_0"], 1),
    avg_risk_pct=round(s["avg_actual_risk_pct"], 2), max_risk_pct=round(s["max_actual_risk_pct"], 2), months_positive_pct=round(100 * s["pct_months_positive"]),
    costs=round(s["costs_total"]), contracts_min=int(tr.contracts.min()), contracts_max=int(tr.contracts.max()),
    worst_trade_pct=round(float(100 * (tr.pnl_usd / tr.equity_before).min()), 1), main_risk=float(MAIN), cmp_risk=float(CMP),
    dd_recovered="no" if s["mtm_dd_recovered"] is None else "yes", dd_peak=s["mtm_dd_peak"][:10], dd_trough=s["mtm_dd_trough"][:10],
    wo5_p_loss_pct=round(100 * mc["results"]["without the best 5"][str(float(MAIN))]["p_loss"], 1),
    wo5_p_dd50_pct=round(100 * mc["results"]["without the best 5"][str(float(MAIN))]["p_dd_50"], 1),
    wo5_median_end=round(mc["results"]["without the best 5"][str(float(MAIN))]["median_end"]),
    all_p_dd50_pct=round(100 * mc["results"]["all signals"][str(float(MAIN))]["p_dd_50"], 1),
    bh_contracts=n_bh, bh_pnl=round(bh.iloc[-1] - START), bh_dd_pct=round(100 * (bh / bh.cummax() - 1).min(), 1),
    r3_ending_equity=round(s3["ending_equity"]), r3_cagr_pct=round(s3["cagr_pct"], 1), r3_dd_pct=round(s3["mtm_max_dd_pct"], 1), r3_traded=s3["signals_traded"],
    r2_traded=s2["signals_traded"], r2_skipped=s2["signals_skipped"],
    r2_traded_r=round(float(t2[t2.contracts > 0].r.mean()), 2), r2_skipped_r=round(float(t2[t2.contracts == 0].r.mean()), 2),
    median_stop_usd=round(float(sig.risk_pts.median() * PV)), max_stop_usd=round(float(sig.risk_pts.max() * PV)),
    capital_for_2pct=round(float(sig.risk_pts.max() * PV / 0.02), -2),
    kelly_all_pct=round(100 * mc["kelly_fraction"]["all"], 1), kelly_wo5_pct=round(100 * mc["kelly_fraction"]["without_best5"], 1))])
tr["start"] = pd.to_datetime(tr.signal_time, utc=True).dt.tz_convert(NY).dt.strftime("%Y-%m-%d")
tr["end"] = pd.to_datetime(tr.signal_exit_time, utc=True).dt.tz_convert(NY).dt.strftime("%Y-%m-%d")
write("trades", [dict(n=i + 1, start=r.start, end=r.end, contracts=int(r.contracts), stop_pts=round(r.stop_pts, 1), risk_pct=round(r.risk_pct_actual, 2),
                      pnl=round(r.pnl_usd), r=round(r.r, 2), exit="initial stop" if r.exit_reason == "stop" else "10-day low",
                      traded="yes" if r.contracts > 0 else "skipped", equity=round(r.equity_after)) for i, r in tr.iterrows()])
write("years", [dict(year=int(y), signals=int(v["signals"]), wins=int(v["wins"]), pnl=round(v["pnl"]), return_pct=round(v["return_pct"], 1),
                     max_dd_pct=round(v["max_dd_pct"], 1)) for y, v in s["by_year"].items()])
rows = []
for r in ["1", "1.5", "2", "2.5", "3", "4", "5", "6", "8", "10"]:
    v = json.load(open(rep(r) + "_summary.json")); a = mc["results"]["all signals"][str(float(r))]; w = mc["results"]["without the best 5"][str(float(r))]
    rows.append(dict(risk_pct=float(r), traded=v["signals_traded"], ending_equity=round(v["ending_equity"]), cagr_pct=round(v["cagr_pct"], 1),
                     mtm_dd_pct=round(v["mtm_max_dd_pct"], 1), mc_median_end=round(a["median_end"]), mc_p95_dd_pct=round(a["p95_dd_pct"], 1),
                     wo5_median_end=round(w["median_end"]), wo5_p_loss_pct=round(100 * w["p_loss"], 1), wo5_p95_dd_pct=round(w["p95_dd_pct"], 1),
                     wo5_p_dd30_pct=round(100 * w["p_dd_30"], 1)))
write("risks", rows, [dict(label="Monte Carlo", value="20,000 paths of 42 signals resampled with replacement, sized on closed equity with whole MBT contracts; drawdowns are closed-trade, which ran 7 to 15 points shallower than mark-to-market on the historical path")])
for f in os.listdir(out): print(f, os.path.getsize(os.path.join(out, f)))
