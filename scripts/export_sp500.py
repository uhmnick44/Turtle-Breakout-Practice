"""Export the S&P 500 (MES-sized ES prices) backtest into the JSON files the report page reads.
Each file is {rows, meta}; meta carries this script and the two scripts that made its inputs.
Usage: python3 export_sp500.py <results dir> <30m bars csv> <scripts dir> <out dir>"""
import sys, os, json
import pandas as pd, numpy as np
res, bars_csv, sdir, out = sys.argv[1:5]
NY = "America/New_York"
MAIN = "rep_mes_pure_skip_cost4"
code = lambda f: open(os.path.join(sdir, f)).read()
META = [dict(label="export_sp500.py", value=code("export_sp500.py"), type="code", lang="python"),
        dict(label="report.py", value=code("report.py"), type="code", lang="python"),
        dict(label="backtest.py", value=code("backtest.py"), type="code", lang="python"),
        dict(label="Data", value="Databento GLBX.MDP3 ohlcv-1m ES.FUT, 2016-10-23 to 2026-11-20, volume-rolled, back-adjusted, 30-minute candles. Sized as MES ($5 per point); MES listed 2019-05, so earlier rows are ES prices at $5 per point"),
        dict(label="Case", value="Overnight mode (day-trading schedule off), fills at the indicator's modeled levels, 2% of closed equity per signal, signals needing more than 2% at 1 contract skipped, $4 per contract per round trip plus one round trip per quarterly roll held through")]
def write(name, rows, extra=None):
    rows = [{k: (None if isinstance(v, float) and np.isnan(v) else v) for k, v in r.items()} for r in rows]
    json.dump(dict(rows=rows, meta=META + (extra or [])), open(os.path.join(out, name + ".json"), "w"))
