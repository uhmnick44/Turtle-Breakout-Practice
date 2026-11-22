"""Export the BTC/MBT sized backtest into the JSON files the report page reads.
Each file is {rows, meta}; meta carries this script and the two scripts that made its inputs.
Usage: python3 export_dashboard_btc.py <results dir> <30m bars csv> <scripts dir> <out dir>"""
import sys, os, json
import pandas as pd, numpy as np
res, bars_csv, sdir, out = sys.argv[1:5]
NY = "America/New_York"; PV = 0.1; START = 100000
code = lambda f: open(os.path.join(sdir, f)).read()
META = [dict(label="export_dashboard_btc.py", value=code("export_dashboard_btc.py"), type="code", lang="python"),
        dict(label="report.py", value=code("report.py"), type="code", lang="python"),
        dict(label="backtest.py", value=code("backtest.py"), type="code", lang="python"),
        dict(label="Data", value="Databento GLBX.MDP3 ohlcv-1m BTC.FUT, 2017-12-17 to 2026-11-20, calendar roll 5 trading days before expiry, back-adjusted, 30-minute candles, classic CME hours"),
        dict(label="Case", value="Day-trading mode off, fills at the indicator's modeled levels, 2% of closed equity per signal, sized in Micro Bitcoin contracts (0.1 BTC, $0.10 per point), $7 per contract per round trip assumed costs")]
def write(name, rows, extra=None):
    rows = [{k: (None if isinstance(v, float) and np.isnan(v) else v) for k, v in r.items()} for r in rows]
    json.dump(dict(rows=rows, meta=META + (extra or [])), open(os.path.join(out, name + ".json"), "w"))
main = "rep_mbt_pure_level_cost7"
s = json.load(open(os.path.join(res, main + "_summary.json")))
tr = pd.read_csv(os.path.join(res, main + "_trades.csv"))
eq = pd.read_csv(os.path.join(res, main + "_equity_daily.csv"))
eq["t"] = pd.to_datetime(eq.iloc[:, 0], utc=True).dt.tz_convert(NY)
b = pd.read_csv(bars_csv, usecols=["time_open", "close_adj", "close"])
b["t"] = pd.to_datetime(b.time_open, utc=True).dt.tz_convert(NY) + pd.Timedelta(minutes=30)
n_bh = int(START / (PV * b.close.iloc[0]))  # $100k of notional at the first close, held and rolled
bd = b.set_index("t").close_adj.resample("D").last().dropna()
bh = START + (bd - b.close_adj.iloc[0]) * PV * n_bh
e = eq.set_index(eq.t.dt.normalize()).equity_mtm
e.index = e.index.tz_localize(None); bh.index = bh.index.tz_localize(None).normalize()
df = pd.DataFrame(dict(strategy=e)).join(bh.rename("buyhold"), how="left").ffill()
df["dd_pct"] = 100 * (df.strategy / df.strategy.cummax() - 1)
write("equity", [dict(date=d.strftime("%Y-%m-%d"), strategy=round(r.strategy, 2), buyhold=round(r.buyhold, 2), dd_pct=round(r.dd_pct, 3)) for d, r in df.iterrows()])
dt = json.load(open(os.path.join(res, "rep_mbt_dt_level_cost7_summary.json")))
full = json.load(open(os.path.join(res, "rep_btc_dt_level_cost115_summary.json")))
sig = pd.read_csv(os.path.join(res, "bt_pure_level_signals.csv"))
tp = np.sort(tr[tr.contracts > 0].pnl_usd.values)
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
    bh_contracts=n_bh, bh_pnl=round(bh.iloc[-1] - START), bh_dd_usd=round((bh - bh.cummax()).min()), bh_dd_pct=round(100 * (bh / bh.cummax() - 1).min(), 1),
    dt_ending_equity=round(dt["ending_equity"]), dt_return_pct=round(dt["total_return_pct"], 1), dt_costs=round(dt["costs_total"]),
    dt_round_trips=round(dt["avg_segments"]), full_traded=full["signals_traded"], full_median_stop_usd=round(float(sig.risk_pts.median() * 5)),
    full_min_stop_usd=round(float(sig.risk_pts.min() * 5)))])
tr["start"] = pd.to_datetime(tr.signal_time, utc=True).dt.tz_convert(NY).dt.strftime("%Y-%m-%d")
tr["end"] = pd.to_datetime(tr.signal_exit_time, utc=True).dt.tz_convert(NY).dt.strftime("%Y-%m-%d")
write("trades", [dict(n=i + 1, start=r.start, end=r.end, contracts=int(r.contracts), stop_pts=round(r.stop_pts, 1), risk_pct=round(r.risk_pct_actual, 2),
                      pnl=round(r.pnl_usd), r=round(r.r, 2), exit="initial stop" if r.exit_reason == "stop" else "10-day low",
                      traded="yes" if r.contracts > 0 else "skipped", equity=round(r.equity_after)) for i, r in tr.iterrows()])
write("years", [dict(year=int(y), signals=int(v["signals"]), wins=int(v["wins"]), pnl=round(v["pnl"]), return_pct=round(v["return_pct"], 1),
                     max_dd_pct=round(v["max_dd_pct"], 1)) for y, v in s["by_year"].items()])
V = [("Main case: no day-trading schedule, $7", main), ("No schedule, no costs", "rep_mbt_pure_level_cost0"),
     ("No schedule, $15", "rep_mbt_pure_level_cost15"), ("No schedule, fills at candle close, $7", "rep_mbt_pure_close_cost7"),
     ("No schedule, fixed $2,000 risk, $7", "rep_mbt_pure_level_cost7_fixed"),
     ("Pine default: day-trading schedule, no costs", "rep_mbt_dt_level_cost0"), ("Day-trading schedule, $7", "rep_mbt_dt_level_cost7"),
     ("Day-trading schedule, $15", "rep_mbt_dt_level_cost15"), ("Day-trading schedule, fills at candle close, $7", "rep_mbt_dt_close_cost7"),
     ("Full-size BTC contract, day-trading schedule, $115", "rep_btc_dt_level_cost115")]
rows = []
for label, f in V:
    v = json.load(open(os.path.join(res, f + "_summary.json")))
    rows.append(dict(variant=label, ending_equity=round(v["ending_equity"]), return_pct=round(v["total_return_pct"], 1),
                     profit_factor=round(v["profit_factor"], 2), mtm_dd_pct=round(v["mtm_max_dd_pct"], 1), costs=round(v["costs_total"]),
                     traded=v["signals_traded"]))
write("variants", rows, [dict(label="Costs", value="Per contract per round trip, an assumed figure for commission, fees and slippage, not a broker's quoted rate. MBT $7 = $2.50 per side plus 2 ticks; BTC $115 = $7.50 per side plus 2 ticks")])
for f in os.listdir(out): print(f, os.path.getsize(os.path.join(out, f)))
