import json, numpy as np, pandas as pd, sys
W=sys.argv[1]; J=json.load(open(sys.argv[2]))
rng=np.random.default_rng(11)
for tag,key in [("full","individual_full"),("win","individual_window")]:
    for k in ["btc","sp","mnq"]:
        t=pd.read_csv(f"{W}/{tag}_{k}_trades.csv"); t=t[t.contracts>0]; r=t.r.values
        b=np.array([rng.choice(r,len(r)).mean() for _ in range(20000)])
        J[key][k]["ci_r"]=[float(np.percentile(b,2.5)),float(np.percentile(b,97.5))]; J[key][k]["p_le0_r"]=100*float((b<=0).mean())
tl=pd.DataFrame(J["tradelist"]); J["portfolio"]["avg_risk"]=float(tl.risk.mean()); J["portfolio"]["max_risk"]=float(tl.risk.max())
json.dump(J,open(sys.argv[2],"w"))
for key in ["individual_window","individual_full"]:
    for k,v in J[key].items(): print(key,k,[round(x,2) for x in v["ci_r"]],round(v["p_le0_r"],2),round(v["exp_r"],2))
print(J["portfolio"]["ci_r"],J["portfolio"]["avg_risk"],J["portfolio"]["max_risk"])
