"""Export a sized backtest into the JSON files a report page reads. Each file is {rows, meta};
meta carries this script, the two scripts that made its inputs, and the run's settings.
Usage: python3 export_report.py <config.json>
Config: {results, bars, scripts, out, account, main, case, costs_note, variants: [[label, prefix], ...]}"""
import sys, os, json, math
import pandas as pd, numpy as np
cfg = json.load(open(sys.argv[1]))
res, out, A = cfg["results"], cfg["out"], float(cfg["account"])
NY = "America/New_York"
code = lambda f: open(os.path.join(cfg["scripts"], f)).read()
META = [dict(label="export_report.py", value=code("export_report.py"), type="code", lang="python"),
        dict(label="report.py", value=code("report.py"), type="code", lang="python"),
        dict(label="backtest.py", value=code("backtest.py"), type="code", lang="python"),
        dict(label="Data", value="Databento GLBX.MDP3 ohlcv-1m MNQ.FUT, 2019-05-05 to 2026-10-20, volume-rolled, back-adjusted, 30-minute candles"),
        dict(label="Case", value=cfg["case"]), dict(label="Costs", value=cfg["costs_note"])]
def clean(v):
    if isinstance(v, (float, np.floating)) and (math.isnan(v) or math.isinf(v)): return None
    return v.item() if isinstance(v, np.generic) else v
def write(name, rows):
    json.dump(dict(rows=[{k: clean(v) for k, v in r.items()} for r in rows], meta=META), open(os.path.join(out, name + ".json"), "w"))
rnd = lambda v, d=0: None if v is None or (isinstance(v, float) and (math.isnan(v) or math.isinf(v))) else (round(v) if d == 0 else round(v, d))
main = cfg["main"]
s = json.load(open(os.path.join(res, main + "_summary.json")))
tr = pd.read_csv(os.path.join(res, main + "_trades.csv"))
eq = pd.read_csv(os.path.join(res, main + "_equity_daily.csv"))
eq["t"] = pd.to_datetime(eq.iloc[:, 0], utc=True).dt.tz_convert(NY)
b = pd.read_csv(cfg["bars"], usecols=["time_open", "close_adj"])
b["t"] = pd.to_datetime(b.time_open, utc=True).dt.tz_convert(NY) + pd.Timedelta(minutes=30)
bd = b.set_index("t").close_adj.resample("D").last().dropna()
bh = A + (bd - b.close_adj.iloc[0]) * 2
e = eq.set_index(eq.t.dt.normalize()).equity_mtm
e.index = e.index.tz_localize(None); bh.index = bh.index.tz_localize(None).normalize()
df = pd.DataFrame(dict(strategy=e)).join(bh.rename("buyhold"), how="left").ffill()
df["dd_pct"] = 100 * (df.strategy / df.strategy.cummax() - 1)
write("equity", [dict(date=d.strftime("%Y-%m-%d"), strategy=round(r.strategy, 2), buyhold=round(r.buyhold, 2), dd_pct=round(r.dd_pct, 3)) for d, r in df.iterrows()])
traded = tr[tr.contracts > 0]
big = traded[traded.r > 4].pnl_usd.sum()
gross = s["gross_total"]; costs = s["commfees_total"] + s["slippage_total"]
write("metrics", [dict(
    start_equity=round(A), ending_equity=rnd(s["ending_equity"]), net_pnl=rnd(s["net_pnl"]), total_return_pct=rnd(s["total_return_pct"], 1),
    cagr_pct=rnd(s["cagr_pct"], 1), signals=s["signals_total"], traded=s["signals_traded"], skipped=s["signals_skipped"],
    skipped_risk=s["skipped_risk"], skipped_margin=s["skipped_margin"],
    win_rate_pct=rnd(100 * s["win_rate"]), avg_win=rnd(s["avg_win"]), avg_loss=rnd(s["avg_loss"]), expectancy=rnd(s["expectancy_usd"]),
    expectancy_r=rnd(s["expectancy_r"], 2), profit_factor=rnd(s["profit_factor"], 2), mtm_dd_usd=rnd(s["mtm_max_dd_usd"]),
    mtm_dd_pct=rnd(s["mtm_max_dd_pct"], 1), underwater_days=rnd(s["longest_underwater_days"]), losing_streak=s["max_losing_streak"],
    best_trade=rnd(s["best_trade"]), net_without_best=rnd(s["net_without_best"]), big_winner_share_pct=rnd(100 * big / s["net_pnl"]) if s["net_pnl"] else None,
    ci_low=rnd(s["bootstrap_expectancy_ci95"][0]), ci_high=rnd(s["bootstrap_expectancy_ci95"][1]), p_le_0_pct=rnd(100 * s["bootstrap_p_mean_le_0"], 1),
    avg_risk_pct=rnd(s["avg_actual_risk_pct"], 1), max_risk_pct=rnd(s["max_actual_risk_pct"], 1), months_positive_pct=rnd(100 * s["pct_months_positive"]),
    gross_pnl=rnd(gross), commfees=rnd(s["commfees_total"]), slippage=rnd(s["slippage_total"]), costs=rnd(costs),
    cost_share_pct=rnd(100 * costs / gross) if gross > 0 else None, round_trips=s["round_trips"], roll_trades=s["roll_trades"],
    cost_per_round_trip=rnd(2 * s["cost_per_side"], 2), margin_call_days=s["margin_call_days"],
    bh_pnl=rnd(bh.iloc[-1] - A), bh_dd_usd=rnd((bh - bh.cummax()).min()), bh_dd_pct=rnd(100 * (bh / bh.cummax() - 1).min(), 1))])
tr["start"] = pd.to_datetime(tr.signal_time, utc=True).dt.tz_convert(NY).dt.strftime("%Y-%m-%d")
tr["end"] = pd.to_datetime(tr.signal_exit_time, utc=True).dt.tz_convert(NY).dt.strftime("%Y-%m-%d")
why = {"risk": "stop too wide", "margin": "not enough margin"}
write("trades", [dict(n=i + 1, start=r.start, end=r.end, contracts=int(r.contracts), stop_pts=round(r.stop_pts, 1),
                      risk_per_contract=round(r.stop_pts * 2), risk_pct=round(r.risk_pct_actual, 1), pnl=round(r.pnl_usd), cost=round(r.cost_usd),
                      r=round(r.r, 2), exit="initial stop" if r.exit_reason == "stop" else "10-day low",
                      traded="yes" if r.contracts > 0 else why.get(r.skip_reason, "skipped"), equity=round(r.equity_after)) for i, r in tr.iterrows()])
write("years", [dict(year=int(y), signals=int(v["signals"]), wins=int(v["wins"]), pnl=round(v["pnl"]), return_pct=round(v["return_pct"], 1),
                     max_dd_pct=round(v["max_dd_pct"], 1)) for y, v in s["by_year"].items()])
rows = []
for label, f in cfg["variants"]:
    v = json.load(open(os.path.join(res, f + "_summary.json")))
    rows.append(dict(variant=label, traded=v["signals_traded"], ending_equity=rnd(v["ending_equity"]), return_pct=rnd(v["total_return_pct"], 1),
                     profit_factor=rnd(v.get("profit_factor"), 2), mtm_dd_pct=rnd(v.get("mtm_max_dd_pct"), 1),
                     costs=rnd(v.get("commfees_total", 0) + v.get("slippage_total", 0)), max_risk_pct=rnd(v.get("max_actual_risk_pct"), 1)))
write("variants", rows)
for f in sorted(os.listdir(out)): print(f, os.path.getsize(os.path.join(out, f)))
