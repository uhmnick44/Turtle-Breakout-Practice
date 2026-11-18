"""Apply fixed-fractional position sizing to a signals CSV from backtest.py.
contracts = floor(risk_dollars / (initial stop distance in points * point value)).
Sizing uses the indicator's modeled entry and stop, decided at the breakout candle."""
import argparse, json, math
import pandas as pd, numpy as np
p = argparse.ArgumentParser()
p.add_argument("signals"); p.add_argument("--account", type=float, default=100000)
p.add_argument("--risk_pct", type=float, default=5.0); p.add_argument("--compound", type=int, default=1)
p.add_argument("--point_value", type=float, default=2.0); p.add_argument("--cost_rt", type=float, default=0.0)
p.add_argument("--out", required=True)
a = p.parse_args()
sig = pd.read_csv(a.signals).sort_values("signal_time").reset_index(drop=True)
eq = a.account; rows = []; peak = eq; maxdd = 0; maxdd_pct = 0
for _, s in sig.iterrows():
    risk_usd = (eq if a.compound else a.account) * a.risk_pct / 100
    per_ct = s.risk_pts * a.point_value
    n = math.floor(risk_usd / per_ct)
    pnl = n * (s.pnl_pts * a.point_value - s.segments * a.cost_rt)
    risk_taken = n * per_ct
    eq_before = eq; eq += pnl
    peak = max(peak, eq); dd = eq - peak; maxdd = min(maxdd, dd); maxdd_pct = min(maxdd_pct, dd / peak)
    rows.append(dict(signal_time=s.signal_time, contracts=n, stop_pts=round(s.risk_pts, 2), risk_usd=round(risk_taken),
                     risk_pct_actual=round(100 * risk_taken / eq_before, 2), pnl_usd=round(pnl), r=round(s.r_multiple, 2),
                     equity=round(eq), dd_from_peak=round(dd), worst_open_mae_usd=round(n * s.mae * a.point_value)))
out = pd.DataFrame(rows)
pnl = out.pnl_usd.values; w = pnl[pnl > 0]; l = pnl[pnl <= 0]
summary = dict(account=a.account, risk_pct=a.risk_pct, compound=bool(a.compound), n=len(out), skipped_zero_contracts=int((out.contracts == 0).sum()),
               contracts_min=int(out.contracts.min()), contracts_max=int(out.contracts.max()), contracts_mean=float(out.contracts.mean()),
               ending_equity=float(eq), net_pnl=float(eq - a.account), return_pct=float(100 * (eq / a.account - 1)),
               win_rate=float(len(w) / len(pnl)), avg_win=float(w.mean()), avg_loss=float(l.mean()), expectancy=float(pnl.mean()),
               profit_factor=float(w.sum() / -l.sum()), max_drawdown_usd=float(maxdd), max_drawdown_pct=float(100 * maxdd_pct),
               worst_single_loss=float(pnl.min()), best_single_win=float(pnl.max()), avg_actual_risk_pct=float(out.risk_pct_actual.mean()),
               total_without_best=float(np.sort(pnl)[:-1].sum()))
out.to_csv(a.out + ".csv", index=False); json.dump(summary, open(a.out + ".json", "w"), indent=1)
print(json.dumps(summary, indent=1))
