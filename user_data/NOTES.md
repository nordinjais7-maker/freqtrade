# SessionSweep – notes

Session-timing liquidity-sweep strategy for Freqtrade, built for
**SUI/USDT:USDT** (Binance USDT-M perpetual), 5m timeframe, 1h informative.

| File | Purpose |
|---|---|
| `user_data/strategies/SessionSweep.py` | The sweep-and-reclaim strategy (all logic + parameters, heavily commented) |
| `user_data/strategies/SessionMomentum.py` | The Asia-range breakout momentum strategy (section 4e) |
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
