"""Monte Carlo of position-risk choices for an account trading the backtest's signals.
Resamples whole signals with replacement (stop distance and P&L per contract kept together),
sizes each one with floor(risk% of closed equity / per-contract risk), skips when 0 contracts.
Closed-trade equity only: drawdowns here understate mark-to-market drawdowns.
Usage: python3 mc_risk.py signals.csv --account 10000 --pv 0.1 --cost_rt 7 --out out.json"""
import argparse, json, math
import numpy as np, pandas as pd
p = argparse.ArgumentParser()
p.add_argument("signals"); p.add_argument("--account", type=float, default=10000); p.add_argument("--pv", type=float, default=0.1)
p.add_argument("--cost_rt", type=float, default=7.0); p.add_argument("--paths", type=int, default=20000); p.add_argument("--out", required=True)
p.add_argument("--risks", default="0.5,1,1.5,2,2.5,3,4,5,6,8,10")
a = p.parse_args()
s = pd.read_csv(a.signals)
risk_ct = (s.risk_pts * a.pv).values                       # $ risked per contract
pnl_ct = (s.pnl_pts * a.pv - s.segments * a.cost_rt).values  # $ result per contract after costs
order = np.argsort(pnl_ct / risk_ct)
pools = {"all signals": np.arange(len(s)), "without the best 3": order[:-3], "without the best 5": order[:-5]}
rng = np.random.default_rng(7)
N = len(s)
out = {}
for pname, pool in pools.items():
    idx = rng.choice(pool, size=(a.paths, N))
    for r in [float(x) for x in a.risks.split(",")]:
        eq = np.full(a.paths, a.account); peak = eq.copy(); mdd = np.zeros(a.paths); traded = np.zeros(a.paths)
        for k in range(N):
            rc, pc = risk_ct[idx[:, k]], pnl_ct[idx[:, k]]
            n = np.floor(eq * r / 100 / rc); n[eq <= 0] = 0
            eq = eq + n * pc; traded += n > 0
            peak = np.maximum(peak, eq); mdd = np.minimum(mdd, eq / peak - 1)
        out.setdefault(pname, {})[r] = dict(
            median_end=float(np.median(eq)), p5_end=float(np.percentile(eq, 5)), p_loss=float((eq < a.account).mean()),
            median_dd_pct=float(100 * np.median(mdd)), p95_dd_pct=float(100 * np.percentile(mdd, 5)),
            p_dd_30=float((mdd <= -0.30).mean()), p_dd_50=float((mdd <= -0.50).mean()),
            median_traded=float(np.median(traded)), median_growth_per_signal=float(np.median((eq / a.account) ** (1 / N) - 1)))
# Kelly-style log-growth optimum on the observed R multiples (no rounding, no skips)
R = pnl_ct / risk_ct
f = np.arange(0.005, 0.5, 0.005)
g = [np.mean(np.log1p(x * R)) if (1 + x * R).min() > 0 else -np.inf for x in f]
kelly = dict(all=float(f[int(np.argmax(g))]))
for nm, k in [("without_best3", 3), ("without_best5", 5)]:
    Rk = np.sort(R)[:-k]; gk = [np.mean(np.log1p(x * Rk)) if (1 + x * Rk).min() > 0 else -np.inf for x in f]
    kelly[nm] = float(f[int(np.argmax(gk))]) if max(gk) > 0 else 0.0
json.dump(dict(params=vars(a), kelly_fraction=kelly, results=out), open(a.out, "w"), indent=1)
print("kelly", kelly)
for pname, d in out.items():
    print("\n", pname); print(" risk  med_end   p5_end  P(loss) medDD  95%DD  P(DD>30) P(DD>50) med_traded")
    for r, v in d.items():
        print(f" {r:>4} {v['median_end']:>8.0f} {v['p5_end']:>8.0f} {v['p_loss']:>6.1%} {v['median_dd_pct']:>6.1f} {v['p95_dd_pct']:>6.1f} {v['p_dd_30']:>7.1%} {v['p_dd_50']:>7.1%} {v['median_traded']:>5.0f}")
