#!/usr/bin/env bash
# Download 12 months of SUI/USDT:USDT Binance USDT-M futures data and backtest
# the SessionSweep strategy. Run from the repository root on a machine that can
# reach Binance (e.g. your Mac):
#
#   source .venv/bin/activate      # or however you activate freqtrade
#   bash user_data/scripts/sessionsweep_backtest.sh
#
# Override the window with: TIMERANGE=20250101-20251231 bash user_data/scripts/...
set -euo pipefail

CONFIG=user_data/config_sessionsweep.json
PAIR="SUI/USDT:USDT"
# Last 12 months by default (macOS `date -v`, GNU `date -d` fallback)
END=$(date -u +%Y%m%d)
START=$(date -u -v-365d +%Y%m%d 2>/dev/null || date -u -d '365 days ago' +%Y%m%d)
TIMERANGE=${TIMERANGE:-"${START}-${END}"}

echo ">>> 1/3 Downloading 5m + 1h futures candles (plus mark & funding) for ${PAIR}"
# --timerange is padded by ~10 days so the strategy's startup candles are available.
PAD_START=$(date -u -v-375d +%Y%m%d 2>/dev/null || date -u -d '375 days ago' +%Y%m%d)
freqtrade download-data \
    --config "${CONFIG}" --userdir user_data \
    --pairs "${PAIR}" \
    --timeframes 5m 1h \
    --timerange "${PAD_START}-${END}" \
    --trading-mode futures

echo ">>> 2/3 Backtesting ${TIMERANGE}"
freqtrade backtesting \
    --config "${CONFIG}" --userdir user_data \
    --strategy SessionSweep \
    --timerange "${TIMERANGE}" \
    --breakdown month \
    --export trades \
    --notes "SessionSweep baseline ${TIMERANGE}"

echo ">>> 3/3 Session split (enter_tag = london_* / ny_*) and exit-reason breakdown"
# Group 1 = per enter_tag, group 2 = per enter_tag + exit_reason.
freqtrade backtesting-analysis \
    --config "${CONFIG}" --userdir user_data \
    --analysis-groups 1 2
