# SessionSweep – notes

Session-timing liquidity-sweep strategy for Freqtrade, built for
**SUI/USDT:USDT** (Binance USDT-M perpetual), 5m timeframe, 1h informative.

| File | Purpose |
|---|---|
| `user_data/strategies/SessionSweep.py` | The sweep-and-reclaim strategy (all logic + parameters, heavily commented) |
| `user_data/strategies/SessionMomentum.py` | The Asia-range breakout momentum strategy (section 4e) |
| `user_data/strategies/SessionSweep1h.py`, `SessionMomentum1h.py` | The same two strategies on 1-hour candles (section 4f) |
| `user_data/strategies/SuiFlushShort.py`, `config_suiflush.json` | The uploaded SUI flush-short playbook port, reviewed and extended (section 4g) |
| `user_data/scripts/fetch_okx_flow.py`, `fetch_binance_flow.py` | Hourly long/short-ratio + open-interest history from OKX (~60 days) or Binance (years) |
| `user_data/strategies/FlushReversal.py`, `config_flushrev.json`, `scripts/fetch_binance_taker.py` | Limit-order fade after taker-driven flushes, pre-registered (section 4h) |
| `user_data/strategies/DailyTrend.py` | Freqtrade version of the section 4j long/flat trend ensemble (vol-targeted, rebalancing band) |
| `user_data/scripts/trend_crosscheck.py` | Rebuilds DailyTrend's daily equity from backtest orders and compares it with `trend_backtest.py` |
| `user_data/scripts/trend_backtest.py` | Standalone daily trend-ensemble backtest with vol-targeting and controls, pre-registered (section 4j) |
| `user_data/scripts/carry_backtest.py` | Standalone spot-long / perp-short funding-carry backtest, pre-registered (section 4i) |
| `user_data/config_sessionsweep.json` | Futures / isolated / dry-run config, 1 open trade, **API keys are placeholders** |
| `user_data/scripts/sessionsweep_backtest.sh` | Exact download + backtest + session-split commands for your Mac |
| `user_data/scripts/sessionsweep_variants.py` | Runs a batch of parameter variants and prints one comparison table |
| `user_data/scripts/sessionsweep_timing.py` | Hour / session / weekday / exit / hold-time breakdown of a backtest result |
| `user_data/scripts/sessionsweep_smoke_backtest.py` | Offline plumbing test on synthetic candles (no network needed) |
| `user_data/NOTES.md` | This file |

No Freqtrade core code was touched. Freqtrade `2026.10` (the `stable` branch) was used.

---

## 1. Strategy logic

1. **Asia range.** For every UTC day, the running high/low of candles whose open
   time is inside `[asia_start, asia_end)` (default 00:00–07:00). The values are
   cumulative *inside* the window and only used after it closes (`asia_done`),
   so no candle ever sees its own future.
2. **Sweep + reclaim** (only while in London `[07:00, 12:00)` or NY `[12:30, 17:00)`):
   * **Short:** highest high of the last `sweep_lookback` post-Asia candles is
     above `asia_high` (× `1 + sweep_min_pct`) **and** the current candle
     *closes* below `asia_high`.
   * **Long:** mirror image on `asia_low`.
   * The signal fires on the first candle where this state becomes true
     (edge-triggered). If price pokes back out and reclaims again a new signal
     can fire, as long as the sweep is still inside the lookback.
3. **Stop loss** = sweep wick extreme ± `stop_buffer_pct` (price %). It is set
   with `custom_stoploss()` via `stoploss_from_absolute(..., leverage=...)`.
   The class-level `stoploss = -0.15` is only a hard cap (15% of stake = 5% price at 3x).
4. **Take profit** = opposite side of the Asia range, scaled by
   `tp_range_fraction` (1.0 = full range, 0.5 = mid-range). Implemented with
   `custom_roi()`, so the backtester checks it against candle high/low like a
   limit order. `minimal_roi` is set to an unreachable value.
5. **Trailing options**
   * `breakeven_at_midrange` – move stop to entry once price reaches the Asia midpoint.
   * Freqtrade's native `trailing_stop*` attributes are present in the class
     (off by default). They combine with the custom stop; Freqtrade keeps whichever is tighter.
   * `exit_at_session_end` + `flat_time_min` – optional time-based flatten (default off).
6. **Filters:** `asia_range_min_pct` (skip tiny ranges), `max_stop_distance_pct`
   (skip setups with a far stop), `min_rr` (minimum TP/stop ratio), and the
   optional **1h EMA trend filter** (`use_trend_filter`, `trend_ema_len`):
   longs only above the 1h EMA, shorts only below.
7. **Risk settings:** `max_open_trades = 1`, `margin_mode = isolated`,
   leverage from `leverage_level` (default 3x, capped by the exchange max).
8. **Entry tags** `london_long / london_short / ny_long / ny_short` make the
   backtest report split results by session automatically ("ENTER TAG STATS").

### Freqtrade conventions worth remembering

* `stoploss`, `custom_stoploss` and `custom_roi` values are **stake-relative**
  (already multiplied by leverage). A 1% price stop at 3x shows as −3% in reports.
* Profit ratios include fees, so the ROI exit triggers a hair *after* the exact
  target price (the smoke test measured a mean deviation of 0.005%).
* Entries are limit orders at the open of the candle **after** the signal candle.

---

## 2. Parameters

All are Freqtrade strategy parameters. Override without editing code by creating
`user_data/strategies/SessionSweep.json` (hyperopt output format), e.g.

```json
{ "strategy_name": "SessionSweep",
  "params": { "buy": { "sweep_lookback": 3, "use_trend_filter": true }, "sell": { "tp_range_fraction": 0.75 } } }
```

The `strategy_name` field is required; without it Freqtrade refuses the file.

Times are **minutes after 00:00 UTC** (420 = 07:00). Windows are `[start, end)`.

| Parameter | Space | Default | Meaning |
|---|---|---|---|
| `asia_start_min` / `asia_end_min` | buy | 0 / 420 | Asia window 00:00–07:00 |
| `london_start_min` / `london_end_min` | buy | 420 / 720 | London window 07:00–12:00 |
| `ny_start_min` / `ny_end_min` | buy | 750 / 1020 | New York window 12:30–17:00 |
| `trade_london` / `trade_ny` | buy | true / true | Enable trading in each session |
| `sweep_lookback` | buy | 6 | Max candles between sweep wick and reclaiming close (1 = same candle) |
| `sweep_min_pct` | buy | 0.0 | Min penetration beyond the Asia level, % of price |
| `asia_range_min_pct` | buy | 0.3 | Skip days whose Asia range is smaller than this % |
| `max_stop_distance_pct` | buy | 2.0 | Skip setups whose stop is further than this % from entry |
| `min_rr` | buy | 0.0 | Min reward:risk (TP distance / stop distance); 0 = off |
| `use_trend_filter` / `trend_ema_len` | buy | false / 50 | 1h EMA direction filter |
| `leverage_level` | buy | 3.0 | Leverage (isolated) |
| `stop_buffer_pct` | sell | 0.15 | Stop buffer beyond the sweep wick, % of price |
| `tp_range_fraction` | sell | 1.0 | TP distance as a fraction of the Asia range |
| `breakeven_at_midrange` | sell | false | Move stop to entry at the Asia midpoint |
| `exit_at_session_end` / `flat_time_min` | sell | false / 1020 | Time-based flatten at 17:00 UTC |

Class attributes you may also tune: `stoploss` (hard cap, −0.15),
`trailing_stop`, `trailing_stop_positive` (0.03), `trailing_stop_positive_offset` (0.06),
`startup_candle_count` (720 = enough for a 50-period 1h EMA).

---

## 3. Backtest status

### What happened in the build environment

(The real result is in section 4.)

Outbound connections to `api.binance.com`, `fapi.binance.com` and
`data.binance.vision` were refused by the sandbox proxy, so **no real market
data could be downloaded** and no real 12-month result exists yet.

What *was* verified here:

* `python -m py_compile`, `ruff check` and `ruff format` pass.
* `freqtrade list-strategies` loads the strategy (16 buy + 5 sell parameters).
* The config validates in futures / isolated mode.
* `user_data/scripts/sessionsweep_smoke_backtest.py` ran the **real backtester**
  end to end on 365 days of synthetic random-walk SUI candles (5m, 1h, mark,
  funding). On that data: 1211 trades, both sessions and both directions fired,
  entries only at 07–11 UTC (London tags) and 12–16 UTC (NY tags).
* Cross-checking the exported trades against the signal candles:
  every stop exit filled exactly at `sweep wick ± buffer`, every ROI exit at the
  opposite Asia side (max deviation 0.13%), and every signal candle satisfied
  the sweep-and-reclaim condition.

> The synthetic P&L is negative, as it must be for a mean-reversion rule on
> a memory-less random walk. It says nothing about SUI. Do not read it as a result.

### Run the real backtest on your Mac

From the repo root, with your freqtrade virtualenv active
(`source .venv/bin/activate`), either run the script:

```bash
bash user_data/scripts/sessionsweep_backtest.sh
```

or step by step:

```bash
freqtrade download-data --config user_data/config_sessionsweep.json --userdir user_data \
  --pairs "SUI/USDT:USDT" --timeframes 5m 1h 4h --trading-mode futures \
  --timerange 20251021-20261031
```

```bash
freqtrade backtesting --config user_data/config_sessionsweep.json --userdir user_data \
  --strategy SessionSweep --timerange 20251031-20261031 \
  --breakdown month --cache none --export signals --notes "SessionSweep baseline"
```

```bash
freqtrade backtesting-analysis --config user_data/config_sessionsweep.json --userdir user_data \
  --analysis-groups 1 2
```

Where to read the numbers you asked for:

| Metric | Where |
|---|---|
| Number of trades, win rate | `BACKTESTING REPORT` → Trades / Win% |
| Profit factor | `SUMMARY METRICS` → Profit factor (and per month in `MONTH BREAKDOWN`) |
| Max drawdown | `SUMMARY METRICS` → Absolute drawdown / Max % of account underwater |
| London vs NY | `ENTER TAG STATS` (tags `london_*` vs `ny_*`), or `backtesting-analysis --analysis-groups 1` |

Useful variants:

```bash
# London only: write a parameter file next to the strategy, then backtest as usual
echo '{"strategy_name": "SessionSweep", "params": {"buy": {"trade_ny": false}}}' > user_data/strategies/SessionSweep.json
freqtrade backtesting --config user_data/config_sessionsweep.json --userdir user_data \
  --strategy SessionSweep --timerange 20251031-20261031
```

(Use `"trade_london": false` for NY only; delete the JSON file to go back to defaults.)

```bash
# Interactive chart with Asia levels and trades
freqtrade plot-dataframe --config user_data/config_sessionsweep.json --userdir user_data \
  --strategy SessionSweep --pairs "SUI/USDT:USDT" --timerange 20261001-20261031
```

```bash
# Hyperopt the optimize=True parameters (lookback, buffers, filters, TP fraction)
freqtrade hyperopt --config user_data/config_sessionsweep.json --userdir user_data \
  --strategy SessionSweep --hyperopt-loss SortinoHyperOptLoss \
  --spaces buy sell --timerange 20251031-20261031 -e 300
```

```bash
# Dry run (no keys needed for dry-run on Binance futures)
freqtrade trade --config user_data/config_sessionsweep.json --userdir user_data --strategy SessionSweep
```

If `download-data` says funding data is missing for early dates, add
`"futures_funding_rate": 0` to the config (Freqtrade then assumes zero funding
where no history exists).

---

## 4. Real baseline result (Binance, 2025-10-31 to 2026-10-31)

Run on a Mac with the default parameters, 3x leverage, 1000 USDT, full balance per trade.
SUI fell about 60% over this window.

| Metric | Value |
|---|---|
| Trades | 582 (1 still open at the end) |
| Win rate | 25.8% |
| Profit factor | 0.99 |
| Total profit | −10.2% |
| Max drawdown | 79.7% (equity peaked at 3204 USDT in March 2026, then fell to 465) |
| Longest losing streak | 21 |
| Avg winner / avg loser (stake-relative) | +7.85% / −2.59% |

| Session | Trades | Win rate | Net USDT | Profit factor (approx.) |
|---|---|---|---|---|
| London | 299 | 22.4% | −530 | 0.93 |
| New York | 283 | 29.3% | +429 | 1.05 |

| Entry tag | Trades | Win rate | Net USDT |
|---|---|---|---|
| ny_short | 138 | 33.3% | +717 |
| london_short | 147 | 23.8% | −106 |
| ny_long | 145 | 25.5% | −289 |
| london_long | 152 | 21.1% | −424 |

Every exit was either the take profit (150) or the stop (431). Trades often run
for many hours and sometimes days, well past the session they started in.

