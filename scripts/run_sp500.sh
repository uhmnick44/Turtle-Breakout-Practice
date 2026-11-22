#!/usr/bin/env bash
# Turtle Breakout - Revelio on S&P 500 futures: $100k, 2% of closed equity per signal, slippage + fees.
# Input: Databento GLBX.MDP3 ohlcv-1m ES.FUT, CSV encoding (.csv.zst), unpacked into data/es/raw/.
# Usage: bash scripts/run_sp500.sh
#
# Prices are ES. Results are sized two ways on the same prices: ES ($50/pt, tick $12.50) and
# MES ($5/pt, tick $1.25). MES only listed 2019-05, so pre-2019 MES results are ES prices at $5/pt.
# Costs per contract round trip = 2 x SLIP_TICKS x tick value + fees (assumptions, not quotes):
#   ES  $5.00 fees + 1 tick/side -> $30      MES $1.50 fees + 1 tick/side -> $4
# Cost runs also pay one round trip per contract for each quarterly roll a held position spans.
set -euo pipefail
D=data/es; R=results/turtle_breakout_revelio/sp500; mkdir -p "$R"
SLIP_TICKS=${SLIP_TICKS:-1}; ES_FEES=${ES_FEES:-5.00}; MES_FEES=${MES_FEES:-1.50}
OUT=$D/raw.parquet python3 scripts/decode_csv.py $D/raw
DROP_HALT=1 python3 scripts/build_continuous.py $D/raw.parquet $D
python3 scripts/resample.py $D/es_1m_continuous.parquet $D/es_30m_continuous.csv x $D/raw.parquet
B=$D/es_30m_continuous.csv
for mode in dt pure; do
  python3 scripts/backtest.py $B --out $R/bt_${mode}_level --daytrading $([ $mode = dt ] && echo 1 || echo 0) --pv 50 > /dev/null
done
ES_RT=$(python3 -c "print('%g' % (2*$SLIP_TICKS*12.5+$ES_FEES))"); MES_RT=$(python3 -c "print('%g' % (2*$SLIP_TICKS*1.25+$MES_FEES))")
for c in "es 50 $ES_RT" "mes 5 $MES_RT"; do set -- $c
  for mode in dt pure; do for pol in skip min1; do for cost in 0 $3; do
    python3 scripts/report.py $R/bt_${mode}_level $B --pv $2 --risk_pct 2 --account 100000 --compound 1 \
      --policy $pol --cost_rt $cost $([ $cost != 0 ] && echo --rolls $D/es_rolls.csv) --out $R/rep_${1}_${mode}_${pol}_cost$cost > /dev/null
  done; done; done
done
