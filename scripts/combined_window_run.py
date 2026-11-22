"""Re-run each market's report on a common window, then write 30-min MTM equity too."""
import pandas as pd, subprocess, os, sys
S = sys.argv[1]; W = S + "/work/"
START = pd.Timestamp("2019-05-05 22:00", tz="UTC"); END = pd.Timestamp("2026-10-21 00:00", tz="UTC")
cases = {
 "btc": dict(br="turtle-break-backtest-0mczq8", bt="results/turtle_breakout_revelio/btc_2017_2026/bt_pure_level",
             bars="data/btc/btc_30m_continuous.csv", args="--account 10000 --risk_pct 10 --compound 1 --policy skip --cost_rt 7 --pv 0.1",
             full="results/turtle_breakout_revelio/btc_2017_2026/10k/rep_mbt_pure_level_cost7_risk10"),
 "sp":  dict(br="gallant-einstein-ls8ow1", bt="results/turtle_breakout_revelio/sp500/bt_pure_level",
             bars="data/es/es_30m_continuous.csv", args="--account 10000 --risk_pct 10 --compound 1 --policy skip --cost_rt 4 --pv 5 --rolls data/es/es_rolls.csv",
             full="results/turtle_breakout_revelio/sp500/rep10k_mes_pure_skip_cost4"),
 "mnq": dict(br="tender-archimedes-tdtqme", bt=W + "mnq_bt_pure_level",
             bars="data/mnq/mnq_30m_continuous.csv", args="--account 10000 --risk_pct 2 --compound 1 --policy min1 --cost_rt 2.5 --pv 2",
             full="results/turtle_breakout_revelio/2019_2026/10k/rep10k_pure_level_min1_cost2.5"),
}
for k, c in cases.items():
    d = os.path.join(S, c["br"]); bt = c["bt"] if c["bt"].startswith("/") else os.path.join(d, c["bt"])
    src = open(os.path.join(d, "scripts/report.py")).read() + '\neqdf.to_csv(a.out + "_equity_30m.csv", index=False)\n'
    open(W + f"report_{k}.py", "w").write(src)
    sig = pd.read_csv(bt + "_signals.csv"); seg = pd.read_csv(bt + "_segments.csv")
    st = pd.to_datetime(sig.signal_time, utc=True)
    keep = (st >= START) & (st < END)
    sig[keep].to_csv(W + f"win_{k}_signals.csv", index=False)
    seg[pd.to_datetime(seg.signal_time, utc=True).isin(st[keep])].to_csv(W + f"win_{k}_segments.csv", index=False)
    b = pd.read_csv(os.path.join(d, c["bars"])); t = pd.to_datetime(b.time_open, utc=True)
    b[(t >= START) & (t + pd.Timedelta(minutes=30) <= END)].to_csv(W + f"win_{k}_bars.csv", index=False)
    # full-period run too (reproduces committed result + 30m curve)
    for tag, pre, bars in [("win", W + f"win_{k}", W + f"win_{k}_bars.csv"), ("full", bt, os.path.join(d, c["bars"]))]:
        cmd = f"python3 {W}report_{k}.py {pre} {bars} {c['args']} --out {W}rep/{tag}_{k}"
        subprocess.run(cmd, shell=True, cwd=d, check=True, stdout=subprocess.DEVNULL)
    print(k, "dropped signals before window:", int((st < START).sum()), "kept:", int(keep.sum()))
