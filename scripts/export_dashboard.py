"""Export the 2019-2026 sized backtest into the JSON files the report page reads.
Each file is {rows, meta}; meta carries this script and the two scripts that made its inputs.
Usage: python3 export_dashboard.py <results dir> <30m bars csv> <scripts dir> <out dir> [100k|10k|50k]
  10k / 50k: that account size, 1 MNQ minimum, $2.50 per round trip main case; reads <results dir>/<set>."""
import sys, os, json
import pandas as pd, numpy as np
res, bars_csv, sdir, out = sys.argv[1:5]
SET = sys.argv[5] if len(sys.argv) > 5 else "100k"
ACCT = {"100k": 100000, "50k": 50000, "10k": 10000}[SET]
if SET != "100k": res = os.path.join(res, SET)
P = "rep" + SET
NY = "America/New_York"
code = lambda f: open(os.path.join(sdir, f)).read()
META = [dict(label="export_dashboard.py", value=code("export_dashboard.py"), type="code", lang="python"),
        dict(label="report.py", value=code("report.py"), type="code", lang="python"),
        dict(label="backtest.py", value=code("backtest.py"), type="code", lang="python"),
        dict(label="Data", value="Databento GLBX.MDP3 ohlcv-1m MNQ.FUT, 2019-05-05 to 2026-10-20, volume-rolled, back-adjusted, 30-minute candles"),
        dict(label="Case", value="Day-trading mode, fills at the indicator's modeled levels, 2% of closed equity per signal, signals needing more than 2% at 1 contract skipped, no costs") if SET == "100k" else
        dict(label="Case", value=f"${ACCT:,} account, day-trading mode, fills at the indicator's modeled levels, 2% of closed equity per signal with a minimum of 1 contract, $2.50 per contract per round trip for commission, fees and slippage")]
def write(name, rows, extra=None):
    rows = [{k: (None if isinstance(v, float) and np.isnan(v) else v) for k, v in r.items()} for r in rows]
    json.dump(dict(rows=rows, meta=META + (extra or [])), open(os.path.join(out, name + ".json"), "w"))
main = "rep_dt_level_c1_skip" if SET == "100k" else P + "_dt_level_min1_cost2.5"
s = json.load(open(os.path.join(res, main + "_summary.json")))
tr = pd.read_csv(os.path.join(res, main + "_trades.csv"))
eq = pd.read_csv(os.path.join(res, main + "_equity_daily.csv"))
eq["t"] = pd.to_datetime(eq.iloc[:, 0], utc=True).dt.tz_convert(NY)
b = pd.read_csv(bars_csv, usecols=["time_open", "close_adj"])
b["t"] = pd.to_datetime(b.time_open, utc=True).dt.tz_convert(NY) + pd.Timedelta(minutes=30)
bd = b.set_index("t").close_adj.resample("D").last().dropna()
bh = ACCT + (bd - b.close_adj.iloc[0]) * 2
e = eq.set_index(eq.t.dt.normalize()).equity_mtm
e.index = e.index.tz_localize(None); bh.index = bh.index.tz_localize(None).normalize()
df = pd.DataFrame(dict(strategy=e)).join(bh.rename("buyhold"), how="left").ffill()
df["dd_pct"] = 100 * (df.strategy / df.strategy.cummax() - 1)
write("equity", [dict(date=d.strftime("%Y-%m-%d"), strategy=round(r.strategy, 2), buyhold=round(r.buyhold, 2), dd_pct=round(r.dd_pct, 3)) for d, r in df.iterrows()])
tp = tr[tr.contracts > 0].pnl_usd.values
bh_dd = (bh - bh.cummax())
pos = np.sort(tp); big = tr[(tr.contracts > 0) & (tr.r > 4)].pnl_usd.sum()
write("metrics", [dict(
    start_equity=ACCT, ending_equity=round(s["ending_equity"]), net_pnl=round(s["net_pnl"]), total_return_pct=round(s["total_return_pct"], 1),
    cagr_pct=round(s["cagr_pct"], 1), years=round(s["years"], 1), signals=s["signals_total"], traded=s["signals_traded"], skipped=s["signals_skipped"],
    win_rate_pct=round(100 * s["win_rate"]), avg_win=round(s["avg_win"]), avg_loss=round(s["avg_loss"]), expectancy=round(s["expectancy_usd"]),
    expectancy_r=round(s["expectancy_r"], 2), profit_factor=round(s["profit_factor"], 2), mtm_dd_usd=round(s["mtm_max_dd_usd"]),
    mtm_dd_pct=round(s["mtm_max_dd_pct"], 1), underwater_days=round(s["longest_underwater_days"]), losing_streak=s["max_losing_streak"],
    best_trade=round(s["best_trade"]), net_without_best=round(s["net_without_best"]), net_without_best2=round(s["net_without_best2"]),
    big_winner_share_pct=round(100 * big / s["net_pnl"]), ci_low=round(s["bootstrap_expectancy_ci95"][0]), ci_high=round(s["bootstrap_expectancy_ci95"][1]),
    p_le_0_pct=round(100 * s["bootstrap_p_mean_le_0"], 1), avg_risk_pct=round(s["avg_actual_risk_pct"], 2), max_risk_pct=round(s["max_actual_risk_pct"], 1), costs=round(s["costs_total"]), months_positive_pct=round(100 * s["pct_months_positive"]),
    round_trips_per_signal=round(s["avg_segments"]), bh_pnl=round(bh.iloc[-1] - ACCT), bh_dd_usd=round(bh_dd.min()),
    bh_dd_pct=round(100 * (bh / bh.cummax() - 1).min(), 1))])
