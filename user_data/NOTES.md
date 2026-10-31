# SessionSweep – notes

Session-timing liquidity-sweep strategy for Freqtrade, built for
**SUI/USDT:USDT** (Binance USDT-M perpetual), 5m timeframe, 1h informative.

| File | Purpose |
|---|---|
| `user_data/strategies/SessionSweep.py` | The strategy (all logic + parameters, heavily commented) |
| `user_data/config_sessionsweep.json` | Futures / isolated / dry-run config, 1 open trade, **API keys are placeholders** |
| `user_data/scripts/sessionsweep_backtest.sh` | Exact download + backtest + session-split commands for your Mac |
| `user_data/scripts/sessionsweep_variants.py` | Runs a batch of parameter variants and prints one comparison table |
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
  --pairs "SUI/USDT:USDT" --timeframes 5m 1h --trading-mode futures \
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

## 5. Comparing variants in one go

`user_data/scripts/sessionsweep_variants.py` runs a set of variants and prints one
compact table with the London / NY split. It needs data that is already downloaded.

```bash
python user_data/scripts/sessionsweep_variants.py
```

The default set is baseline, NY only, London only, 1h trend filter, NY only with
trend filter, `min_rr` 1.5, `sweep_lookback` 1, `asia_range_min_pct` 0.6, a 0.75
TP with break-even, and a 17:00 UTC flatten. It takes about ten minutes.
Use `--only` to pick some, and `--timerange` to test another window.

To check a winner out of sample, download the previous year and rerun on it:

```bash
freqtrade download-data --config user_data/config_sessionsweep.json --userdir user_data \
  --pairs "SUI/USDT:USDT" --timeframes 5m 1h --trading-mode futures --timerange 20241020-20251031
```

```bash
python user_data/scripts/sessionsweep_variants.py --timerange 20241031-20251031
```

## 6. Suggested next tests

1. **Baseline, then isolate sessions.** Run the full 12 months, then
   `trade_ny=false` and `trade_london=false` separately. Compare profit factor
   and expectancy per tag; if one session is clearly negative, disable it.
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
