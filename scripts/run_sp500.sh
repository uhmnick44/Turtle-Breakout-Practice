#!/usr/bin/env bash
# Turtle Breakout - Revelio on S&P 500 futures: $100k, 2% risk, slippage + fees.
#
# Input: Databento GLBX.MDP3 ohlcv-1m for MES.FUT (or ES.FUT), CSV encoding
# (.csv.zst), unpacked into one or more folders under data/<root>/raw*/.
#
# Usage:  ROOT=mes bash scripts/run_sp500.sh data/mes/raw1 [data/mes/raw2 ...]
#         ROOT=es  bash scripts/run_sp500.sh data/es/raw1
#
# Cost model (all assumptions, set them to your broker's real numbers):
#   SLIP_TICKS  slippage per side, in ticks (default 1). Breakout entries and
#               stop exits are stop orders, so they fill worse, not better.
#   FEES_RT     commission + exchange + NFA fees per contract round trip, in $.
#               Default is a placeholder, not any broker's quoted rate.
# Every scheduled close/re-entry in day-trading mode is a separate round trip
# and pays the full cost again.
set -euo pipefail
ROOT=${ROOT:-mes}
case "$ROOT" in
  mes) PV=5;  TICK=1.25;  FEES_RT=${FEES_RT:-1.50} ;;
  es)  PV=50; TICK=12.50; FEES_RT=${FEES_RT:-5.00} ;;
  *) echo "ROOT must be mes or es"; exit 1 ;;
esac
SLIP_TICKS=${SLIP_TICKS:-1}
COST_RT=$(python3 -c "print(2*$SLIP_TICKS*$TICK + $FEES_RT)")
D=data/$ROOT; R=results/turtle_breakout_revelio/sp500_$ROOT; mkdir -p "$D" "$R"

OUT=$D/raw.parquet python3 scripts/decode_csv.py "$@"
python3 scripts/build_continuous.py "$D/raw.parquet" "$D"
python3 scripts/resample.py "$D/${ROOT}_1m_continuous.parquet" "$D/${ROOT}_30m_continuous.csv" x "$D/raw.parquet"
BARS=$D/${ROOT}_30m_continuous.csv

for mode in dt pure; do
  DTF=$([ $mode = dt ] && echo 1 || echo 0)
  python3 scripts/backtest.py "$BARS" --out "$R/bt_${mode}_level" --daytrading $DTF --pv $PV > /dev/null
  for pol in skip min1; do
    python3 scripts/report.py "$R/bt_${mode}_level" "$BARS" --pv $PV --risk_pct 2 --account 100000 \
      --compound 1 --policy $pol --out "$R/rep_${mode}_${pol}_nocost" > /dev/null
    python3 scripts/report.py "$R/bt_${mode}_level" "$BARS" --pv $PV --risk_pct 2 --account 100000 \
      --compound 1 --policy $pol --cost_rt "$COST_RT" --out "$R/rep_${mode}_${pol}_cost"
  done
done
echo "cost per contract round trip: \$$COST_RT ($SLIP_TICKS tick/side slippage + \$$FEES_RT fees)"