s = json.load(open(os.path.join(res, MAIN + "_summary.json")))
tr = pd.read_csv(os.path.join(res, MAIN + "_trades.csv"))
eq = pd.read_csv(os.path.join(res, MAIN + "_equity_daily.csv"))
eq["t"] = pd.to_datetime(eq.iloc[:, 0], utc=True).dt.tz_convert(NY)
b = pd.read_csv(bars_csv, usecols=["time_open", "close_adj", "close"])
b["t"] = pd.to_datetime(b.time_open, utc=True).dt.tz_convert(NY) + pd.Timedelta(minutes=30)
BH_N = int(100000 // (b.close.iloc[0] * 5))  # MES contracts worth about $100,000 at the first candle
bd = b.set_index("t").close_adj.resample("D").last().dropna()
bh = 100000 + (bd - b.close_adj.iloc[0]) * 5 * BH_N
e = eq.set_index(eq.t.dt.normalize()).equity_mtm
e.index = e.index.tz_localize(None); bh.index = bh.index.tz_localize(None).normalize()
df = pd.DataFrame(dict(strategy=e)).join(bh.rename("buyhold"), how="left").ffill()
df["dd_pct"] = 100 * (df.strategy / df.strategy.cummax() - 1)
write("equity", [dict(date=d.strftime("%Y-%m-%d"), strategy=round(r.strategy, 2), buyhold=round(r.buyhold, 2), dd_pct=round(r.dd_pct, 3)) for d, r in df.iterrows()])
traded = tr[tr.contracts > 0]
big = traded[traded.r > 3]
write("metrics", [dict(
    start_equity=100000, ending_equity=round(s["ending_equity"]), net_pnl=round(s["net_pnl"]), total_return_pct=round(s["total_return_pct"], 1),
    cagr_pct=round(s["cagr_pct"], 1), years=round(s["years"], 1), signals=s["signals_total"], traded=s["signals_traded"], skipped=s["signals_skipped"],
    win_rate_pct=round(100 * s["win_rate"]), avg_win=round(s["avg_win"]), avg_loss=round(s["avg_loss"]), expectancy=round(s["expectancy_usd"]),
    expectancy_r=round(s["expectancy_r"], 2), profit_factor=round(s["profit_factor"], 2), mtm_dd_usd=round(s["mtm_max_dd_usd"]),
    mtm_dd_pct=round(s["mtm_max_dd_pct"], 1), underwater_days=round(s["longest_underwater_days"]), losing_streak=s["max_losing_streak"],
    best_trade=round(s["best_trade"]), net_without_best=round(s["net_without_best"]), net_without_best2=round(s["net_without_best2"]),
    big_winners=int(len(big)), big_winner_share_pct=round(100 * big.pnl_usd.sum() / s["net_pnl"]),
    ci_low=round(s["bootstrap_expectancy_ci95"][0]), ci_high=round(s["bootstrap_expectancy_ci95"][1]),
    p_le_0_pct=round(100 * s["bootstrap_p_mean_le_0"], 1), avg_risk_pct=round(s["avg_actual_risk_pct"], 2), max_risk_pct=round(s["max_actual_risk_pct"], 2),
    months_positive_pct=round(100 * s["pct_months_positive"]), round_trips_per_signal=round(s["avg_segments"]),
    gross=round(s["gross_total"]), costs=round(s["costs_total"]), roll_costs=round(s["roll_costs_total"]), rolls_crossed=s["rolls_crossed"],
    min_contracts=int(traded.contracts.min()), max_contracts=int(traded.contracts.max()), bh_contracts=BH_N,
    bh_pnl=round(bh.iloc[-1] - 100000), bh_dd_usd=round((bh - bh.cummax()).min()), bh_dd_pct=round(100 * (bh / bh.cummax() - 1).min(), 1))])
tr["start"] = pd.to_datetime(tr.signal_time, utc=True).dt.tz_convert(NY).dt.strftime("%Y-%m-%d")
tr["end"] = pd.to_datetime(tr.signal_exit_time, utc=True).dt.tz_convert(NY).dt.strftime("%Y-%m-%d")
write("trades", [dict(n=i + 1, start=r.start, end=r.end, contracts=int(r.contracts), stop_pts=round(r.stop_pts, 1), risk_pct=round(r.risk_pct_actual, 2),
                      rolls=int(r.rolls), cost=round(r.cost_usd), pnl=round(r.pnl_usd), r=round(r.r, 2),
                      exit="initial stop" if r.exit_reason == "stop" else "10-day low",
                      traded="yes" if r.contracts > 0 else "skipped", equity=round(r.equity_after)) for i, r in tr.iterrows()])
write("years", [dict(year=int(y), signals=int(v["signals"]), wins=int(v["wins"]), pnl=round(v["pnl"]), return_pct=round(v["return_pct"], 1),
                     max_dd_pct=round(v["max_dd_pct"], 1)) for y, v in s["by_year"].items()])
V = [("Main case: MES, overnight, $4 per round trip + rolls", MAIN),
     ("MES, overnight, no costs", "rep_mes_pure_skip_cost0"),
     ("MES, overnight, 2 ticks slippage ($6.50)", "rep_mes_pure_skip_cost6.5"),
     ("MES, day-trading mode, $4 per round trip", "rep_mes_dt_skip_cost4"),
     ("MES, day-trading mode, no costs", "rep_mes_dt_skip_cost0"),
     ("MES, day-trading mode, 2 ticks slippage ($6.50)", "rep_mes_dt_skip_cost6.5"),
     ("ES, overnight, skip over 2%, $30 per round trip", "rep_es_pure_skip_cost30"),
     ("ES, overnight, force 1 contract, $30", "rep_es_pure_min1_cost30"),
     ("ES, day-trading mode, force 1 contract, $30", "rep_es_dt_min1_cost30")]
rows = []
for label, f in V:
    v = json.load(open(os.path.join(res, f + "_summary.json")))
    rows.append(dict(variant=label, traded=v["signals_traded"], ending_equity=round(v["ending_equity"]), return_pct=round(v["total_return_pct"], 1),
                     profit_factor=round(v["profit_factor"], 2), mtm_dd_pct=round(v["mtm_max_dd_pct"], 1),
                     avg_risk_pct=round(v["avg_actual_risk_pct"], 2), costs=round(v["costs_total"])))
write("variants", rows, [dict(label="Costs", value="Per contract per round trip, an assumed figure for commission, fees and slippage, not a broker's quoted rate. MES $4 = $1.50 fees + 1 tick ($1.25) each side; ES $30 = $5 fees + 1 tick ($12.50) each side. Cost rows also pay one round trip per quarterly roll held through")])
for f in sorted(os.listdir(out)): print(f, os.path.getsize(os.path.join(out, f)))