### What it means

* **No edge yet.** Winners are 3× losers, but a 25.8% win rate exactly cancels that.
  The p-value of the mean trade is 0.95, so the result is indistinguishable from noise.
* **The drawdown is mostly sizing.** Each trade risks the full balance at 3x, so a
  21-loss streak is brutal. Profit factor and win rate are the numbers to compare.
* **Shorts won, longs lost, in a market down 60%.** That points at the 1h trend
  filter, but it may simply reflect this one bearish year.
* **New York beat London**, mainly through NY shorts. Early London sweeps are often
  the start of the real move rather than a fake-out.

Choosing "NY shorts only" from this table would be fitting to one year of data.
Any variant that looks better must be checked on a different period before trusting it.

### First variant sweep (same window, run on the Mac)

| Variant | Trades | Win % | PF | Profit % | Max DD % | London PF | NY PF |
|---|---|---|---|---|---|---|---|
| baseline | 582 | 25.8 | 0.99 | −10.2 | 79.7 | 0.93 | 1.05 |
| ny_only | 374 | 26.5 | 0.98 | −24.8 | 80.2 | – | 0.98 |
| london_only | 323 | 22.9 | 0.92 | −31.7 | 56.0 | 0.92 | – |
| **trend_1h** | **191** | **29.3** | **1.22** | **+79.3** | **23.6** | **1.12** | **1.31** |
| ny_only_trend | 119 | 29.4 | 1.10 | +25.2 | 24.2 | – | 1.10 |
| min_rr_1.5 | 567 | 24.9 | 1.03 | +50.6 | 67.9 | 0.88 | 1.18 |
| lookback_1 | 730 | 20.8 | 0.98 | −32.2 | 79.2 | 0.71 | 1.20 |
| range_min_0.6 | 582 | 25.8 | 0.99 | −10.2 | 79.7 | 0.93 | 1.05 |
| tp0.75_breakeven | 713 | 22.6 | 0.88 | −68.4 | 74.2 | 0.84 | 0.91 |
| flat_at_17utc | 634 | 31.7 | 1.01 | +9.0 | 47.5 | 1.02 | 1.00 |

What changed the picture:

* **The 1h trend filter is the only clear improvement.** Profit factor rose from 0.99
  to 1.22, drawdown fell from 80% to 24%, and *both* sessions turned positive.
  It also has a mechanical reason: it stops fading sweeps that are really the
  start of a trend move.
* **"NY beats London" did not survive.** NY only made 374 trades versus 283 inside
  the baseline, because with one open trade allowed, London trades were blocking
  NY entries. Run alone, NY has PF 0.98. The baseline session split is confounded.
* **`asia_range_min_pct` 0.6 changed nothing.** SUI's Asia range is almost always
  wider than 0.6%, so the filter never bites. Values of 1.5 and 2.5 are now in the set.
* **Tighter TP with break-even hurts**, and single-candle sweeps (`lookback_1`) hurt London.
* **Flattening at 17:00 UTC** raises win rate and roughly halves drawdown, at no cost
  to PF. It is worth combining with the trend filter.

All of this is one year of one pair. The next subsection shows `trend_1h` did not
hold on a different year.

### Out-of-sample check (2024-10-31 to 2025-10-31): the trend filter fails

The same variants, run on the year before, which none of the choices above had seen:

| Variant | Trades | Win % | PF | Profit % | Max DD % | London PF | NY PF |
|---|---|---|---|---|---|---|---|
| baseline | 644 | 18.5 | 0.92 | −97.6 | 99.4 | 1.16 | 0.73 |
| trend_1h | 206 | 18.0 | 0.69 | −71.7 | 79.5 | 0.75 | 0.65 |
| trend_rr1.5 | 204 | 17.6 | 0.70 | −69.6 | 78.1 | 0.76 | 0.67 |
| trend_flat17 | 208 | 24.0 | 0.60 | −73.7 | 78.1 | 0.75 | 0.47 |
| trend_ema20 | 126 | 14.3 | 0.60 | −59.5 | 66.6 | 0.64 | 0.58 |
| trend_ema100 | 249 | 19.7 | 0.81 | −73.5 | 84.4 | 0.77 | 0.84 |

**Conclusion: the strategy has no robust edge on SUI** (and, see below, not on BTC either).

* Every trend variant is *worse* than the baseline on the unseen year. The PF of
  1.22 in 2025-26 was a fit to that one bearish year, not a property of the idea.
* The baseline itself loses on both years (PF 0.92 and 0.99). At 3x with the full
  balance per trade it would have nearly wiped out the account in 2024-25.
* Which session looks better flips between years (London PF 1.16 then 0.93,
  NY 0.73 then 1.05). That is noise, not a session effect.

Do **not** run this live, and do not keep tuning parameters on these two years:
every further tweak would be fitted to data that has already been used.

If you want to keep exploring the idea, change the hypothesis rather than the knobs,
and decide the rule *before* looking at results. Reasonable candidates:

* Test the unchanged baseline on BTC and ETH perps, where session liquidity is deeper.
  If it fails there too, drop the idea.
* Require a displacement candle after the reclaim, or a lower-timeframe break of
  structure, before entering. That changes what a "sweep" is, not how it is filtered.
  (Implemented: see section 4b.)

To run the BTC test (pass/fail rule fixed in advance: the **unchanged baseline**
needs PF above about 1.15 on *both* years):

```bash
freqtrade download-data --config user_data/config_sessionsweep.json --userdir user_data \
  --pairs "BTC/USDT:USDT" --timeframes 5m 1h 4h --trading-mode futures --timerange 20241020-20261031
```

```bash
python user_data/scripts/sessionsweep_variants.py --pair BTC/USDT:USDT --only baseline trend_1h --timerange 20241031-20251031
```

```bash
python user_data/scripts/sessionsweep_variants.py --pair BTC/USDT:USDT --only baseline trend_1h --timerange 20251031-20261031
```

### BTC result: fails on both years

| Year | Variant | Trades | Win % | PF | Profit % | Max DD % | London PF | NY PF |
|---|---|---|---|---|---|---|---|---|
| 2024-25 | baseline | 571 | 28.9 | 0.90 | −60.0 | 75.2 | 1.13 | 0.74 |
| 2024-25 | trend_1h | 206 | 31.6 | 0.96 | −9.7 | 48.5 | 1.14 | 0.83 |
| 2025-26 | baseline | 550 | 28.5 | 0.74 | −81.8 | 82.8 | 0.69 | 0.77 |
| 2025-26 | trend_1h | 184 | 28.3 | 0.67 | −52.1 | 54.5 | 0.70 | 0.65 |

The baseline needed PF above about 1.15 on both years and got 0.90 and 0.74, so
by the rule fixed in advance **the idea is dropped**. Four tests on two pairs
(SUI and BTC, two years each) all lose. London looked positive in 2024-25 on both
pairs but negative in 2025-26 on both, so it is not a stable effect either.

Any new rule must be checked on both years, with PF above about 1.15 on each, before
a dry run is worth the time.

## 4b. Enhancements (structural changes, all off by default)

After the four failed tests the strategy was extended with rule changes rather
than more knob-tuning. Each one changes *what* a valid setup is, or how it is
sized and managed, and each is off by default, so the default strategy still
produces exactly the trades it did before (verified: identical trade list on the
synthetic smoke data). Each was also verified on its own to do what it says.

| Parameter | Default | Effect when on | Why it might help |
|---|---|---|---|
| `risk_per_trade_pct` | 0 | Size each trade so the stop loses this % of equity (`custom_stake_amount`) | Removes the 80–99% drawdowns; makes variants comparable |
| `max_trades_per_session` | 0 | Only the first N sweeps per session per day (`confirm_trade_entry`) | The first sweep of a session is the classic setup; later ones are chop |
| `require_mss` + `mss_lookback` | off / 6 | Reclaim candle must also close beyond the prior 6-candle swing low/high | Demands a market-structure shift, not just a close back inside |
| `displacement_atr_mult` | 0 | Reclaim candle body ≥ N × ATR(14) in the trade direction | Filters weak, indecisive reclaims |
| `entry_retrace_frac` + `entry_wait_candles` | 0 / 6 | Limit order part-way back toward the level; cancelled if unfilled | Better price and a tighter stop; misses runaway moves |
| `max_asia_adr_ratio` | 0 | Asia range must be ≤ N × 14-day average daily range | Compressed Asia ranges tend to produce cleaner expansions |
| `max_trade_hours` | 0 | Close trades older than N hours (`custom_exit`, reason `time_stop`) | Baseline trades ran for days; the thesis is intraday |

Risk sizing changes stake, not signals, so its PF equals the baseline's (fees
aside); compare drawdown instead. With 1% risk at 3x the stake is usually a
fraction of the balance, so the config's "unlimited" stake is just the cap.

### How to judge them

Run every enhancement on both pairs and both years in one go (about 35 minutes):

```bash
python user_data/scripts/sessionsweep_variants.py --enhance-set --pair SUI/USDT:USDT BTC/USDT:USDT --timerange 20241031-20251031 20251031-20261031
```

The script ends with a profit-factor grid, one column per pair/year, and the
minimum across columns. **The rule, fixed in advance: a variant counts only if its
minimum PF across all four columns is above 1.10.** Picking the best single
column would be the same mistake as before. The variants were chosen before any
of these results were seen; do not add new ones after looking.

### Enhancement results: all fail the pass rule

Profit factor, 1% risk per trade, run on the Mac:

| Variant | SUI 2024-25 | SUI 2025-26 | BTC 2024-25 | BTC 2025-26 | Min |
|---|---|---|---|---|---|
| risk1 (control) | 0.82 | 1.06 | 0.85 | 0.71 | 0.71 |
| risk1_first_sweep | 0.67 | 1.00 | 0.83 | 0.70 | 0.67 |
| risk1_mss | 0.88 | 1.08 | 0.82 | 0.73 | 0.73 |
| risk1_displacement | 1.00 | 1.07 | 0.92 | 0.81 | **0.81** |
| risk1_retest | 0.70 | 1.14 | 0.85 | 0.73 | 0.70 |
| risk1_compression | 0.73 | 1.05 | 0.74 | 0.69 | 0.69 |
| risk1_timestop6h | 0.80 | 1.07 | 0.77 | 0.63 | 0.63 |
| risk1_confluence | 0.92 | 1.26 | 0.87 | 0.69 | 0.69 |

The pass mark was a minimum above 1.10. The best is 0.81, so **no enhancement
passes**. Every variant except one is profitable only on SUI 2025-26, the year the
strategy was first built on.

Two things are still worth knowing:

* **Displacement is the one consistent improvement.** It beats the control in all
  four columns (by 0.01 to 0.18 PF). The reclaim candle's strength carries real
  information, but not enough to make the strategy profitable.
* **Fees matter more than they look.** The control has a lower PF than the
  original full-balance baseline (0.82 vs 0.92 on SUI 2024-25) because risk
  sizing puts the largest positions on the tightest stops, where the 0.1%
  round-trip fee is the biggest share of the risk. A setup with a stop under
  about 1% has to clear roughly a 10% fee hurdle before it earns anything.

**Final conclusion:** across 2 pairs, 2 years and 31 rule sets, the Asia-range
sweep-and-reclaim idea does not show an edge on 5m Binance perpetuals. This
branch is best kept as a testing harness rather than as a strategy to trade.

## 4c. Breakout-confirmation entry model, targets, flush exit, timing

Requested after the enhancement round. Everything is off by default, so all the
results above still reproduce (verified: identical trade list with defaults).

| Parameter | Default | Effect when on |
|---|---|---|
| `entry_mode` | `reclaim` | `breakout`: sweep → reclaim → wait up to `confirm_window` candles for a close *below* the post-reclaim swing low (short) or *above* the swing high (long). The entry fires on that break-down / break-out candle. Stop stays beyond the sweep wick (window extended so the wick is still in view). |
| `confirm_window` | 6 | Candles allowed between reclaim and break |
| `tp_range_fraction` | 1.0 | Already the Fibonacci target: 0.5 = 50%, 0.618 = 61.8% of the Asia range from the swept level |
| `tp_mode` | `range` | `resistance`: use the previous day's low (short) / high (long) when it sits between entry and the range target, i.e. the nearer support/resistance |
| `flush_atr_mult` | 0 | After a closed candle since entry with body ≥ N × ATR(14) in our favour (a flush down / push up), exit at the next open after the **first opposite-colour candle** |

Verified on synthetic data: breakout entries all follow a reclaim within the
window and all close through the swing; resistance targets are never further
than the range target and changed 51 of 338 signals; the flush exit fired on 17
of 214 trades with a small positive average.

### How to test it

Entry-model variants (9 variants, about 36 minutes for both pairs and years):

