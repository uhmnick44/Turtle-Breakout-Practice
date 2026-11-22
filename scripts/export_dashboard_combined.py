"""Export the three-account common-window results into the JSON files the combined report page reads.
Each file is {rows, meta}; meta carries this script and the scripts that made its inputs.
Usage: python3 export_dashboard_combined.py <combined_10k results dir> <scripts dir> <out dir>"""
import sys, os, json
import pandas as pd
res, sdir, out = sys.argv[1:4]
os.makedirs(out, exist_ok=True)
code = lambda f: open(os.path.join(sdir, f)).read()
META = [dict(label=f, value=code(f), type="code", lang="python") for f in
        ["export_dashboard_combined.py", "combined_window_run.py", "combined_stats.py", "combined_r_bootstrap.py"]] + [
    dict(label="Window", value="2019-05-05 to 2026-10-20, the dates all three markets have data; each account starts at $10,000 on 2019-05-05"),
    dict(label="Cases", value="Bitcoin: MBT, 10% of closed equity, skip if 1 contract needs more, $7 RT. S&P 500: MES, 10%, skip, $4 RT plus rolls. MNQ: 1 contract on every signal, $2.50 RT. All: day-trading schedule off, level fills, Pine defaults")]
J = json.load(open(os.path.join(res, "combined_stats.json")))
def write(name, rows):
    rows = [{k: (None if isinstance(v, float) and v != v else v) for k, v in r.items()} for r in rows]
    json.dump(dict(rows=rows, meta=META), open(os.path.join(out, name + ".json"), "w"))
NAME = dict(combined="Combined, 3 accounts", btc="Bitcoin, 10% risk", sp="S&P 500, 10% risk", mnq="MNQ, 1 contract")
def acct(key, d):
    return dict(key=key, account=NAME[key], start=d["start"], end=round(d["end"]), net=round(d["net"]), ret_pct=round(d["ret"], 1), cagr_pct=round(d["cagr"], 1),
        years=round(d["years"], 2), signals=d["signals"], traded=d["traded"], skipped=d["skipped"], wins=d["wins"], losses=d["losses"],
        win_rate_pct=round(d["win_rate"], 1), avg_win=round(d["avg_win"]), avg_loss=round(d["avg_loss"]), payoff=round(d["payoff"], 2),
        exp_usd=round(d["exp_usd"]), exp_r=round(d["exp_r"], 2), median_r=round(d["median_r"], 2), pf=round(d["pf"], 2),
        best=round(d["best"]), best_r=round(d["best_r"], 2), worst=round(d["worst"]), worst_r=round(d["worst_r"], 2),
        wo_best=round(d["wo_best"]), wo_best2=round(d["wo_best2"]), top3_pct=round(d["top3"], 1),
        win_streak=d["win_streak"], lose_streak=d["lose_streak"], hold_days=round(d["hold"], 1),
        gross=round(d["gross"]), costs=round(d["costs"]), costs_pct=round(100 * d["costs"] / d["gross"], 1),
        avg_risk_pct=round(d["avg_risk"], 1), max_risk_pct=round(d["max_risk"], 1),
        dd_usd=round(d["dd_usd"]), dd_pct=round(d["dd_pct"], 1), dd_peak=d["dd_peak"], dd_trough=d["dd_trough"],
        dd_recovered=d["dd_rec"][:10] if d["dd_rec"] != "not recovered" else "not recovered", closed_dd=round(d["closed_dd"]),
        underwater_days=round(d["uw_days"]), worst_month_pct=round(d["worst_month"], 1), best_month_pct=round(d["best_month"], 1),
        months_positive_pct=round(d["months_pos"], 1), sharpe=round(d["sharpe"], 2),
        r_ci_low=round(d["ci_r"][0], 2), r_ci_high=round(d["ci_r"][1], 2), p_le0_pct=round(d["p_le0_r"], 1),
        trades_per_year=round(d["trades_per_year"], 1),
        share_pct=100.0 if key == "combined" else round(J["portfolio"]["share_of_net"][key], 1))
write("accounts", [acct("combined", J["portfolio"])] + [acct(k, J["individual_window"][k]) for k in ["btc", "sp", "mnq"]])
FN = dict(btc="Bitcoin, full 8.9 years", sp="S&P 500, full 10.1 years", mnq="MNQ, full 7.5 years")
write("fullperiod", [dict(key=k, account=FN[k], period=f"{d['period'][0]} to {d['period'][1]}".replace("2026-10-21", "2026-10-20"), years=round(d["years"], 2),
      traded=d["traded"], end=round(d["end"]), cagr_pct=round(d["cagr"], 1), pf=round(d["pf"], 2), exp_r=round(d["exp_r"], 2), dd_pct=round(d["dd_pct"], 1))
      for k, d in J["individual_full"].items()])
eq = {}
for k in ["btc", "sp", "mnq"]:
    e = pd.read_csv(os.path.join(res, f"win_{k}_equity_daily.csv")); e.columns = ["t", "v"]
    eq[k] = e.set_index(pd.to_datetime(e.t.str[:10])).v
E = pd.DataFrame(eq).sort_index().ffill().fillna(10000.0); E["total"] = E.sum(axis=1)
E["dd_pct"] = 100 * (E.total / E.total.cummax() - 1)
write("equity", [dict(date=d.strftime("%Y-%m-%d"), btc=round(r.btc), sp=round(r.sp), mnq=round(r.mnq), total=round(r.total), dd_pct=round(r.dd_pct, 2)) for d, r in E.iterrows()])
write("years", [dict(year=int(y), label=y + (" (from May 5)" if y == "2019" else " (to Oct 20)" if y == "2026" else ""), signals=v["signals"],
      pnl=round(v["total_pnl"]), ret_pct=round(v["total_ret"], 1), dd_pct=round(v["total_dd"], 1),
      btc_pnl=round(v["btc_pnl"]), btc_ret_pct=round(v["btc_ret"], 1), sp_pnl=round(v["sp_pnl"]), sp_ret_pct=round(v["sp_ret"], 1),
      mnq_pnl=round(v["mnq_pnl"]), mnq_ret_pct=round(v["mnq_ret"], 1)) for y, v in J["years"].items()])
MK = dict(btc="Bitcoin", sp="S&P 500", mnq="MNQ")
write("trades", [dict(n=i + 1, market=MK[t["m"]], start=t["s"], end=t["e"], contracts=t["c"], risk_pct=t["risk"], pnl=t["pnl"], r=t["r"], exit=t["x"]) for i, t in enumerate(J["tradelist"])])
c = J["monthly_corr"]
write("corr", [dict(pair="Bitcoin and S&P 500", corr=round(c["btc-sp"], 2)), dict(pair="Bitcoin and MNQ", corr=round(c["btc-mnq"], 2)), dict(pair="S&P 500 and MNQ", corr=round(c["sp-mnq"], 2))])
for f in sorted(os.listdir(out)): print(f, os.path.getsize(os.path.join(out, f)))