tr["start"] = pd.to_datetime(tr.signal_time, utc=True).dt.tz_convert(NY).dt.strftime("%Y-%m-%d")
tr["end"] = pd.to_datetime(tr.signal_exit_time, utc=True).dt.tz_convert(NY).dt.strftime("%Y-%m-%d")
write("trades", [dict(n=i + 1, start=r.start, end=r.end, contracts=int(r.contracts), stop_pts=round(r.stop_pts, 1), risk_pct=round(r.risk_pct_actual, 2),
                      pnl=round(r.pnl_usd), r=round(r.r, 2), exit="initial stop" if r.exit_reason == "stop" else "10-day low",
                      traded="yes" if r.contracts > 0 else "skipped", equity=round(r.equity_after)) for i, r in tr.iterrows()])
write("years", [dict(year=int(y), signals=int(v["signals"]), wins=int(v["wins"]), pnl=round(v["pnl"]), return_pct=round(v["return_pct"], 1),
                     max_dd_pct=round(v["max_dd_pct"], 1)) for y, v in s["by_year"].items()])
V = [("Main case", main), ("Take 1 contract when the stop exceeds 2%", "rep_dt_level_c1_min1"),
     ("Fixed $2,000 risk, skip wide stops", "rep_dt_level_c0_skip"), ("Fixed $2,000 risk, take 1 contract", "rep_dt_level_c0_min1"),
     ("No day-trading schedule", "rep_pure_level_c1_skip"), ("Alert-driven fills at candle close", "rep_dt_close_c1_skip"),
     ("Main case, $2.50 per round trip", "rep_dt_level_c1_skip_cost2.5"), ("Main case, $5.00 per round trip", "rep_dt_level_c1_skip_cost5"),
     ("No schedule, $2.50 per round trip", "rep_pure_level_c1_skip_cost2.5"), ("Alert fills, $2.50 per round trip", "rep_dt_close_c1_skip_cost2.5")]
if SET != "100k":
    V = [("Main case, $2.50 per round trip", main), ("No costs", P + "_dt_level_min1_cost0"), ("$5.00 per round trip", P + "_dt_level_min1_cost5"),
         ("No day-trading schedule, no costs", P + "_pure_level_min1_cost0"), ("No schedule, $2.50 per round trip", P + "_pure_level_min1_cost2.5"),
         ("No schedule, $5.00 per round trip", P + "_pure_level_min1_cost5"), ("Alert fills, no costs", P + "_dt_close_min1_cost0"),
         ("Alert fills, $2.50 per round trip", P + "_dt_close_min1_cost2.5"), ("Alert fills, $5.00 per round trip", P + "_dt_close_min1_cost5")]
    if SET == "50k":
        V += [("Skip signals needing more than 2%, $2.50 per round trip", P + "_dt_level_skip_cost2.5"),
              ("Skip over 2%, no schedule, $2.50 per round trip", P + "_pure_level_skip_cost2.5"),
              ("Skip over 2%, alert fills, $2.50 per round trip", P + "_dt_close_skip_cost2.5")]
rows = []
for label, f in V:
    v = json.load(open(os.path.join(res, f + "_summary.json")))
    rows.append(dict(variant=label, ending_equity=round(v["ending_equity"]), return_pct=round(v["total_return_pct"], 1), profit_factor=round(v["profit_factor"], 2),
                     mtm_dd_pct=round(v["mtm_max_dd_pct"], 1), costs=round(v["costs_total"]), traded=v["signals_traded"]))
write("variants", rows, [dict(label="Costs", value="Per contract per round trip, an assumed figure for commission, fees and slippage, not a broker's quoted rate")])
for f in os.listdir(out): print(f, os.path.getsize(os.path.join(out, f)))