```bash
python user_data/scripts/sessionsweep_variants.py --entry-set --pair SUI/USDT:USDT BTC/USDT:USDT --timerange 20241031-20251031 20251031-20261031
```

`brk_all_signals` is the full model: breakout entry, displacement ≥ 0.8 ATR,
61.8% / resistance target, flush exit, 8-hour time stop, 1% risk. `risk1` is the
control. Same pass rule as before: **minimum PF across the four columns above 1.10.**

Session-timing variants on the full model (12 variants, about 48 minutes):

```bash
python user_data/scripts/sessionsweep_variants.py --timing-set --pair SUI/USDT:USDT BTC/USDT:USDT --timerange 20241031-20251031 20251031-20261031
```

They move the Asia window (00–07, 00–08, 01–08), narrow London (07–09, 08–11),
narrow NY (12:30–14:30, 13:30–16:00, 14:30–17:00), isolate each session, and
flatten at 17:00 or 21:00 UTC. The Asia window cannot cross midnight.

Hour-by-hour breakdown of any backtest (entry hour, session, weekday, exit
reason, holding time):

```bash
python user_data/scripts/sessionsweep_timing.py
```

A timing effect is real only if the same hours win on both pairs and both years;
a cell with fewer than about 30 trades is noise.

### Entry-model results: fail, and one bug found

Profit factor, 1% risk, run on the Mac (control = `risk1`):

| Variant | SUI 2024-25 | SUI 2025-26 | BTC 2024-25 | BTC 2025-26 | Min |
|---|---|---|---|---|---|
| risk1 (control) | 0.82 | 1.06 | 0.85 | 0.71 | 0.71 |
| brk | 0.88 | 1.07 | 0.83 | **0.76** | 0.76 |
| brk_fib50 | 0.71 | (bug) | 0.68 | 0.52 | 0.52 |
| brk_fib618 | 0.82 | (bug) | 0.71 | 0.57 | 0.57 |
| brk_resistance | 0.87 | 1.11 | 0.83 | 0.75 | 0.75 |
| brk_flush | 0.60 | 0.97 | 0.45 | 0.49 | 0.45 |
| brk_disp_flush | 0.67 | 1.13 | 0.50 | 0.44 | 0.44 |
| brk_all_signals | 0.63 | 1.10 | 0.51 | 0.43 | 0.43 |
| reclaim_fib618_flush | 0.66 | 0.80 | 0.47 | 0.53 | 0.47 |

* **Breakout confirmation** is a small, fairly consistent improvement over the
  control (better in 3 of 4 columns, best minimum so far at 0.76) with a higher
  win rate and about half the drawdown, but it is still a losing strategy.
* **The flush exit is clearly harmful** (0.45–0.60 on three columns). Exiting on the
  first opposite-colour candle cuts the winners that pay for everything else.
* **50% / 61.8% targets are worse** than the full range in every valid column: the
  winners get smaller while the stop stays where it is.
* **Resistance targets** change little.

**Bug found and fixed.** `brk_fib50` / `brk_fib618` on SUI 2025-26 show 4 trades and
a PF near 50. In breakout mode the entry comes after the reclaim *and* a further
break, so a 50% or 61.8% target was often already behind the entry; `custom_roi`
then returned no target, one short in a falling market stayed open for months and
blocked the single trade slot. Entries now require the target to lie beyond the
planned entry (the default trade list is unchanged). Those two cells are invalid;
rerun them if they matter. The `--timing-set` was not run yet.

## 4d. Higher timeframe: 4h trend and RSI overbought / oversold

| Parameter | Default | Effect when on |
|---|---|---|
| `trend_timeframe` | `1h` | `4h`: the EMA trend filter uses 4h candles instead of 1h |
| `use_rsi_filter` | off | Shorts need RSI ≥ `rsi_overbought` (70), longs need RSI ≤ `rsi_oversold` (30) |
| `rsi_timeframe` | `1h` | Timeframe of that RSI: `5m`, `1h` or `4h` |
| `rsi_len` | 14 | RSI length (Wilder smoothing, pure pandas) |

**4h data is now required.** Download it for every pair before backtesting
(the strategy declares a 4h informative even when the filters are off):

```bash
freqtrade download-data --config user_data/config_sessionsweep.json --userdir user_data --pairs "SUI/USDT:USDT" "BTC/USDT:USDT" --timeframes 4h --trading-mode futures --timerange 20241020-20261031
```

Verified on synthetic data: defaults reproduce the previous trade list exactly;
the 5m RSI matches pandas-ta to 5e-6; the 1h RSI a 5m candle sees is exactly the
RSI of the last *closed* 1h candle (no lookahead); with the filter on, every short
had RSI ≥ threshold and every long RSI ≤ threshold on the chosen timeframe.

One thing to know before reading results: **4h RSI ≥ 60 and "4h close below the
4h EMA" almost never hold at the same time** (both describe the same recent 4h
move), so combining the 4h RSI filter with the 4h trend filter produces close to
zero trades. The variant set therefore pairs the 4h trend with the *1h* RSI,
which is the classic "overbought pull-back inside a downtrend" condition.

### How to test it

12 variants, about 48 minutes for both pairs and years. Six apply the filters to
the plain strategy (control `risk1`), six to the full breakout model (control `t_base`):

```bash
python user_data/scripts/sessionsweep_variants.py --htf-set --pair SUI/USDT:USDT BTC/USDT:USDT --timerange 20241031-20251031 20251031-20261031
```

Same pass rule: **minimum PF across the four columns above 1.10.** Expect far
fewer trades with the RSI filters on (on synthetic data 1h 70/30 kept about 5% of
entries); a column with under about 30 trades is noise whatever its PF.

## 4e. SessionMomentum: the opposite bet (`user_data/strategies/SessionMomentum.py`)

Every sweep test so far pointed the same way: breaks of the Asia range tended to
*continue*, which is why fading them lost. `SessionMomentum` trades with the break.

**Rules (defaults):** during London or NY, the first 5m close beyond the Asia
high/low whose body is ≥ 1 ATR in the break direction and whose volume is ≥ 1.5×
the 20-candle average. Stop 0.1% beyond the breakout candle's low/high, capped at
1.5% from entry. Target = one Asia range beyond the broken level. 1% of equity
risked per trade, first break per session only, max 1 open trade, 3x isolated.

| Parameter | Default | Meaning |
|---|---|---|
| `break_min_pct` | 0 | Close must exceed the level by this % |
| `displacement_atr_mult` | 1.0 | Breakout candle body ≥ N × ATR(14); 0 = off |
| `volume_mult` | 1.5 | Breakout volume ≥ N × 20-candle average; 0 = off |
| `asia_range_min_pct` / `asia_range_max_pct` | 0.3 / 0 | Skip tiny / huge Asia ranges (max 0 = off) |
| `max_trades_per_session` | 1 | Breaks per session per day; 0 = unlimited |
| `use_trend_filter`, `trend_timeframe`, `trend_ema_len` | off, 4h, 50 | Trade only with the 1h/4h EMA |
| `use_rsi_filter`, `rsi_timeframe`, `rsi_long_min`, `rsi_short_max` | off, 1h, 55, 45 | RSI on the momentum side of 50 |
| `stop_mode` | candle | `candle` / `level` (back inside the range) / `mid` (Asia mid) |
| `stop_buffer_pct`, `max_stop_distance_pct` | 0.1, 1.5 | Stop buffer and cap |
| `tp_range_mult` | 1.0 | Target in Asia ranges beyond the level |
| `trail_atr_mult`, `trail_start_r` | 0, 1.0 | ATR chandelier trail once N R in profit; 0 = off |
| `max_trade_hours`, `exit_at_session_end`, `flat_time_min` | 0, off, 17:00 | Time exits |
| `risk_per_trade_pct`, `leverage_level` | 1.0, 3.0 | Sizing and leverage |

Verified on synthetic data: every entry is the first close beyond the level,
in session, with the required body and volume; stops filled exactly at the
planned level and targets within 0.11%; stop losses were 1.06–1.17% of equity;
the session cap held; the ATR trail moved the stop on 36 of 64 trades and no trade
ever exited worse than its initial stop.

### How to test it (same rule: minimum PF > 1.10 across all four columns)

18 variants, about 72 minutes for both pairs and years. The set was fixed before
any result was seen; it covers the volume and displacement thresholds, trend and
RSI alignment, the three stop modes, target distance, two trails, time exits, an
Asia-range cap and one combination (`m_all`).

```bash
python user_data/scripts/sessionsweep_variants.py --strategy SessionMomentum --pair SUI/USDT:USDT BTC/USDT:USDT --timerange 20241031-20251031 20251031-20261031
```

Expect roughly 150–300 trades per pair-year (one per session at most). The
volume filter is the part most likely to matter on real data: synthetic volume
is random, so it was only checked for correctness, not for effect.

### SessionMomentum results: fails on three of four columns

Profit factor, run on the Mac (18 variants; selected rows, full grid in the run log):

| Variant | SUI 2024-25 | SUI 2025-26 | BTC 2024-25 | BTC 2025-26 | Min |
|---|---|---|---|---|---|
| m_base | 1.19 | 0.53 | 0.67 | 0.64 | 0.53 |
| m_no_volume | 0.93 | 0.71 | 0.79 | 0.66 | **0.66** |
| m_disp1.5 | 1.23 | 0.43 | 0.63 | 0.60 | 0.43 |
| m_trend1h | 1.10 | 0.63 | 0.69 | 0.69 | 0.63 |
| m_trend4h_rsi1h | 1.12 | 0.68 | 0.70 | 0.59 | 0.59 |
| m_stop_mid | 1.35 | 0.62 | 0.71 | 0.86 | 0.62 |
| m_tp2 | 1.10 | 0.37 | 0.69 | 0.71 | 0.37 |
| m_trail2atr | 0.37 | 0.33 | 0.33 | 0.39 | 0.33 |
| m_flat1700 | 1.22 | 0.46 | 0.69 | 0.64 | 0.46 |
| m_all | 0.33 | 0.40 | 0.32 | 0.38 | 0.32 |

* **Breakouts work on SUI 2024-25 only** (most variants above 1.0 there, London PF
  up to 1.6) and lose everywhere else. That is the mirror image of the sweep
  results, which were best on SUI 2025-26: each idea has one good year and it is
  not the same year. Neither is an edge; both are regime luck.
* **Wider stop (Asia mid) is the only change that helps in every column** (0.62–1.35
  vs 0.53–1.19), by lifting the win rate from ~25% to 35–50%. Still below 1 in three.
* **The ATR trail is a design mistake, not a tuning one.** 2 × ATR on 5m candles is
  about 0.3% of price while the initial risk is ~1%, so once a trade is 1R up the
  trail sits almost at the market and caps winners near 0.7R while losers still
  lose 1R: PF ≈ 0.36 × 0.7 / 0.64 ≈ 0.4, exactly what the grid shows. A trail
  should be expressed in R or in higher-timeframe ATR. Left as is, documented.
* The volume filter did not help; removing it gives the best minimum (0.66).

**Final conclusion across both families:** fading the Asia range (31 rule sets)
and trading its break (18 rule sets) both fail on 2 pairs × 2 years. The Asia
range on 5m Binance perpetuals does not carry a tradable edge in either direction
with these tools. Further work should change the *information* used (order flow,
funding, open interest, cross-pair context), not the rules around the same levels.

## 4f. 1-hour versions: `SessionSweep1h` and `SessionMomentum1h`

Both are thin subclasses that keep every rule, parameter and callback of the 5m
strategy and change only the base timeframe (and, for the sweep, the candle-count
defaults: lookback, confirmation window, retest wait and MSS lookback become 2–3
hourly candles instead of 6 five-minute ones).

What changes on hourly candles:

* **Asia range** = candles opening 00:00–06:00. **London** = candles opening
  07:00–11:00. **New York** = candles opening 13:00–16:00, because the 12:00
  candle opens before the 12:30 session start; set `ny_start_min` to 720 to
  include it.
* A sweep / breakout is judged on the **hourly** close, so there are far fewer
  signals (synthetic data: 118 sweep trades per 114 days vs 440 on 5m) and each
  one carries more information. Displacement and volume compare against hourly
  ATR and volume, so `SessionMomentum1h` defaults to a 0.5 ATR body and 1.2×
  volume (a full hourly ATR body almost never occurs).
* Only 1h and 4h data are needed. The 1h informative merge is a no-op on a 1h
  base; the 4h one still shifts so no unfinished 4h candle is visible.

**Config change:** `timeframe` was removed from `config_sessionsweep.json` so each
strategy's own timeframe applies (Freqtrade's config value would otherwise
override the subclass back to 5m). The 5m strategies are unaffected.

Test exactly as before, with the strategy name:

