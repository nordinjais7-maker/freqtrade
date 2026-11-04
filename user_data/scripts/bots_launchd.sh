#!/usr/bin/env bash
# Run the DailyTrend dry-run bots (BTC and SUI) as macOS launchd jobs.
#
#   bash user_data/scripts/bots_launchd.sh install    # stop Terminal copies, install, start
#   bash user_data/scripts/bots_launchd.sh status     # is each job running? last log lines
#   bash user_data/scripts/bots_launchd.sh restart    # e.g. after git pull changed the strategy
#   bash user_data/scripts/bots_launchd.sh uninstall  # stop and remove the jobs
#
# launchd keeps exactly one copy of each bot running, starts it at login and
# restarts it within a minute if it exits. The bots keep using their own
# databases, so the dry run continues where it left off.
# Logs: user_data/logs/dailytrend_<btc|sui>.log (plus .err for crash output).
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
FREQTRADE="$REPO/.venv/bin/freqtrade"
AGENTS="${LAUNCHD_AGENTS_DIR:-$HOME/Library/LaunchAgents}"
LOGS="$REPO/user_data/logs"
DOMAIN="gui/$(id -u)"
DRY="${LAUNCHD_DRY_RUN:-0}"   # 1 = write plists only (for testing)

BOTS=(btc sui)
config_for() { case "$1" in btc) echo user_data/config_dailytrend_dryrun.json ;;
                              sui) echo user_data/config_dailytrend_sui.json ;; esac; }
label_for() { echo "com.freqtrade.dailytrend.$1"; }
plist_for() { echo "$AGENTS/$(label_for "$1").plist"; }

write_plist() {
  local bot=$1 cfg label
  cfg=$(config_for "$bot"); label=$(label_for "$bot")
  cat > "$(plist_for "$bot")" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>$label</string>
  <key>WorkingDirectory</key><string>$REPO</string>
  <key>ProgramArguments</key>
  <array>
    <string>/usr/bin/caffeinate</string>
    <string>-i</string>
    <string>$FREQTRADE</string>
    <string>trade</string>
    <string>--config</string><string>$cfg</string>
    <string>--userdir</string><string>user_data</string>
    <string>--strategy</string><string>DailyTrend</string>
    <string>--logfile</string><string>$LOGS/dailytrend_$bot.log</string>
  </array>
  <key>RunAtLoad</key><true/>
  <key>KeepAlive</key><true/>
  <key>ThrottleInterval</key><integer>60</integer>
  <key>ProcessType</key><string>Background</string>
  <key>StandardOutPath</key><string>$LOGS/dailytrend_$bot.out</string>
  <key>StandardErrorPath</key><string>$LOGS/dailytrend_$bot.err</string>
</dict>
</plist>
EOF
}

stop_terminal_copies() {
  # Bots started by hand in Terminal would duplicate the launchd ones.
  local bot cfg pids
  for bot in "${BOTS[@]}"; do
    cfg=$(config_for "$bot")
    pids=$(pgrep -f "python.*freqtrade trade --config $cfg" || true)
    if [[ -n "$pids" ]]; then
      echo "  stopping Terminal-started $bot bot (pid $(echo $pids | tr '\n' ' '))"
      kill -INT $pids 2>/dev/null || true
    fi
  done
  for _ in $(seq 1 20); do   # wait up to 20 s for a clean shutdown
    pgrep -f "python.*freqtrade trade --config user_data/config_dailytrend_" >/dev/null || return 0
    sleep 1
  done
  echo "  still running after 20 s; forcing stop"
  pkill -KILL -f "python.*freqtrade trade --config user_data/config_dailytrend_" || true
}

unload() {
  local bot=$1
  launchctl bootout "$DOMAIN/$(label_for "$bot")" 2>/dev/null || true
}

cmd_install() {
  [[ -x "$FREQTRADE" ]] || { echo "Not found: $FREQTRADE (run from the freqtrade repo with .venv)"; exit 1; }
  mkdir -p "$AGENTS" "$LOGS"
  if [[ "$DRY" == 1 ]]; then
    for bot in "${BOTS[@]}"; do write_plist "$bot"; echo "  wrote $(plist_for "$bot")"; done
    return
  fi
  echo "Stopping any existing copies ..."
  for bot in "${BOTS[@]}"; do unload "$bot"; done
  stop_terminal_copies
  echo "Installing and starting ..."
  for bot in "${BOTS[@]}"; do
    write_plist "$bot"
    plutil -lint -s "$(plist_for "$bot")"
    launchctl bootstrap "$DOMAIN" "$(plist_for "$bot")"
    echo "  started $(label_for "$bot")"
  done
  sleep 5
  cmd_status
}

cmd_status() {
  local bot label state pid
  for bot in "${BOTS[@]}"; do
    label=$(label_for "$bot")
    echo "=== $bot ($label)"
    if launchctl print "$DOMAIN/$label" >/tmp/.ft_launchd_$$ 2>/dev/null; then
      state=$(awk -F'= ' '/^\tstate =/{print $2; exit}' /tmp/.ft_launchd_$$)
      pid=$(awk -F'= ' '/^\tpid =/{print $2; exit}' /tmp/.ft_launchd_$$)
      echo "  state: ${state:-unknown}   pid: ${pid:-none}"
    else
      echo "  not installed"
    fi
    rm -f /tmp/.ft_launchd_$$
    [[ -f "$LOGS/dailytrend_$bot.log" ]] && tail -n 3 "$LOGS/dailytrend_$bot.log" | sed 's/^/  | /'
  done
  echo "Copies running: $(pgrep -f 'python.*freqtrade trade --config user_data/config_dailytrend_' | wc -l | tr -d ' ') (expect 2)"
}

cmd_restart() {
  for bot in "${BOTS[@]}"; do
    launchctl kickstart -k "$DOMAIN/$(label_for "$bot")" && echo "  restarted $bot"
  done
}

cmd_uninstall() {
  for bot in "${BOTS[@]}"; do
    unload "$bot"
    rm -f "$(plist_for "$bot")"
    echo "  removed $(label_for "$bot")"
  done
}

case "${1:-}" in
  install) cmd_install ;;
  status) cmd_status ;;
  restart) cmd_restart ;;
  uninstall) cmd_uninstall ;;
  *) sed -n '2,13p' "$0"; exit 1 ;;
esac