```bash
python user_data/scripts/sessionsweep_variants.py --strategy SessionSweep1h --enhance-set --pair SUI/USDT:USDT BTC/USDT:USDT --timerange 20241031-20251031 20251031-20261031
```

```bash
python user_data/scripts/sessionsweep_variants.py --strategy SessionMomentum1h --pair SUI/USDT:USDT BTC/USDT:USDT --timerange 20241031-20251031 20251031-20261031
```

Hourly backtests run about ten times faster than 5m. The pass rule is the same;
with fewer trades, treat any column under about 30 trades as noise.

### SessionSweep1h results: fail

| Variant | SUI 2024-25 | SUI 2025-26 | BTC 2024-25 | BTC 2025-26 | Min |
|---|---|---|---|---|---|
| risk1 (control) | 0.85 | 1.13 | 0.74 | 0.80 | 0.74 |
| risk1_first_sweep | 0.87 | 1.16 | 0.73 | 0.81 | 0.73 |
| risk1_retest | 0.93 | 1.17 | 0.65 | 0.76 | 0.65 |
| risk1_compression | 0.68 | 1.20 | 0.71 | 0.72 | 0.68 |
| risk1_timestop6h | 0.82 | 1.16 | 0.74 | 0.70 | 0.70 |
| risk1_mss | 0.64 | 1.06 | 0.84 | 1.08 | 0.64 (32–90 trades) |
| risk1_displacement | 0.50 | 2.19 | 0.65 | 1.11 | 0.50 (8–67 trades) |
| risk1_confluence | 1.33 | 1.08 | 0.58 | 1.21 | 0.58 (8–61 trades) |

Same picture as on 5m, with about half the trades: good on SUI 2025-26, losing
elsewhere. The MSS, displacement and confluence rows have too few trades on SUI
to mean anything (8–37), and their BTC columns still disagree with each other.

### SessionMomentum1h results: fails the rule, but the first candidate worth a third test

| Variant | SUI 2024-25 | SUI 2025-26 | BTC 2024-25 | BTC 2025-26 | Min | Trades/col |
|---|---|---|---|---|---|---|
| m_base (= m_disp0.5) | 1.49 | 1.30 | 0.68 | 1.10 | 0.68 | 48 / 61 / 164 / 161 |
| m_no_volume | 1.37 | 0.83 | 0.83 | 0.80 | 0.80 | 98 / 109 / 225 / 214 |
| m_trend4h | 1.22 | 1.76 | 0.80 | 1.30 | 0.80 | 29 / 43 / 102 / 94 |
| m_rsi1h | 1.45 | 1.53 | 0.78 | 1.11 | 0.78 | 39 / 53 / 136 / 144 |
| **m_trend4h_rsi1h** | 1.24 | 1.66 | 0.89 | 1.27 | **0.89** | 25 / 41 / 93 / 91 |
| m_stop_mid | 1.22 | 0.95 | 0.88 | 0.94 | 0.88 | 69 / 94 / 182 / 173 |
| m_tp2 | 1.57 | 1.34 | 0.72 | 1.03 | 0.72 | 46 / 60 / 153 / 130 |
| m_timestop6h | 1.88 | 1.39 | 0.65 | 0.80 | 0.65 | 48 / 62 / 170 / 170 |
| m_trail2atr | 0.56 | 0.88 | 0.28 | 0.44 | 0.28 | |

Why this one is different from everything before it:

* **Three of four columns are positive** for the default rules, and the 4h-trend /
  1h-RSI alignment makes the BTC columns better in both years (0.68→0.89,
  1.10→1.27) while keeping SUI positive. Every earlier family had one good year.
* **The failure is concentrated**: BTC 2024-25 New York (PF 0.46–0.55 in every
  variant) while BTC 2024-25 London is 1.06–1.64. On 1h candles NY is only four
  candles (13:00–16:00). This looks like one bad bucket rather than a broken idea.
* **The volume filter earns its place here** (removing it: 1.30→0.83, 1.10→0.80),
  unlike on 5m.
* Caveats: SUI columns have 25–61 trades, so their PFs are rough; and the
  hourly results use the same two years the whole project has been looking at.

It still does **not** pass (0.89 < 1.10), so by the rule it is not a strategy
yet. It is the first thing that deserves a genuinely new dataset instead of
being dropped.

**Pre-registered third test** (decided before any new data is seen):

* Candidates: exactly two, `m_base` and `m_trend4h_rsi1h` on `SessionMomentum1h`,
  unchanged.
* New data: ETH/USDT:USDT for both years, plus BTC and SUI for 2023-10-31 to
  2024-10-31 (one earlier year each). That is four unseen columns.
* Pass: PF above 1.10 in every one of the four new columns for a candidate.
  Any column with fewer than 30 trades is reported but cannot count as a pass.
* If a candidate passes, the next step is a 4-week dry run, not live money.

```bash
freqtrade download-data --config user_data/config_sessionsweep.json --userdir user_data --pairs "ETH/USDT:USDT" --timeframes 1h 4h --trading-mode futures --timerange 20241020-20261031
```

```bash
freqtrade download-data --config user_data/config_sessionsweep.json --userdir user_data --pairs "BTC/USDT:USDT" "SUI/USDT:USDT" --timeframes 1h 4h --trading-mode futures --timerange 20231020-20241031 --prepend
```

```bash
python user_data/scripts/sessionsweep_variants.py --strategy SessionMomentum1h --only m_base m_trend4h_rsi1h --pair ETH/USDT:USDT --timerange 20241031-20251031 20251031-20261031
```

```bash
python user_data/scripts/sessionsweep_variants.py --strategy SessionMomentum1h --only m_base m_trend4h_rsi1h --pair BTC/USDT:USDT SUI/USDT:USDT --timerange 20231031-20241031
```

`m_disp1.5` produces no trades on hourly candles (a full-ATR hourly body is too
rare); the runner reports such variants as zeros.

### Third test result: both candidates fail

Four unseen columns, pass mark PF > 1.10 in every one:

| Candidate | ETH 2024-25 | ETH 2025-26 | BTC 2023-24 | SUI 2023-24 | Min | Trades |
|---|---|---|---|---|---|---|
| m_base | 0.77 | 0.86 | 0.64 | 0.69 | 0.64 | 116 / 145 / 162 / 40 |
| m_trend4h_rsi1h | 1.04 | 1.05 | 0.72 | 0.79 | 0.72 | 71 / 91 / 90 / 19 |

Robustness columns agreed: every bootstrap PF band includes values below 1,
every permutation p-value is above 0.4, and at most 3 of 5 calendar folds were
profitable. The aligned variant is better than the plain one in all four new
columns (as it was in all four original ones), but it is roughly break-even on
ETH and loses on the 2023-24 year of both coins.

The one consistent structural finding across the whole study: **London beats
New York for hourly breakouts** (ETH London PF 1.62 / 1.70 vs NY 0.70 / 0.55; the
same split on BTC 2024-25). Noted as a hypothesis for a future study; not tested
further here, because testing it now on data already seen would be the mistake
this project set out to avoid.

## Final conclusion of the study

| Family | Rule sets | Pairs × years | Best minimum PF | Passed |
|---|---|---|---|---|
| Sweep 5m | 31 | 2 × 2 | 0.81 | no |
| Sweep 1h | 8 | 2 × 2 | 0.74 | no |
| Momentum 5m | 18 | 2 × 2 | 0.66 | no |
| Momentum 1h | 18 + out-of-sample | 3 pairs, 3 years | 0.89 in-sample, 0.72 out-of-sample | no |

Neither fading nor trading the break of the Asia session range on Binance
perpetuals produced an edge that survives a change of year or pair. The code
is a working, verified research harness; none of the strategies should be run
with money.

## 4g. SuiFlushShort: the uploaded "SUI Flush Playbook" port (deep review)

Supplied as `freqtrade_sui_flush.zip` and now in the repo as
`user_data/strategies/SuiFlushShort.py`, `user_data/scripts/fetch_okx_flow.py`
and `user_data/config_suiflush.json` (credentials are placeholders).

**The rules** (15m, short only): first 15m close below the prior 6h low while OKX's
long/short *account* ratio is ≥ 2.6 (crowded longs); skip if open interest rose ≥ 1%
in 4h while the ratio rose over 2h; optional BTC-also-breaking filter. Stop 0.2%
above max(break-candle high, broken low). Half off at 1R and stop to breakeven,
rest at 2R, cover on a reclaim of the lowest-low candle's high within 4 candles,
time stops at 2h (no T1) and 4h. 1% of equity at risk, half on weekends, 5× isolated.
Playbook claim: +0.47R per trade before fees on 78 trades, Aug–Nov 2026, OKX data.

### Review findings

* **The code is sound.** Flow rows are only used after their hour closes (verified:
  the merged ratio on every entry equals the last *closed* hour's value). The
  structural stop, sizing, partial exit and reclaim logic do what the README says.
* **Backtest fidelity gap (fixed).** Freqtrade evaluates `adjust_trade_position` and
  `custom_exit` at each candle's *open*, so the author's 1R and 2R targets could
  only fire when a later candle opened past them. T2 is now a `custom_roi`, which
  Freqtrade checks against the candle's low, so it fills intra-candle. T1 and the
  reclaim still need `--timeframe-detail 1m`, as the README says.
* **The data is the problem, not the code.** OKX keeps about 60 days of hourly
  ratio history. A 78-trade sample from one falling quarter, in a short-only
  strategy, cannot be told apart from "shorting SUI in a bear market worked".
  Binance publishes the same metric back to 2021 (`data.binance.vision`, 5-minute
  samples), so `fetch_binance_flow.py` builds a multi-year hourly file and the
  strategy gained `flow_source = binance` (with a matching live refresh) and
  `ls_mode = percentile` (ratio above its own rolling 80th percentile), because
  Binance's ratio reads lower than OKX's and an absolute 2.6 would not transfer.
* **Fees matter.** The stop is ~1% of price, so the 0.1% round-trip fee is ~0.1R
  per trade and funding on a 5× short adds to it. The playbook's +0.47R is before
  both; Freqtrade's backtest includes both.
* Research parameters added (defaults unchanged): lookback, stop buffer, T1/T2
  multiples, reclaim window, time stops, risk, leverage, all switchable.

Verified on synthetic data: every entry is a first break with ratio ≥ threshold
and not disarmed; stops fill exactly at the structural level; 16 of 78 trades took
the T1 partial; T2 fills within 0.1% of 2R; risk is 0.99% of equity on weekdays
and 0.49% on weekends; no entries when the flow file is missing; percentile mode
and the Binance file parser work (24 hourly rows from 288 five-minute samples,
labelled with the hour start).

### Pre-registered test (written before any real result)

1. **Replication** (sanity, not pass/fail): OKX flow, defaults, over the ~60 days
   the OKX file covers, with 1m detail. Compare with the playbook's numbers.
2. **Main test**: Binance flow, percentile 80, two years of SUI
   (2024-11 → 2025-10 and 2025-11 → 2026-10), 1m detail.
   **Pass = PF > 1.10 in both years, ≥ 30 trades per year, robustness verdict at
   least WATCH.** Named secondary candidates: percentile 90 and absolute 2.0.
3. **The control** `f_bin_noflow` (same entries without the ratio filter) must be
   clearly worse than the main candidate in both years, or the filter is not the edge.
4. If it passes: 4-week dry run with the OKX source (the live default), nothing live.

Commands on the Mac, one at a time. Data: 15m and 1m candles for SUI and BTC
(1m is large: about 1 GB for two pairs over two years, allow 15 minutes):

```bash
freqtrade download-data -c user_data/config_suiflush.json --userdir user_data --pairs "SUI/USDT:USDT" "BTC/USDT:USDT" --timeframes 15m 1m --trading-mode futures --timerange 20241020-20261031
```

```bash
python user_data/scripts/fetch_okx_flow.py
```

```bash
python user_data/scripts/fetch_binance_flow.py --symbol SUIUSDT --start 2024-10-20 --end 2026-10-31
```

Replication over the OKX window (adjust the start to the first date the OKX
fetch printed):

```bash
python user_data/scripts/sessionsweep_variants.py --strategy SuiFlushShort --only f_okx_default --timeframe-detail 1m --pair SUI/USDT:USDT --timerange 20260903-20261031
```

Main test, all 15 variants, about 20 minutes per year with 1m detail:

```bash
python user_data/scripts/sessionsweep_variants.py --strategy SuiFlushShort --only f_bin_pct80 f_bin_pct90 f_bin_abs2.0 f_bin_noflow --timeframe-detail 1m --pair SUI/USDT:USDT --timerange 20241031-20251031 20251031-20261031
```

Then, only if something passes, the remaining variants to see which rules carry it.

### Results: replication holds, the two-year test fails

**Replication** (OKX flow, defaults, 2026-09-03 → 2026-10-31, 1m detail):
57 trades, win 52.6%, PF 1.67, +9.5% at 1% risk, max drawdown 2.8%. That matches
the playbook's direction (its 78 trades, +0.47R before fees). But the permutation
p-value is 0.057, the bootstrap PF band is 0.88–3.25 and 3 of 5 calendar folds
were profitable: a good two months, not yet evidence. Two thirds of the profit
came from the 30 trades taken after a +10% 30-day rally (bull-regime PF 3.03);
in chop the rule lost (PF 0.77).

**Main test** (Binance flow, SUI, 1m detail, fees and funding included):

| Variant | 2024-25 | 2025-26 | Trades | Verdict |
|---|---|---|---|---|
| f_bin_pct80 (main candidate) | 0.62 | 0.75 | 277 / 171 | FAIL |
| f_bin_pct90 | 0.58 | 0.67 | 181 / 111 | FAIL |
| f_bin_abs2.0 | 0.70 | 0.70 | 502 / 329 | FAIL |
| f_bin_noflow (control, no ratio filter) | 0.68 | 0.69 | 785 / 717 | FAIL |

Zero of five calendar folds profitable for every candidate in 2024-25; the
bootstrap PF bands top out at 0.82–1.07. **The long/short filter is not the edge**:
with it (0.62 / 0.75) the strategy is no better than without it (0.68 / 0.69),
which is the opposite of the playbook's central claim. The range break itself
loses about 0.3R per trade after costs across both years, in every regime label.

**Conclusion (revised after the diagnostic below).** The plain break is a two-month
regime artefact. Whether the OKX crowded-longs filter adds a durable edge is
*unresolved*, because no backtestable proxy for it has been validated yet; see the
diagnostic. Do not trade it with money.

One diagnostic that would sharpen this (not a search for a winner): run
`f_bin_pct80` over the same 2026-09-03 → 2026-10-31 window. If it also shows
PF near 1.6, the Binance ratio is a faithful proxy for OKX's and the two-year
result stands as is; if it does not, the OKX and Binance ratios behave
differently and the replication and main test are not directly comparable.

```bash
python user_data/scripts/sessionsweep_variants.py --strategy SuiFlushShort --only f_bin_pct80 f_bin_noflow --timeframe-detail 1m --pair SUI/USDT:USDT --timerange 20260903-20261031
```

**Diagnostic result (same 60-day window):**

| Variant | Trades | Win % | PF |
|---|---|---|---|
| OKX ≥ 2.6 (replication) | 57 | 52.6 | 1.67 |
| Binance percentile 80 | 10 | 40.0 | 1.32 |
| No filter | 93 | 43.0 | 1.18 |

The Binance percentile filter passed 10 of 93 breaks where the OKX rule passed 57,
so **the two-year test judged a different filter, not the OKX rule on more data.**
A rolling percentile rises when the ratio stays high for weeks, which is exactly
the crowded regime the playbook wants to trade, so percentile mode is the wrong
proxy for an absolute "crowded" level. This weakens the earlier sentence "the
filter is not the edge" to: *the Binance-percentile filter is not an edge*.

What the data does and does not show now:

* The plain 6h-low break was mildly profitable in Sep–Oct 2026 (PF 1.18, 93
  trades) and lost over the two years before (0.68 / 0.69). The break itself is
  regime-dependent; that part is settled.
* Within the window the OKX filter lifted PF from 1.18 to 1.67 by keeping 57 of 93
  trades. Whether that selection repeats cannot be tested backwards: OKX has no
  history beyond 60 days, and no Binance proxy has been shown to match it yet.

**Closing diagnostic, the proxy check that was still missing:** the absolute
Binance threshold (`f_bin_abs2.0`, which the playbook's own numbers suggest is the
OKX-2.6 equivalent) over the same window. If it keeps roughly 50 trades with PF
near 1.6, the Binance absolute ratio is a fair proxy and its two-year result
(0.70 / 0.70) is the verdict on the rule. If it does not, the OKX rule remains
untested beyond two months and the only honest path is forward data: keep
`fetch_okx_flow.py` running weekly to build history, and judge again in six months.

```bash
python user_data/scripts/sessionsweep_variants.py --strategy SuiFlushShort --only f_bin_abs2.0 --timeframe-detail 1m --pair SUI/USDT:USDT --timerange 20260903-20261031
```

**Result:** 68 trades, win 41.2%, PF 1.19, 3 of 5 folds. The Binance absolute
threshold keeps about as many trades as the OKX rule (68 vs 57) but shows no
lift over the unfiltered break (1.18 on 93 trades). So the Binance ratio *is* a
fair size-for-size proxy, and the OKX filter's apparent lift (1.18 → 1.67) is
either information unique to OKX's trader population or, more likely given the
OKX bootstrap band of 0.88–3.25 on 57 trades, noise. Either way it cannot be
confirmed from history.

**Final reading of SuiFlushShort on SUI:** the break alone is regime-dependent and
loses over two years; the best available two-year test of "break + crowded
longs" (Binance absolute 2.0) gives PF 0.70 in both years; the OKX variant's
extra lift rests on 57 trades and is not separable from luck. Not a strategy to
trade. The one remaining source of evidence is forward OKX data, which costs
nothing to collect: run `fetch_okx_flow.py` weekly.

### Pre-registered BTC test (the rule has never seen BTC)

The strategy now derives its flow instrument from the traded pair and skips the
BTC filter when trading BTC itself. Candidates fixed in advance: `f_bin_abs2.0`
(main), `f_bin_noflow` (control), `f_okx_default` over the OKX window. Pass =
PF > 1.10 in both years with ≥ 30 trades and verdict ≥ WATCH, and the control
clearly worse. Expectation stated before running: BTC's long/short ratio sits
lower than SUI's, so the absolute 2.0 may select few trades; if a column has
fewer than 30 trades it is reported as THIN and cannot pass.

```bash
python user_data/scripts/fetch_binance_flow.py --symbol BTCUSDT --start 2024-10-20 --end 2026-10-31
```

```bash
python user_data/scripts/fetch_okx_flow.py --inst BTC-USDT-SWAP
```

```bash
python user_data/scripts/sessionsweep_variants.py --strategy SuiFlushShort --only f_bin_abs2.0 f_bin_pct80 f_bin_noflow --timeframe-detail 1m --pair BTC/USDT:USDT --timerange 20241031-20251031 20251031-20261031
```

```bash
python user_data/scripts/sessionsweep_variants.py --strategy SuiFlushShort --only f_okx_default f_bin_abs2.0 f_bin_noflow --timeframe-detail 1m --pair BTC/USDT:USDT --timerange 20260903-20261031
```

**BTC results (first run).** The `git pull` before this run failed on a DNS error,
so the backtests used the previous strategy version with SUI hardcoded as the flow
instrument: the filtered rows below applied *SUI's* ratio to BTC trades and are
confounded. The control does not read the flow data and is valid.

| Variant | BTC 2024-25 | BTC 2025-26 | BTC Sep–Oct 2026 | Valid? |
|---|---|---|---|---|
| f_bin_noflow (plain 6h-low break) | 0.55 (683 trades) | 0.62 (718) | 0.45 (109) | yes |
| f_bin_abs2.0 | 0.66 | 0.55 | 0.55 | no, SUI ratio |
| f_bin_pct80 | 0.53 | 0.50 | | no, SUI ratio |
| f_okx_default | | | 0.45 (60) | no, SUI ratio |

Zero of five calendar folds profitable in both years for the control. **The plain
break loses badly on BTC in every period, including the Sep–Oct 2026 window where
it was mildly positive on SUI.** The playbook's break rule is not transferable.
The filtered BTC rows must be rerun after pulling (BTC flow files are in place:
Binance from 2025-01-24, OKX from 2026-09-03); given the control, a filter would
need to turn PF 0.55 into 1.10 to pass, which no filter in this study has come
close to.

**BTC rerun (correct BTC flow data, commit 8b1b3e2):**

| Variant | BTC 2024-25 | BTC 2025-26 | BTC Sep–Oct 2026 |
|---|---|---|---|
| f_bin_noflow (control) | 0.55 (683) | 0.62 (718) | 0.45 (109) |
| f_bin_abs2.0 | 0.69 (60*) | 0.72 (202) | 0.15 (15, thin) |
| f_bin_pct80 | 0.47 (150) | 0.61 (210) | |
| f_okx_default | | | no trades |

\* The Binance BTC file starts 2025-01-24 (a DNS failure on the first download
skipped 97 days), so the 2024-25 column covers about nine months.

* All variants fail; none reaches 0.75 in any full year.
* The absolute ratio filter gives a small, consistent lift over the plain break on
  BTC (0.55→0.69, 0.62→0.72), the only place in the study where a crowded-longs
  filter helped in both years. It is far from enough.
* OKX's BTC long/short ratio never reached 2.6 in its 60-day window, so the
  playbook rule simply does not fire on BTC: the threshold is SUI-specific.

## Final conclusion for SuiFlushShort

On SUI the playbook replicates for its own two months and fails over two years;
on BTC the break loses in every period and the filter cannot rescue it. The
strategy is not a tradable edge. The one thing worth keeping is cheap: run
`fetch_okx_flow.py` weekly so that, in six months, the OKX rule can be judged on
data it has never seen.

## 4h. FlushReversal: pre-registered test of the research report's top candidate

Source: `reports/BTC SUI futures orderflow edges.md`, candidate 1. Strategy
`user_data/strategies/FlushReversal.py`, config `user_data/config_flushrev.json`,
taker data from `user_data/scripts/fetch_binance_taker.py`.

**This section is the pre-registration. It was committed before any real BTC or
SUI data was loaded into the strategy.** The commit that adds it is the record;
nothing below may change after results are seen.

### Rules (fixed)

* 5m candles. Event: the 15-minute return (3 candles) is at least *k* × its
  trailing 7-day standard deviation, and the taker share of those 15 minutes'
  volume in the move's direction is at or above its trailing 7-day *p*-th
  percentile. Taker-buy volume comes from Binance kline archives.
* Fade it with a limit order at the event close moved *e* × ATR(14) further in the
  move's direction, valid 15 minutes. Take profit at 50% retracement of the move,
  stop 1.0 × the move's 3-candle range beyond its extreme, 60-minute time stop.
  No entries within 10 minutes of 00:00, 08:00 or 16:00 UTC funding.
* 1% of equity at risk, 3× isolated, max 1 open trade.

**Deviation from the report, decided before data:** both trailing windows are
7 days, not 7 and 30. Freqtrade caps Binance 5m startup history at 2,494 candles
(about 8.7 days), so a 30-day window cannot run live.

**Cost model.** Freqtrade charges one fee rate on both legs. With no `--fee` it
uses Binance's worst case, 0.05% per side: 3 bp more than the report's maker
entry, and no exit slippage. The stress run uses `--fee 0.0007` per side, about
4 bp more per round trip. Freqtrade fills limits on touch; the `_tick` variants
require price to trade one tick through.

Verified on synthetic data: every event meets the move and flow rules; flow
thresholds use only earlier candles; no entry falls within 10 minutes of funding;
entries fill at the limit or better; stops fill exactly and targets within 0.11%;
no trade exceeds 60 minutes; stop losses are 1.05% of equity; unfilled orders
expire; the low-flow control selects disjoint events of the same size; no taker
file means no trades.

### Protocol

1. **Design window**, both pairs, three half-years: 2023-05-12 → 2023-12-31,
   2024-01-01 → 2024-06-30, 2024-07-01 → 2024-12-31. Run the 8-cell grid
   (*k* ∈ {2.5, 3.0}, *p* ∈ {90, 95}, *e* ∈ {0, 0.25}).
2. **Selection rule:** one cell for both pairs, the one with the highest median
   profit factor across the six pair-half-year columns. Ties go to the cell with
   more trades. Record the choice in this file before step 3.
3. **Out of sample, one run only**, 2025-01-01 → 2025-12-31 and 2026-01-01 →
   2026-10-31, both pairs: the selected cell, its `_ctrl` (low-flow control) and
   its `_tick` (fill-through) variants at default fees, then the selected cell
   with `--fee 0.0007`. No re-tuning afterwards.

### Pass rule (per pair; every line must hold)

| Criterion | Threshold |
|---|---|
| Trades per OOS year | ≥ 75 |
| Profit factor, each OOS year, default fees | ≥ 1.10 |
| Robustness verdict across the two OOS years | WATCH or PASS |
| Selected cell minus `_ctrl`, profit factor, each OOS year | ≥ +0.10 |
| `_tick` variant profit factor, each OOS year | ≥ 1.05 |
| `--fee 0.0007` stress, profit factor, each OOS year | ≥ 1.00 |

A pass on SUI alone is reported as "SUI only, low power". A pass of any kind
leads to a 6-month dry run (Nov 2026 → Apr 2027) whose rule is a mean net result
per trade ≥ 0 and a live fill rate of at least 60% of the backtest's. Nothing
goes live before that.

### Step 1 result: every setting loses in-sample

Design window, profit factor, default fees (taker 0.05% per side):

| Cell | SUI H2-23 | SUI H1-24 | SUI H2-24 | BTC H2-23 | BTC H1-24 | BTC H2-24 | Median |
|---|---|---|---|---|---|---|---|
| fr_k3.0_p95_e0.0 | 0.97 | 0.77 | 0.43 | 0.68 | 0.49 | 0.85 | **0.725** |
| fr_k2.5_p90_e0.0 | 0.78 | 0.76 | 0.72 | 0.56 | 0.55 | 0.63 | 0.675 |
| fr_k3.0_p90_e0.0 | 0.91 | 0.81 | 0.58 | 0.57 | 0.52 | 0.74 | 0.660 |
| fr_k3.0_p95_e0.25 | 0.90 | 0.61 | 0.41 | 0.68 | 0.37 | 0.83 | 0.645 |
| fr_k3.0_p90_e0.25 | 0.78 | 0.71 | 0.60 | 0.57 | 0.44 | 0.68 | 0.640 |
| fr_k2.5_p90_e0.25 | 0.74 | 0.68 | 0.78 | 0.55 | 0.47 | 0.59 | 0.635 |
| fr_k2.5_p95_e0.0 | 0.78 | 0.69 | 0.56 | 0.52 | 0.48 | 0.63 | 0.595 |
| fr_k2.5_p95_e0.25 | 0.74 | 0.53 | 0.56 | 0.48 | 0.33 | 0.57 | 0.545 |

**Step 2 selection (by the pre-registered rule): `fr_k3.0_p95_e0.0`.**

What the design window shows:

* No cell reaches PF 1.0 in any of the 48 cells. The best single cell is 0.97.
* Win rates are 45–63%, so the reversal often happens, but losers outweigh
  winners: the stop beyond the move's extreme and the 60-minute time stop give
  away more than the 50% retracement target earns, after about 10 bp of fees.
* Stronger, more one-sided flushes (k = 3, p = 95) do best, which is the
  direction the research predicts, but the gradient is not enough to cross 1.0.
* Waiting for a deeper limit (e = 0.25 ATR) is worse in every column: the best
  reversals do not come back to the deeper price.

The pre-registration requires one out-of-sample run regardless, so it is run as
specified. A pass needs PF ≥ 1.10 in every pair-year; given an in-sample maximum
of 0.97, it is expected to fail.

### Step 3 result: fails every criterion; the flow condition makes it worse

Out of sample, `fr_k3.0_p95_e0.0`, profit factor (trades):

| Run | SUI 2025 | SUI 2026 YTD | BTC 2025 | BTC 2026 YTD |
|---|---|---|---|---|
| Selected cell, default fees | 0.74 (154) | 0.86 (127) | 0.59 (132) | 0.54 (147) |
| `_ctrl`, low-flow control | 0.77 (79) | 1.29 (47) | 0.70 (29) | 0.93 (23) |
| `_tick`, one-tick fill-through | 0.68 (148) | 0.82 (121) | 0.59 (131) | 0.49 (141) |
| `--fee 0.0007` stress | 0.68 | 0.81 | 0.48 | 0.45 |

Scored against the pre-registered table, per pair:

| Criterion | SUI | BTC |
|---|---|---|
| ≥ 75 trades per year | pass | pass |
| PF ≥ 1.10 each year | **fail** (0.74, 0.86) | **fail** (0.59, 0.54) |
| Verdict WATCH or PASS | **fail** (FAIL) | **fail** (FAIL) |
| Selected minus control ≥ +0.10 each year | **fail** (−0.03, −0.43) | **fail** (−0.11, −0.39) |
| `_tick` PF ≥ 1.05 each year | **fail** | **fail** |
| Fee stress PF ≥ 1.00 each year | **fail** | **fail** |

**FlushReversal fails.** Every bootstrap PF band includes values below 1, no
permutation p-value is below 0.76, and at most 2 of 5 calendar folds are
profitable in any column.

The most informative row is the control. The paper's mechanism says reversal
should be *stronger* after taker-dominated moves. Here, same-size moves *without*
dominant taker flow did better in all four out-of-sample columns. (The control
was not run on the design window, so this comparison exists only out of sample.) On Binance 5m perps in 2023–2026, with candle-level taker data and limit
entries at the signal close, conditioning on one-sided taker flow selects moves
that are more likely to *continue*, not reverse. That matches Osler's
stop-cascade finding better than the liquidity-premium reading. The control's
own numbers (23–79 trades) are too thin to treat as a strategy.

Caveat on fidelity: Freqtrade fills the limit on touch and charges the taker
rate on both legs. The `_tick` row and the fee stress bracket those effects and
both move results down, not up, so fill modelling does not explain the failure.

### Commands (one at a time)

Prepend 5m candles back to 2023 (5m from 2024-10 is already on disk):

```bash
freqtrade download-data -c user_data/config_flushrev.json --userdir user_data --pairs "SUI/USDT:USDT" "BTC/USDT:USDT" --timeframes 5m --trading-mode futures --timerange 20230420-20261031 --prepend
```

Taker-buy volume, about 5 minutes per symbol:

```bash
python user_data/scripts/fetch_binance_taker.py --symbol SUIUSDT --start 2023-04-20 --end 2026-10-31
```

```bash
python user_data/scripts/fetch_binance_taker.py --symbol BTCUSDT --start 2023-04-20 --end 2026-10-31
```

Step 1, design window, 8 cells × 2 pairs × 3 half-years:

```bash
python user_data/scripts/sessionsweep_variants.py --strategy FlushReversal --pair SUI/USDT:USDT BTC/USDT:USDT --timerange 20230512-20231231 20240101-20240630 20240701-20241231
```

Step 3, out of sample. Replace `CELL` with the cell chosen in step 2, for
example `fr_k2.5_p90_e0.0`:

```bash
python user_data/scripts/sessionsweep_variants.py --strategy FlushReversal --only CELL CELL_ctrl CELL_tick --pair SUI/USDT:USDT BTC/USDT:USDT --timerange 20250101-20251231 20260101-20261031
```

```bash
python user_data/scripts/sessionsweep_variants.py --strategy FlushReversal --only CELL --fee 0.0007 --pair SUI/USDT:USDT BTC/USDT:USDT --timerange 20250101-20251231 20260101-20261031
```

## 4i. Funding-rate carry: pre-registered test

The research report's one approach with documented after-cost returns is
delta-neutral funding carry (He, Manela, Ross & von Wachter report a Sharpe
of about 1.8 for BTC under retail costs, in an earlier period; the premium
has been declining). It is not a directional strategy: buy q units on spot,
short q units of the perp, collect funding when it is positive.

Freqtrade cannot hold that two-leg position, so it is tested with a standalone
hourly simulator, `user_data/scripts/carry_backtest.py`, which downloads Binance
spot 1h, perp 1h and funding history from data.binance.vision.

**This section is the pre-registration, committed before any real carry data
was loaded.**

### Rules (fixed)

* Position per 1 USDT of capital: spot notional = 1 / (1 + 1/L) and an equal perp
  short, with the perp leg at leverage L = 2 (margin = notional / 2).
* `always_on`: hedged for the whole window.
* `switched_X` for X ∈ {5%, 10%, 20%}: at each funding settlement take the mean of
  the last 9 settled rates, annualised. Enter when it is above X, exit when it is
  below X/4. Executed at the next hour's close, using only settled rates.
* Costs per leg per side: spot taker 0.10%, perp taker 0.05%, slippage 1 bp (BTC)
  or 3 bp (SUI). Fee stress: all costs × 2 (`--fee-mult 2`).
* Not modelled: liquidation, exchange or counterparty risk, auto-deleveraging,
  transfers between spot and futures wallets. The output counts `margin_ev`, the
  times the perp leg's loss would have used more than 80% of its margin before a
  daily rebalance.

Verified on hand-built data: a perfect hedge has zero price P&L; funding income
matches the closed-form amount; final equity equals funding minus costs plus
basis; entries and exits occur exactly one hour after the signal crosses;
spot archives with microsecond timestamps parse correctly.

### Protocol

1. **Design**, both symbols: 2023-05-12 → 2023-12-31 and 2024-01-01 → 2024-12-31.
2. **Selection:** the rule with the highest *minimum* Sharpe across the four
   design columns; ties go to the higher minimum annualised return. Record it
   here before step 3.
3. **Out of sample, one run:** 2025-01-01 → 2025-12-31 and 2026-01-01 → 2026-10-31,
   both symbols, the selected rule at normal and doubled costs.

### Pass rule (per symbol; every line must hold)

| Criterion | Threshold |
|---|---|
| Annualised net return, each OOS year | ≥ 4% on capital |
| Daily Sharpe, each OOS year | ≥ 1.0 |
| Max drawdown, each OOS year | no worse than −5% |
| Doubled costs, annualised net return, each OOS year | > 0% |

4% is roughly what a stablecoin savings product pays; carry that does not beat
it is not worth the exchange risk. Expectation stated before running: BTC
funding has been compressed since 2024, so BTC may fall short of 4%; SUI
funding is higher but swings negative more often.

### Commands (one at a time)

Downloads about 3 years of spot, perp and funding history for both symbols
(cached under `user_data/data/carry/`), then runs the design window:

```bash
python user_data/scripts/carry_backtest.py --symbol BTCUSDT SUIUSDT --start 2023-05 --end 2026-10 --periods 2023-05-12:2023-12-31 2024-01-01:2024-12-31
```

Out of sample, after the selection is recorded:

```bash
python user_data/scripts/carry_backtest.py --symbol BTCUSDT SUIUSDT --start 2023-05 --end 2026-10 --periods 2025-01-01:2025-12-31 2026-01-01:2026-10-31
```

```bash
python user_data/scripts/carry_backtest.py --symbol BTCUSDT SUIUSDT --start 2023-05 --end 2026-10 --fee-mult 2 --periods 2025-01-01:2025-12-31 2026-01-01:2026-10-31
```

### Design result and selection (2026-11-03, recorded before any out-of-sample run)

Annualised net % / daily Sharpe / max drawdown %, normal costs:

| Rule | BTC 2023 | BTC 2024 | SUI 2023 | SUI 2024 | Min Sharpe |
|---|---|---|---|---|---|
| always_on | 6.13 / 12.50 / -0.20 | 12.40 / 13.76 / -0.30 | 1.94 / 4.31 / -0.55 | 16.88 / 5.78 / -3.47 | 4.31 |
| switched_5 | 4.41 / 7.75 / -0.68 | 10.67 / 12.27 / -0.29 | 3.37 / 2.56 / -2.03 | 10.60 / 5.90 / -1.93 | 2.56 |
| **switched_10** | 4.65 / 9.34 / -0.25 | 8.95 / 10.23 / -0.31 | 5.71 / 5.69 / -0.76 | 11.47 / 6.78 / -1.77 | **5.69** |
| switched_20 | 2.22 / 5.53 / -0.12 | 7.14 / 9.02 / -0.37 | 5.22 / 6.26 / -0.26 | 6.36 / 7.03 / -0.48 | 5.53 |

**Selected: `switched_10`** (highest minimum Sharpe, 5.69; no tie). It goes to the
out-of-sample run unchanged. `margin_ev` was 0 everywhere.

Observations, not changes to the protocol:

* Sharpe ratios of 4-14 come from a smooth, nearly riskless P&L path with no
  liquidation, exchange or de-peg events in the sample. The Sharpe ≥ 1 line is
  therefore easy; the 4% return line and the drawdown line are the ones that bind.
* Funding contributed almost all of the return (basis ±0.5%). 2023 BTC already sat
  near the 4% bar (4.65% selected); 2024 was the high-funding year.
* SUI always-on earned only 1.94% in 2023 because funding was often negative;
  switching helped there, which is why a switched rule won.

### Out-of-sample result (2026-11-03): `switched_10` fails on both symbols

Annualised net % / daily Sharpe / max drawdown %; last column is annualised net % at
doubled costs. Pass needs ≥ 4% / ≥ 1.0 / ≥ −5% / > 0% in every year.

| Symbol, year | Ann % | Sharpe | Max DD % | Ann % at 2× costs | Hedged % of hours | Verdict |
|---|---|---|---|---|---|---|
| BTC 2025 | 1.28 | 3.98 | -0.27 | 0.73 | 38 | fail (return) |
| BTC 2026 (to Oct) | -0.03 | -0.17 | -0.13 | -0.31 | 5 | fail (return, Sharpe, 2× costs) |
| SUI 2025 | -1.36 | -2.08 | -1.36 | -4.03 | 25 | fail (return, Sharpe, 2× costs) |
| SUI 2026 (to Oct) | -0.81 | -1.62 | -0.89 | -2.36 | 14 | fail (return, Sharpe, 2× costs) |

Verdict: **hypothesis rejected** for both symbols. No drawdown line was breached and
`margin_ev` was 0; the failure is that funding no longer pays.

For reference only (not selectable after the fact), every other rule also misses the
4% line in every out-of-sample column. The best is `always_on` BTC 2025 at 3.54%,
and `always_on` falls to 1.2-1.7% in 2026. Funding earned by an always-on hedge:
BTC 13.1% of capital in 2024, then 3.8% in 2025 and 1.6% in 2026 to October; SUI
18.2%, then 1.6% and 1.2%. That matches the research report's prediction of
compressed BTC funding, and SUI compressed even further. The switched rules lost
on SUI because brief funding spikes triggered round trips (10 for `switched_10` in
2025) whose costs exceeded the funding they captured.

Per the pre-registration, no re-tuning of thresholds on this data. Carry is
not worth running at 2025-26 funding levels; revisit only if the 30-day
average BTC funding is back above ~10% a year.

## 4j. Daily trend ensemble on BTC: pre-registered test

Source: the research report `reports/Footprint and best crypto strategies.md`
ranks slow daily trend following as the best-evidenced directional family
(realistic net Sharpe 0.5-1.0, drawdowns 25-45%), and warns that volatility sizing
alone may explain most of its benefit. Every parameter below comes from
literature published before 2022, so 2022-01-01 → 2026-10-31 is post-publication
data for BTC. **This section is committed before any real daily data is loaded.**

Simulator: `user_data/scripts/trend_backtest.py` (standalone daily simulation,
reusing the data.binance.vision loader and cache from `carry_backtest.py`).
`--selftest` passes 7 synthetic checks: closed-form funding, 1x equivalence with
buy-and-hold, exact entry cost, no look-ahead (changing later prices leaves earlier
equity unchanged), the leverage cap, the funding day boundary, and bootstrap sanity.

### Rules (fixed)

* Daily close = last 1h perp close of the UTC day; signal computed on it and executed
  at that price (= next day's open).
* s = mean(sign(r20), sign(r60), sign(r120), sign(close − SMA50)) ∈ [−1, 1].
  Long/flat (LF): exposure = max(s, 0). Long/short (LS): exposure = s.
* Target notional = exposure × min(30% / vol30, 1.5) × equity; vol30 = 30-day std of
  daily log returns × √365.
* Rebalance only when |target − current| ≥ 0.20 × equity; a move to zero or a change of
  sign is always executed. No stops, no other filters.
* Costs: taker 0.05% + slippage 2 bp (BTC) / 5 bp (SUI) per side on traded notional;
  stress case at 2×. Funding from Binance history, paid on each settlement at the perp
  price.
* Controls: C1 = the same sizing with s ≡ 1 (vol-targeted always-long); C2 = 1x perp
  buy-and-hold with funding.

### Pass rule (BTC, 2022-01-01 → 2026-10-31; LF and LS judged separately; every line)

| Criterion | Threshold |
|---|---|
| Net daily Sharpe, annualised | ≥ 0.50 |
| Stationary block bootstrap (20-day mean block, 10,000 draws), 10th percentile Sharpe | > 0 |
| Sharpe − C1 Sharpe | ≥ +0.15 |
| Max drawdown | ≤ 35% and ≤ 0.75 × C1's |
| Worst calendar year (2022 … 2026 YTD) | no worse than −20% |
| Doubled-cost Sharpe | ≥ 0.35 |
| Each of the 4 components alone (same mapping and sizing) | ≥ 3 of 4 with Sharpe > 0 |

* BTC 2020-02 → 2021-12 is printed as a code-sanity window only (starts when 120 days
  of warm-up exist); it is not judged and nothing is tuned on it.
* SUI from its first warm day to 2026-10-31 is report-only: "consistent" if Sharpe > 0,
  never a pass.
* Prior stated before running: 25-35% chance of passing; the C1 line is the most
  likely to fail.
* After a pass: six months of dry run, judged on execution (fills within 10 bp of the
  modelled daily price, funding as modelled), not P&L. After a fail: no re-tuning on
  this window; the conclusion is that no tested directional rule beats vol-targeted
  holding for this account.

### Deviations from the report's draft, decided before data

* The report asked for a Freqtrade run that matches a pandas simulation within
  0.1 Sharpe. Replaced by the synthetic self-tests above: Freqtrade cannot apply the
  0.20-of-equity rebalancing band to a vol-targeted position without a custom
  position-adjustment strategy that would itself need verifying, and the sandbox
  cannot reach Binance data to cross-check it.
* Prices are perp last-trade 1h closes, not mark prices (the cached archive has no
  mark klines). Difference on daily bars is a few bp.
* "Always execute a move to zero or a sign change" is added so that a flat signal
  cannot leave a residual position below the 0.20 band.

### Command (one run; downloads BTC from 2019-09 and reuses the SUI cache)

```bash
python user_data/scripts/trend_backtest.py
```

### Result (2026-11-03): both ensembles PASS every pre-registered line on BTC

BTC 2022-01-01 → 2026-10-31, normal costs (doubled-cost Sharpe in brackets):

| Rule | Sharpe | Ann % | Max DD % | Boot 10th pct | Worst year | Components > 0 |
|---|---|---|---|---|---|---|
| LF ensemble | 0.86 (0.81) | 15.1 | -16.7 | 0.19 | -11.5% (2022) | 4/4 |
| LS ensemble | 0.71 (0.63) | 16.4 | -26.6 | 0.12 | -9.2% (2022) | 4/4 |
| C1 vol-target long | 0.33 (0.32) | 5.5 | -52.1 | -0.32 | -42.6% (2022) | n/a |
| C2 1x buy-and-hold | 0.37 | 4.9 | -69.5 | n/a | -67.1% (2022) | n/a |

Calendar years, LF: 2022 -11.5, 2023 +49.9, 2024 +50.9, 2025 -5.1, 2026 YTD +3.9.
LS: -9.2, +47.6, +36.2, -0.6, +14.5. LF was in the market 43% of days; turnover 16x
equity a year; costs -8.2% and funding -19.4% of starting capital over the window.

SUI (report only, 2023-09-01 → 2026-10-31): LF Sharpe 0.85, max DD -16.6%; LS 0.70;
C1 0.70 with max DD -39.9%. Label: **consistent** for both.

Sanity window (BTC 2020-05 → 2021-12, not judged): LF 2.01, LS 1.84, C1 1.56.
BTC perp archives start 2020-01, so this window began 2020-05-01.

Caveats, stated with the pass:

* The margin is thin where it matters: the bootstrap lower bounds (0.19, 0.12) are just
  above zero, as the pre-registration expected for under five years of data.
* The edge over C1 is mostly drawdown avoidance: the ensembles stepped aside in 2022
  (-11.5% vs -42.6%) and captured most of 2023-24. In 2025-26 they were roughly flat,
  as was BTC; there is no sign yet of an edge in sideways markets.
* Two variants were tested with no multiple-testing correction (none was
  pre-registered); both pass, so the choice does not change the verdict.
* The parameters were taken from pre-2022 literature, but chosen in 2026 by someone
  who knew that family had worked; some hindsight in the family choice cannot be
  ruled out.
* Verification was by synthetic self-tests, not an independent second implementation.

Next step per the pre-registration: six months of dry run, judged on execution,
not P&L. Before that, a Freqtrade implementation should reproduce this result on the
same window within 0.1 Sharpe, closing the cross-check dropped above.

### Freqtrade implementation and cross-check (`DailyTrend`)

`user_data/strategies/DailyTrend.py` implements the long/flat ensemble in Freqtrade
with no new parameters: 1d timeframe, market orders at the next daily open, entry
stake = target / leverage, `adjust_trade_position` for the 0.20-of-equity band, exit
signal when exposure is 0, leverage 2 (isolated), notional ≤ 1.5x equity, no stops.
Config: `user_data/config_dailytrend.json` (BTC, 10,000 USDT dry-run wallet,
placeholder credentials).

`user_data/scripts/trend_crosscheck.py` rebuilds daily mark-to-market equity from
the backtest's filled orders and Freqtrade's own candles, mark and funding data
(Freqtrade's report counts only realised profit, which says little for weeks-long
positions), and compares its Sharpe with `trend_backtest.py`. Pass: |difference| ≤
0.10 (the pre-registered tolerance).

Synthetic check (random trending data, 2022-01 → 2026-10): 55 trades, 165 fills,
Sharpe 0.050 vs 0.072, difference −0.023, PASS. Freqtrade's funding total was 5%
higher than the rebuild's because it charges a settlement that falls exactly on a fill
timestamp on both sides of the fill; Binance charges it once. This makes Freqtrade's
own reported profit slightly pessimistic; the rebuild charges each settlement once.

Liquidation note: at leverage 2 with isolated margin, a ~45% fall from the average
entry would liquidate. At ≤ 1.5x notional, and with the volatility target and band,
that never came close in the test window, but for live use cross margin or leverage
3 with a smaller margin share would be safer choices to review before the dry run.

```bash
freqtrade download-data --config user_data/config_dailytrend.json --userdir user_data --pairs BTC/USDT:USDT --timeframes 1d --trading-mode futures --timerange 20210601-20261101
```

```bash
freqtrade backtesting --config user_data/config_dailytrend.json --userdir user_data --strategy DailyTrend --timerange 20220101-20261101 --fee 0.0007 --export trades
```

```bash
python user_data/scripts/trend_crosscheck.py
```

#### Cross-check on real data (2026-11-03): PASS, provisional

| | Sharpe | Ann % | Max DD % | Final (x start) |
|---|---|---|---|---|
| Freqtrade DailyTrend (rebuilt daily equity) | 0.834 | 14.6 | -16.9 | 1.937 |
| trend_backtest.py (LF ensemble) | 0.863 | 15.1 | -16.7 | 1.975 |

Difference −0.029 (limit ±0.10). 48 trades, 182 fills, fees 806 USDT, funding 1,797
USDT (rebuild) vs 1,871 (Freqtrade's double count at fill timestamps).

Caveat: the local Freqtrade 1h funding-rate and mark files started at 2023-04-20
(earlier downloads), so the Freqtrade run had no funding before that date, while the
simulation had full funding. The missing period is mostly the 2022 bear market, when
the strategy was largely flat, so the effect should be small, and it would make
Freqtrade look better, not worse; Freqtrade still came out slightly below. To be
final, rerun after `download-data ... --prepend` fills the funding and mark history.

Freqtrade's own "Sharpe (closed trades) 0.11" and "Sharpe (daily wallet balance)
1.16" are not comparable: both ignore open-position P&L. Use the rebuilt figure.

#### Cross-check after filling the funding history: PASS (final)

After `download-data --prepend` filled the 1h funding and mark history back to
2021-06, the rebuild (which reads those files) gave Sharpe 0.819 vs 0.863, difference
−0.044, within ±0.10. Funding in the rebuild rose to 1,952 USDT. Freqtrade reused its
cached backtest (`--cache day`), so its fills are from the run without pre-2023-04
funding; funding only enters the fills through the equity used for sizing (about 1%
of equity), so this does not change the verdict.

Remaining gap of ~0.04 Sharpe: Freqtrade sizes from its own equity estimate and fills
at the daily open with contract-precision rounding; the simulation uses exact equity
and the last 1h close. Both effects are small and go in either direction.

### Dry run (pre-registered: six months from November 2026)

Config: `user_data/config_dailytrend_dryrun.json`. Same strategy and parameters, but
**cross margin** (with one position at ≤ 1.5x notional, liquidation would need a
~65% fall in BTC, against ~45% for 2x isolated) and its own database
`user_data/dailytrend_dryrun.sqlite`.

Judged on execution, not profit (six months is too short for P&L to mean anything):

* Every signal day produces the expected action (enter, rebalance, exit or nothing)
  within the first hour after 00:00 UTC; no missed days.
* Fill prices within 10 bp of the 00:00 UTC open on average.
* Funding charged within 10% of rate × notional from Binance's published history.
* Position size within 5% of the model's target after each rebalance.

A dry run fills at the simulated order book, so it cannot measure real slippage. If
the dry run passes, the next step is a small live allocation, judged the same way.

### SUI: exploratory only (decided 2026-11-03)

The pre-registration allows SUI only a "consistent / inconsistent" label (it was
consistent: LF Sharpe 0.85, max DD −16.6%, 2023-09 → 2026-10). SUI has about three
years of history, one listing-era bull run (2024: +54%) and no pre-2022 data, so a
SUI run cannot validate the rule; it can only show that the same code behaves on SUI.

Same strategy, no changes. Config `user_data/config_dailytrend_sui.json` (SUI only,
cross margin, own database `dailytrend_sui_dryrun.sqlite`, separate 10,000 USDT
dry-run wallet). Costs: `--fee 0.001` (0.05% taker + 5 bp slippage, as in the
simulation). Because SUI's volatility is 2-3x BTC's, the 30% volatility target keeps
its position near 0.3-0.5x equity most of the time.

Freqtrade window starts 2023-09-15 (SUI perp listed 2023-05-03; 130 startup candles).
Cross-check tolerance as for BTC: |Sharpe difference| ≤ 0.10.

```bash
freqtrade download-data --config user_data/config_dailytrend_sui.json --userdir user_data --pairs SUI/USDT:USDT --timeframes 1d --trading-mode futures --timerange 20230501-20261101 --prepend
```

```bash
freqtrade backtesting --config user_data/config_dailytrend_sui.json --userdir user_data --strategy DailyTrend --timerange 20230915-20261101 --fee 0.001 --export trades --cache none
```

```bash
python user_data/scripts/trend_crosscheck.py --pair SUI/USDT:USDT --symbol SUIUSDT --start 2023-09-15 --fee 0.001
```

## 5. Comparing variants in one go

`user_data/scripts/sessionsweep_variants.py` runs a set of variants and prints one
compact table with the London / NY split. It needs data that is already downloaded.

```bash
python user_data/scripts/sessionsweep_variants.py
```

The full set has 54 variants and takes about 54 minutes per pair/year. `--trend-set`
runs the six trend-filter variants, `--enhance-set` the eight structural
enhancements, `--entry-set` the nine breakout-entry variants, `--timing-set` the
twelve session-window variants, `--htf-set` the twelve higher-timeframe RSI/trend
variants. `--pair` and `--timerange` accept several values; with more than one
combination the script prints a profit-factor grid at the end. Use `--only` to pick
specific variants.

To check a winner out of sample, download the previous year and rerun on it:

```bash
freqtrade download-data --config user_data/config_sessionsweep.json --userdir user_data \
  --pairs "SUI/USDT:USDT" --timeframes 5m 1h 4h --trading-mode futures \
  --timerange 20241020-20251031 --prepend
```

`--prepend` is required because data for later dates already exists.

```bash
python user_data/scripts/sessionsweep_variants.py --trend-set --timerange 20241031-20251031
```

## 5b. Robustness tables (`user_data/scripts/robustness.py`)

`sessionsweep_variants.py` now prints a ROBUSTNESS table after every variant table
and a verdict column in the final cross-pair summary (`--no-robust` skips it).
Ported from HKUDS/Vibe-Trading's validation and per-regime evidence modules.

| Column | Meaning | A real edge shows |
|---|---|---|
| `p_perm` | One-sided sign-flip permutation test: chance that random +/- luck gives this average trade | `*` = below 0.05 / number of tests run |
| `exp95%lo` | Bootstrap 2.5th percentile of USDT per trade | > 0 |
| `PF95%lo..hi` | Bootstrap 95% band for profit factor | lower end > 1 |
| `WF+` | Equal calendar folds (5, by close date) with PF > 1 | >= 3/5 |
| `bull/bear/chop` | Trades split by the pair's trailing 30-day return at the prior daily close (>= +10% bull, <= -10% bear, else chop; cached 1h futures candles) | PF > 1 in more than one regime |

Verdict across all pair/year columns: **PASS** (PF95%lo > 1, p_perm below the
corrected bar and >= 60% profitable folds everywhere), **WATCH** (positive
expectancy and stable folds everywhere, not yet beyond luck), **FAIL** (loses
somewhere), **THIN** (< 30 trades in a column). The multiple-testing correction
matters: 8 variants x 4 columns = 32 tests, so the bar is p < 0.0016.

## 5c. Regime gate (`use_regime_filter`) and its pre-registered test

The 2026-11-01 robustness run of `SessionSweep1h --enhance-set` failed every
variant, but the regime split showed the SUI profit sat in the **bull** bucket in
both years (risk1 PF 1.08 / 1.79, retest 1.29 / 1.61, timestop6h 1.07 / 1.71;
bear and chop at or below 1). BTC did not show it. Because that idea came from
looking at the split, it needs unseen data.

New strategy parameters (all off by default, in `SessionSweep.py`, inherited by
`SessionSweep1h`):

| Parameter | Default | Meaning |
|---|---|---|
| `use_regime_filter` | False | Only allow entries (long and short) when the pair's trailing return is high enough |
| `regime_lookback_days` | 30 | Trailing window, measured from the previous daily close (no look-ahead) |
| `regime_min_return_pct` | 10.0 | Minimum trailing return in % |

The definition matches the "bull" bucket in `robustness.py`. When the gate is on,
`startup_candle_count` rises to (lookback + 2) days so the first tradable candle
already has a regime value; every other variant keeps its original data window.
Download at least ~32 days of extra history before each timerange.

Runner: `--regime-set` runs `rg_risk1`, `rg_first_sweep`, `rg_retest`,
`rg_timestop6h` next to their ungated controls.

**Pre-registered test** (decided 2026-11-01, before any new data is seen):

* Candidates: exactly four, `rg_risk1`, `rg_first_sweep`, `rg_retest`,
  `rg_timestop6h` on `SessionSweep1h`, unchanged.
* In-sample reference only (does not count): SUI 2024-25 and 2025-26.
* New data: SUI 2023-10-31 to 2024-10-31, and ETH/USDT:USDT for 2024-25 and
  2025-26. Three unseen columns.
* Pass: PF above 1.10 in every unseen column with at least 30 trades, and a
  robustness verdict other than FAIL. Expect ~50-80 trades per column; fewer than
  30 is reported as THIN and cannot pass.
* If a candidate passes: a 4-week dry run, not live money.

```bash
freqtrade download-data --config user_data/config_sessionsweep.json --userdir user_data --pairs "SUI/USDT:USDT" --timeframes 1h 4h --trading-mode futures --timerange 20230920-20241031 --prepend
```

```bash
freqtrade download-data --config user_data/config_sessionsweep.json --userdir user_data --pairs "ETH/USDT:USDT" --timeframes 1h 4h --trading-mode futures --timerange 20240920-20261031
```

```bash
# in-sample reference
python user_data/scripts/sessionsweep_variants.py --strategy SessionSweep1h --regime-set --pair SUI/USDT:USDT --timerange 20241031-20251031 20251031-20261031
# the unseen test
python user_data/scripts/sessionsweep_variants.py --strategy SessionSweep1h --regime-set --pair SUI/USDT:USDT --timerange 20231031-20241031
python user_data/scripts/sessionsweep_variants.py --strategy SessionSweep1h --regime-set --pair ETH/USDT:USDT --timerange 20241031-20251031 20251031-20261031
```

### Regime-gate test result (2026-11-01): all four candidates fail

Pass mark: PF > 1.10 in every unseen column with >= 30 trades.

| Candidate | SUI 2023-24 | ETH 2024-25 | ETH 2025-26 | Min | Trades |
|---|---|---|---|---|---|
| rg_risk1 | 0.99 | 0.78 | 0.74 | 0.74 | 106 / 108 / 86 |
| rg_first_sweep | 0.93 | 0.87 | 0.78 | 0.78 | 100 / 102 / 76 |
| rg_retest | 0.83 | 0.64 | 0.73 | 0.64 | 100 / 97 / 71 |
| rg_timestop6h | 1.03 | 0.78 | 0.59 | 0.59 | 108 / 117 / 89 |

* The bull-regime effect did **not** replicate: SUI 2023-24 bull-bucket PF was
  0.82-1.03 (vs 1.07-2.01 in the two years it was found in), and ETH's bull bucket
  was worse than its chop bucket in both years (0.64-0.87 vs ~1.0).
* Every permutation p-value is above 0.45 and every bootstrap PF band includes
  values below 1. The gate does halve trade count and drawdown, but it does not
  create an edge.
* Data note: ETH data starts 2024-10-20, so the gated ETH 2024-25 column began
  ~20 days late (gated n 108 vs 110 ungated bull trades; 4 folds instead of 5).
  Too small to change the verdict.

Verdict: hypothesis rejected. Per the pre-registration, no further regime
variants on this data.

## 5d. Order-flow logging and the forward desk-filter test

Every OHLCV-only family above failed on unseen data. The one thing the live SUI
desk uses that the bot cannot see is order flow (L/S falling, OI dropping, taker
delta). OKX keeps only ~60 days of hourly per-contract history (~5 days at 5m;
daily since 2024), so it cannot be backtested over years: it has to be collected.

| Script | What it does |
|---|---|
| `user_data/scripts/orderflow_logger.py` | Pulls OKX OI, all-account L/S, top-trader position L/S, taker buy/sell (1H and 5m) and funding for SUI/BTC/ETH perps into `user_data/orderflow/*.csv`. First run back-fills everything OKX still has; later runs merge new rows. |
| `user_data/scripts/orderflow_join.py` | Adds order-flow features to backtest trades, using only hourly bars that closed before the entry and the hour immediately before it (no look-ahead, no stale data across gaps), then scores the trades by them with the robustness numbers. |

Features at entry: `oi_chg_3h`, `ls_chg_3h`, `taker_delta_3h`, `top_pos`, `funding`.

**Pre-registered desk filter** (written before any result): longs need
`ls_chg_3h < 0 and oi_chg_3h < 0` ("flush ending"); shorts need
`ls_chg_3h > 0 and taker_delta_3h < 0` ("retail chasing into sellers").

**Pre-registered forward test** (decided 2026-11-01):

* Strategy: `SessionSweep1h`, variant `risk1`, unchanged. Pairs SUI, BTC, ETH.
* Only trades opening after 2026-11-02 count (the 60-day back-fill is exploratory).
* Score when the desk-PASS bucket has >= 30 trades (likely 3-6 months).
* Pass: desk-PASS PF > 1.10, desk-PASS p_perm < 0.05 (one test, no correction),
  and desk-PASS PF above desk-FAIL PF. Fail on any of the three.

```bash
# once now (back-fill), then hourly via crontab -e:
python user_data/scripts/orderflow_logger.py
# 7 * * * * cd /Users/<you>/freqtrade && .venv/bin/python user_data/scripts/orderflow_logger.py >> user_data/orderflow/log.txt 2>&1

# exploratory read on the back-filled ~60 days
python user_data/scripts/sessionsweep_variants.py --strategy SessionSweep1h --only risk1 --pair SUI/USDT:USDT BTC/USDT:USDT ETH/USDT:USDT --timerange 20260902-20261101
python user_data/scripts/orderflow_join.py --last 3
```

## 6. Suggested next tests

1. **Done: out-of-sample check of the trend filter.** It failed (section 4), so the
   parameter tests below are unlikely to rescue the strategy on SUI.
   When isolating sessions, remember that with one open trade the sessions
   compete for the slot, so compare session-only runs, not the baseline split.
2. **Sweep definition.** `sweep_lookback` 1 (classic single-candle rejection)
   vs 3 vs 6 vs 12; `sweep_min_pct` 0 vs 0.1 vs 0.25 to filter one-tick sweeps.
3. **Range quality.** `asia_range_min_pct` 0.3 → 0.6 → 1.0. Tiny ranges tend to
   produce many 1:1 coin flips; a maximum range filter may be worth adding too.
4. **Exit geometry.** `tp_range_fraction` 0.5 / 0.75 / 1.0, with and without
   `breakeven_at_midrange`. Then try native trailing
   (`trailing_stop=True`, offset 0.06, positive 0.03) to catch extended moves.
5. **Trend filter.** `use_trend_filter=true` with `trend_ema_len` 20 / 50 / 100.
   Expect fewer trades; check whether win rate rises enough to pay for it.
6. **Reward:risk gate.** `min_rr` 1.0 and 1.5. Many sweeps right at the start of
   London have a tight stop and a full-range TP (high RR); late-session ones do not.
7. **Time flatten.** `exit_at_session_end=true` at 17:00 vs 21:00 UTC vs off, to
   see whether holding into the next Asia session helps or hurts.
8. **Robustness.** Walk-forward (e.g. 9 months in-sample hyperopt, 3 months
   out-of-sample), `--fee 0.0006` vs the default taker fee, and `--timeframe-detail 1m`
   for more realistic intra-candle stop/TP ordering when both are hit in one 5m candle.
9. **Leverage sanity.** Backtest at 1x first; leverage only scales the curve
   (and the funding cost) once the 1x edge is confirmed.
10. **Other pairs / sessions.** The strategy is pair-agnostic; try BTC and ETH
    perps, and alternative Asia definitions (e.g. 01:00–08:00 to include Tokyo open).
