# Footprint charts (cluster / volume-at-price / bid x ask) for crypto perps and futures

Source tags: [A] academic, [I] industry/exchange, [V] vendor, [E] educator, [N] anecdotal/forum, [L] local repo (authoritative for Freqtrade behaviour).
Access note: atas.net and developers.binance.com could not be reached from this environment (DNS blocked). arxiv/SSRN papers were not opened. Everything attributed to ATAS, Binance API docs, Sierra Chart, NinjaTrader, Kavajecz & Odders-White and Silantyev below comes **from search-result snippets only**, not full-page reads. The local Freqtrade code was read in full (repo HEAD `dfc1ae1`).

## 1. Definitions: what a footprint shows

### Takeaway
A footprint splits each bar's traded volume by price level and by aggressor side. "Bid" volume is sellers hitting the bid and "ask" volume is buyers lifting the offer. Most named patterns are threshold rules on that grid: imbalances, stacks, POC, unfinished auctions, exhaustion and absorption. Vendors broadly agree on the definitions but not on parameters. Ratios run from 150% to 400%, and some platforms compare levels diagonally while others compare at the same price.

### Cited Findings
- **Bid/ask per level and delta.** NinjaTrader's name for footprint bars is "Volumetric bars". It describes them as tracking bid and ask volume tick by tick to spot imbalance, absorption and exhaustion — [NinjaTrader blog, footprint charts guide](https://ninjatrader.com/futures/blogs/footprint-charts-guide/) [V]. Delta is ask (aggressive buy) volume minus bid (aggressive sell) volume, per level or per bar — [LuxAlgo, Footprint Concepts](https://www.luxalgo.com/library/concept/footprint-concepts.md) [V/E].
- **Diagonal imbalance.** Ask volume at price P is compared with bid volume one tick lower (P−1), because the competing aggressive trades sit one tick apart — [LuxAlgo, Bid/Ask Imbalance](https://www.luxalgo.com/library/concept/bid-ask-imbalance.md) [V/E]. Sierra Chart's Numbers Bars offer "Diagonal Dominant Side" comparisons, which compare "the bid traded volume of one price to the ask traded volume of the price located directly above". Users configure "Compare Thresholds = 300 (%)". Builds 1267 and later add "Enable Diagonal Zero Bid/Ask Compares" for zero-volume sides — [Sierra Chart Support Board thread 6802](https://www.sierrachart.com/SupportBoard.php?ThreadID=6802) [V, snippet only]. A TradingView open-source script states the rule as `buy[idx] ≥ ratio × sell[idx−1]` — [Order Flow Footprint [JOAT]](https://de.tradingview.com/script/3QFpGbCR-Order-Flow-Footprint-JOAT/) [N].
- **Threshold.** About 300% (3:1) is the common default, with a minimum-volume filter so near-empty levels cannot trigger a flag — [LuxAlgo](https://www.luxalgo.com/library/concept/bid-ask-imbalance/) [V/E].
- **Stacked imbalance.** Three or more consecutive levels in one bar imbalanced on the same side. Traders then treat the zone as support or resistance on a retest — [LuxAlgo](https://www.luxalgo.com/library/concept/footprint-concepts.md) [V/E]; [The Right Trader](https://therighttrader.com/learn/volume-and-order-flow/stacked-imbalances) [E]; [FuturesHive guide](https://www.futureshive.com/blog/footprint-charts-complete-guide-2025) [E]. NinjaTrader staff say volumetric-bar imbalance values are **not exposed to NinjaScript**, there is no supported stack-detection code, and it is an open feature request (SFT-3586) — [NinjaTrader forum thread 1263210](https://forum.ninjatrader.com/forum/ninjatrader-8/strategy-development/1263210-stacked-imbalances) [V-staff/N].
- **POC and value area.** The POC is the price with the most volume (or TPOs). The value area expands outward from the POC until it holds about 70% of activity. CQG documentation uses 70% and a later CQG primer uses 68%, so the threshold is not standard — [CQG MPVA help](https://help.cqg.com/cqgic/25/Documents/marketprofilevalueareasmpva.htm) [V]; [CQG Volume Profile primer 2026](https://news.cqg.com/workspaces/2026/07/cqg-one-primer-volume-profile-study) [V]. The 70% figure is justified as roughly one standard deviation of a bell curve — [Market profile, Wikipedia](https://en.wikipedia.org/wiki/Market_profile) [E]; [CBOT Market Profile study guide (PDF)](https://www.quastic.cz/wp-content/uploads/2017/08/CBOT-Market_Profile-EN.pdf) [I]. Market Profile was introduced publicly in 1985 as a CBOT product (Steidlmayer) — [Wikipedia](https://en.wikipedia.org/wiki/Market_profile) [E].
- **Unfinished / finished auction.** An unfinished auction is a bar extreme that still has two-sided trade: bid trades at the high or ask trades at the low. A finished auction has zero volume on one side at the extreme. ATAS marks unfinished-auction lines until price returns. ATAS itself says "there is no 100% guarantee that the price will come back" and that such levels "can hardly be considered an independent instrument" — [ATAS, "Unfinished auction: what it is and how to trade it" (2019)](https://atas.net/volume-analysis/basics-of-volume-analysis/unfinished-auction-what-it-is-and-how-to-trade-it) [V, snippet only].
- **Absorption.** Heavy aggressive volume that fails to move price because passive orders soak it up — [LuxAlgo](https://www.luxalgo.com/library/concept/footprint-concepts.md) [V/E]; [Optimus Futures, absorption vs exhaustion](https://optimusfutures.com/blog/?p=19691) [I-broker/E].
- **Exhaustion print.** Very thin aggressive volume at the bar extreme, read as buyers or sellers running out. One TradingView script instead defines it as bar delta above a multiple of its recent average — [LuxAlgo](https://www.luxalgo.com/library/concept/footprint-concepts.md) [V/E]; [Delta Microstructure Analysis script](https://www.tradingview.com/script/WBhuasLl-Delta-Microstructure-Analysis) [N]. The two definitions disagree: one looks for thin volume, the other for large delta.
- **Delta divergence.** Price makes a new high or low that cumulative or bar delta does not confirm — [NexusFi Academy](https://nexusfi.com/a/strategies/advanced-footprint-chart-patterns) [E].
- Axia Futures, Jigsaw, Exocharts and Bookmap: no primary definitions were retrieved (no search hits, or domains unreachable). Bookmap appears only in passing as a separate data-subscription platform — [NexusFi](https://nexusfi.com/a/platforms/footprint-charts) [E].

### Inferences
- Every footprint signal is a deterministic function of (price, size, aggressor side, time) trade records plus a bin size. That makes all of them reproducible offline from trade prints. Absorption and "pulling/stacking" in the true order-book sense are the exception, because they need resting-depth data.
- The thresholds are free parameters: ratio, minimum volume, stack length and tick or bin size. Each extra parameter raises the risk of overfitting in any backtest.

### Gaps
- No full-text vendor manuals were read for ATAS, Exocharts, Bookmap, Axia or Jigsaw. Their exact default parameters are unverified.

## 2. Practitioner strategies and the evidence for an edge

### Takeaway
The commonly taught setups are stacked-imbalance continuation or retest, unfinished-auction revisit, delta divergence or exhaustion reversal, and POC migration or value-area rotation. I found **no** systematic, out-of-sample, after-cost test of any of them, for crypto or for regulated futures, from academia or from vendors with disclosed methodology. The closest academic evidence is about mechanism, not tradable rules. Support and resistance cluster where limit-order depth sits, and signed trade flow explains contemporaneous price moves in BTC perps. Explaining a move as it happens is not predicting the next one.

### Cited Findings
- Taught setups (education/vendor only):
  - stacked imbalances as continuation and as support/resistance on retest;
  - unfinished auctions as revisit magnets;
  - exhaustion and absorption at extremes as reversal signals;
  - delta divergence as a reversal warning, which is "noise" away from key levels;
  - stops placed beyond the signal bar.

  Sources: [NexusFi Academy, Advanced Footprint Patterns](https://nexusfi.com/a/strategies/advanced-footprint-chart-patterns) [E]; [FuturesHive](https://www.futureshive.com/blog/footprint-charts-complete-guide-2025) [E]; [Optimus Futures guide](https://optimusfutures.com/blog/footprint-charts/) [I/E]; [footprint-lab](https://footprint-lab.com/guides/order-flow-imbalances/) [E]; [tapedelta](https://tapedelta.com/blog/stacked-imbalances-footprint-chart-guide) [E].
- The only performance figure found is a **48% win rate for a single stacked imbalance**, which the article itself calls below breakeven after commissions. It gives no dataset, period or method — [NexusFi Academy](https://nexusfi.com/a/strategies/advanced-footprint-chart-patterns) [E/N, low quality].
- An educator warns against backtests "without out-of-sample checks and across different volatility regimes" for footprint rules — [AlgoStorm](https://algostorm.com/footprint-charts/) [E].
- Volume-profile support: a vendor's own test (2016–2026, 731 Thai stocks, daily bars) reports that volume-profile support "held" 59% of touches. In 41% of touches, price closed more than 3% below the level within 10 days. No baseline bounce rate was given and there is no independent replication — [Deepscope, "Support and Resistance: What Volume-Profile Levels Actually Do (10-Year Test)"](https://deepscope.com/support-resistance-volume-profile/) [V, snippet only]. This is equities, not crypto and not intraday.
- Market Profile / value area: no peer-reviewed empirical test was found. Steidlmayer's books present value-area reference trading as the author's own method without statistical tests — [Steidlmayer & Hawkins, *Steidlmayer on Markets*, 2nd ed. (Wiley 2003)](https://dokumen.pub/steidlmayer-on-markets-trading-with-market-profiletm-2nbsped-0471215562.html) [E]; [Steidlmayer & Koy, *Markets and Market Logic* (1986)](http://www.r-5.org/files/books/trading/charts/market-profile/Peter_Steidlmayer_Kevin_Koy-Markets_and_Market_Logic-EN.pdf) [E]. Claims that price outside value has a "high probability" of returning are vendor assertions — [ATAS blog 2018](https://atas.net/blog/market-profiles-3-things-that-can-improve-your-trading/) [V, snippet].
- **Mechanism (academic).** Kavajecz & Odders-White (2004, *Review of Financial Studies* 17(4):1043–1071) find that support and resistance levels coincide with peaks in limit-order-book depth. They argue that technical rules "locate depth already in place" rather than predict — [RePEc listing](https://ideas.repec.org/a/oup/rfinst/v17y2004i4p1043-1071.html); [Wharton WP PDF](https://rodneywhitecenter.wharton.upenn.edu/wp-content/uploads/2014/04/0108.pdf) [A, snippet only]. This is equities and pre-crypto.
- **Crypto trade-flow imbalance (academic).** Silantyev (2019, *Digital Finance* 1:191–218) used BitMEX XBTUSD perpetual trade and quote data. Trade-flow imbalance (signed aggressor volume, which is what footprint delta measures) explains **contemporaneous** price changes better than aggregate order-flow imbalance. The paper names thin depth and low update rates as the distinguishing traits of crypto microstructure — [RePEc](https://ideas.repec.org/a/spr/digfin/v1y2019i1d10.1007_s42521-019-00007-w.html) [A, abstract/snippet only].
- Companion local notes cover the wider order-flow literature (OFI, book imbalance, maker fill-vs-return trade-off), including arXiv 2502.18625, where net-of-fee imbalance-based maker variants are all negative — `/home/user/freqtrade/research_notes/BTC SUI futures orderflow edges/orderflow_book_imbalance.md` (line ~110) [L, secondary].

### Inferences
- Contemporaneous explanatory power is consistent with delta tracking the bar's direction by construction. A buy-dominated bar is usually an up bar. That relationship does not imply predictive power after the bar closes, so footprint signals need a strictly next-bar or later test.
- Continuation-type rules (stacked imbalance in the move's direction) agree more with the user's own result, described in section 5, than fade-type rules (exhaustion, absorption, delta-divergence reversal).
- Given about 10 bp taker round-trip costs on Binance perps (0.05% per side), a 5m footprint rule needs an average gross move per trade well above 10 bp. No public evidence shows such rules reach that.

### Gaps
- No systematic out-of-sample test of stacked imbalance, unfinished-auction revisit, POC migration or delta divergence on crypto perps or CME futures was found. If one exists on SSRN or arXiv, it was not surfaced, and those domains were not fetched.
- No academic paper testing volume-profile or value-area levels was found. Treat "high-volume node = support/resistance" as unproven.

## 3. Freqtrade implementation (local repo, authoritative)

### Takeaway
Freqtrade (beta feature) builds a per-candle footprint from public trades:
- per-level bid and ask volume and counts;
- bar delta, plus min and max of intrabar cumulative delta;
- diagonal imbalance flags and stacked-imbalance start prices.

It runs in backtesting from `--dl-trades` data. For Binance this downloads data.binance.vision **aggTrades** and maps `is_buyer_maker` to side. The code has several quirks that matter for strategy design:
- imbalances are computed on trade **counts**, not volume;
- the diagonal compares neighbouring *traded* levels, not ticks;
- division by zero counts as an imbalance;
- `max_candles` truncates the footprint in a backtest;
- the docs mislabel bid and ask.

### Cited Findings
**Config keys**
- `exchange.use_public_trades: true` enables the feature. If it is set, an `orderflow` block is mandatory: "Orderflow is a required configuration key when using public trades." — `freqtrade/configuration/config_validation.py:408-411`; docs `docs/advanced-orderflow.md:14-23` [L].
- Schema at `freqtrade/config_schema/config_schema.py:906-949`:
  - required keys: `max_candles`, `scale`, `stacked_imbalance_range`, `imbalance_volume`, `imbalance_ratio`;
  - `cache_size` is optional, default 1500, min 1;
  - `max_candles` default 1500, min 1;
  - `scale` min 0.0;
  - `stacked_imbalance_range` min 0;
  - `imbalance_volume` min 0;
  - `imbalance_ratio` min 0.0.

  Docs example: `cache_size 1000, max_candles 1500, scale 0.5, stacked_imbalance_range 3, imbalance_volume 1, imbalance_ratio 3` — `docs/advanced-orderflow.md:27-45` [L].
- The exchange must support trade data, or startup fails: "Trade data not available for {name}. Can't use orderflow feature." — `freqtrade/exchange/exchange.py:931-936` [L].

**Columns produced**
- Columns added by `ORDERFLOW_ADDED_COLUMNS` (`freqtrade/constants.py:92-…`): `trades`, `orderflow`, `imbalances`, `stacked_imbalances_bid`, `stacked_imbalances_ask`, `max_delta`, `min_delta`, `bid`, `ask`, `delta`, `total_trades`. All are initialised to NaN. The first five hold Python objects (dicts or lists) — `freqtrade/data/converter/orderflow.py:19-36`; docs `docs/advanced-orderflow.md:60-75` [L].
- `orderflow` is a dict keyed by binned price. Each entry has `bid_amount`, `ask_amount`, `bid` (count), `ask` (count), `delta`, `total_volume`, `total_trades`. Price binning is `round(price/scale)*scale` — `orderflow.py:188-217`, line 205 [L].
- Bar-level values: `bid` is the sum of sell-side amounts and `ask` the sum of buy-side amounts, `delta = ask − bid`, and `total_trades = len(trades)`. `max_delta` and `min_delta` are the max and min of the **cumulative per-trade delta within the candle** (intrabar CVD extremes) — `orderflow.py:157-174` [L].
- `trades` stores every raw trade of the candle as a list of dicts (`timestamp`, `date`, `price`, `amount`, `side`, `id`, `cost`) — `orderflow.py:130-132`; docs `:126-138` [L].

**How imbalances are computed (verbatim logic, `orderflow.py:220-242`)**
- `bid = df.bid`, `ask = df.ask.shift(-1)` with the comment "compares bid and ask diagonally". So bid at level P is compared with ask at the next level above it in the index (P+1 bin).
  - `bid_imbalance[P] = bid[P]/ask[P+1] > imbalance_ratio`
  - `ask_imbalance[P] = ask[P+1]/bid[P] > imbalance_ratio`, stored at row P, not P+1.

  This is the standard Sierra/ATAS diagonal (ask at P vs bid at P−1), but the ask flag is labelled one level lower than most platforms would draw it.
- **`df.bid` and `df.ask` here are trade counts**, the 0/1 flags summed per level at lines 202-203 and 213. The volumes would be `bid_amount`/`ask_amount`. So the "ratio" compares the number of aggressive prints, not volume. For aggTrades, one print can be one lot or thousands of contracts. This differs from every vendor definition, which uses volume.
- The comparison is strict (`>`), so `imbalance_ratio: 3` means more than 300%. The docs call it a "difference", but it is a ratio (`docs/advanced-orderflow.md:34`).
- The volume filter is `total_volume < imbalance_volume`, applied to **level P's total volume only**, for both flags (lines 232-236).
- If one side is zero, `x/0 = inf > ratio`, so the flag is True whenever the level passes the volume filter. `0/0 = NaN` gives False. The last row's shifted ask is NaN, so the top level never flags.
- Rows only exist for price bins that had trades (`groupby("price")`, line 216). "Next level" therefore means the next *traded* bin, which may be several ticks away in thin or fast markets.

**Stacked imbalances (`orderflow.py:245-265`)**
- Counts consecutive True rows and returns the starting price of each window that reaches the length `stacked_imbalance_range`. A run longer than the range yields several overlapping start prices. For example, a 5-run with range 3 gives 3 entries. The result is a list of prices, not a count, so strategies have to derive a count or nearest price themselves. "Consecutive" means consecutive traded bins, as above.

**Aggressor-side inference**
- For Binance archive downloads, `side = np.where(is_buyer_maker, "sell", "buy")` ("Side is reversed intentionally based on ccxt parseTrade logic"). Buyer-is-maker means the taker sold, so the trade counts toward `bid`/`bid_amount` — `freqtrade/exchange/binance_public_data.py:337-375` [L].
- Spot and futures CSV schemas are handled separately; futures files have a header and no `is_best_match` — same file, lines 340-365. The source URL is `https://data.binance.vision/data/futures/um/daily/aggTrades/{SYMBOL}/{SYMBOL}-aggTrades-YYYY-MM-DD.zip` — lines 216-225 [L].
- Live and dry-run use ccxt `fetch_trades`, whose `side` field the converter matches with `str.contains("sell"/"buy")` — `orderflow.py:198-199` [L]. Trade-record columns are `DEFAULT_TRADES_COLUMNS = ["timestamp","id","type","side","price","amount","cost"]` — `constants.py:90` [L].

**Backtesting support**
- Yes. In non-live run modes, `DataProvider.trades()` loads trades from disk via `data_handler.trades_load(pair, trading_mode, timerange=…)` — `freqtrade/data/dataprovider.py:522-559`.
- `IStrategy._if_enabled_populate_trades` builds a timerange from the dataframe's first and last dates and calls `populate_dataframe_with_trades` — `freqtrade/strategy/interface.py:1790-1815` [L].
- Download command from the docs: `freqtrade download-data -p BTC/USDT:USDT --timerange 20230101- --trading-mode futures --timeframes 5m --dl-trades` — `docs/advanced-orderflow.md:47-56` [L].
- For Binance, `--dl-trades` uses the fast archive download unless `only_from_ccxt` is set, and falls back to the slower REST API on error. The code notes "Binance futures only allows fromId within the last 2 days" — `freqtrade/exchange/binance.py:415-440`; `binance_public_data.py:~330` [L].
- **`max_candles` truncation:** `start_date = dataframe.tail(max_candles).date.iat[0]`, and trades before it are discarded (`orderflow.py:105-109`). In a backtest the indicators are populated once over the whole timerange, so only the **last `max_candles` candles** get footprint data. All earlier rows stay NaN. A 2-year 5m backtest has about 210k candles, so `max_candles` must be at least that, which defeats the memory cap. Live mode uses the same key to size the trade fetch window — `exchange.py:3355-3372` [L].

**Stated and observed limitations**
- The docs say the feature is "currently in beta and may be subject to changes", is "not been tested with freqAI", and that combining the two is "out of scope" — `docs/advanced-orderflow.md:5-7` [L].
- The docs warn that raw trades data "is rather large" and causes "slow initial startup" and "increased memory usage" — `docs/advanced-orderflow.md:9-10` [L].
- Speed: the converter is a per-candle Python loop that builds dicts for every trade and level (`orderflow.py:116-174`). The cache (`cache_size`) only helps live re-runs, keyed by candle date (lines 121-128, 179).
- **Documentation errors:** `docs/advanced-orderflow.md:116-119` says `bid_amount` is "Total volume bought" and `bid` is "Number of buy orders". The code assigns *sell*-aggressor trades to bid (`orderflow.py:198-203`). The code follows the standard footprint convention and the docs have it backwards.

### Inferences
- To match vendor-style volume imbalances, a strategy should recompute imbalances itself from the `orderflow` dict using `bid_amount`/`ask_amount`, a proper tick grid with zero-filled missing levels, and its own zero-denominator rule. The built-in `imbalances` columns should not be used for this.
- POC per bar, value area, unfinished auction (nonzero `bid_amount` at the bar's top bin or `ask_amount` at the bottom bin), and exhaustion (thin volume at the extreme) are not built in. All of them are easy to derive from the `orderflow` dict in `populate_indicators`.
- For multi-year backtests, the native path is likely impractical in memory and speed. A cheaper route is to precompute per-candle features (delta, CVD extremes, POC, stacked counts, UA flags) offline from the aggTrades CSVs into a feather file, then merge them like the existing taker-volume pipeline (`user_data/scripts/fetch_binance_taker.py`).
- `scale` has to be set per pair. SUI trades around $1–5, so a bin of about 0.0001–0.001 makes sense. BTC needs about 1–10 USD. The docs default of 0.5 is BTC-ish and wrong for SUI. This is inferred from the rounding formula on line 205.

### Gaps
- Run-time and RAM figures for a real 2-year BTC backtest with orderflow enabled were not measured.
- I did not verify whether ccxt's live `fetch_trades` for Binance USDⓈ-M returns aggTrades or raw trades.

## 4. Data: Binance aggTrades caveats and size

### Takeaway
aggTrades carry price, quantity, first/last trade id, timestamp and `is_buyer_maker`, which is enough for per-level aggressor volume. Each record merges several fills, so trade counts and print sizes are distorted and imbalances based on counts are unreliable. There is no order-book data, so absorption and iceberg reads are guesses. About 2 years of USDⓈ-M aggTrades is about 13.8 GB (BTC) and 4.2 GB (SUI), compressed.

### Cited Findings
- Spot aggTrades: "trades that fill at the time, from the same taker order, with the same price will have the quantity aggregated". `m` = buyer was maker, `M` = best price match — [hexdocs mirror of Binance spot docs](https://hexdocs.pm/binance_spot_rest/BinanceSpotRest.Endpoints.MarketData.AggTrades.Query.html) [I-mirror, snippet].
- USDⓈ-M futures aggregate-trade stream: aggregates fills "with same price and taking side every 100 milliseconds" — [Binance futures docs, Aggregate Trade Streams](https://developers.binance.com/docs/derivatives/usds-margined-futures/websocket-market-streams/Aggregate-Trade-Streams) [I, snippet only; page not reachable]. Under this rule a futures aggTrade can merge fills from **different taker orders** within 100 ms. Whether the REST and archive aggTrades follow the stream rule or the spot "same taker order" rule was not verified.
- Archive schema: aggTrades have agg id, price, qty, first/last trade id, timestamp and `is_buyer_maker`. Raw `trades` archives have id, price, qty, quoteQty, time and isBuyerMaker. Kline archives include taker-buy base and quote volume, which is enough for bar-level delta without any trades data — [binance-public-data README](https://github.com/binance/binance-public-data/blob/master/README.md) [I], as summarised in `/home/user/freqtrade/research_notes/BTC SUI futures orderflow edges/data_and_freqtrade_feasibility.md:30-35` [L].
- Size, 24 monthly zips from 2024-11 to 2026-10, compressed:

  | Dataset | BTCUSDT | SUIUSDT |
  | --- | --- | --- |
  | aggTrades | 13.8 GB | 4.2 GB |
  | trades | 21.4 GB | 11.3 GB |

  Source: S3 listing size fields, [data.binance.vision S3 listing](https://s3-ap-northeast-1.amazonaws.com/data.binance.vision?list-type=2&prefix=data/futures/um/monthly/aggTrades/BTCUSDT/BTCUSDT-aggTrades-2025) via `research_notes/BTC SUI futures orderflow edges/data_and_freqtrade_feasibility.md:36-43` [I/L].
- Crypto books are thin and update slowly relative to established markets (Silantyev 2019) — [RePEc](https://ideas.repec.org/a/spr/digfin/v1y2019i1d10.1007_s42521-019-00007-w.html) [A, snippet]. Thin, slow-updating books are the reason an aggressor print alone says little about how much passive liquidity absorbed it.

### Inferences
- **Volume per level and delta are exact** under aggregation, because quantities sum and each aggTrade has a single taker side. **Counts are not exact.** `total_trades`, the per-level `bid`/`ask` counts, and therefore Freqtrade's built-in imbalance flags (section 3) depend on the aggregation rule. The `last_trade_id − first_trade_id + 1` span recovers the underlying fill count, but Freqtrade drops those columns.
- With no order-book context, "absorption" can only be approximated, for example as high volume at a level with little price progress. Hidden or iceberg liquidity and pulled or stacked orders are invisible.
- Liquidations print as ordinary taker trades in aggTrades and cannot be told apart without a separate liquidation feed.
- Uncompressed CSV is typically several times larger than the zip. Holding BTC's raw trades in a pandas DataFrame plus a per-candle list of dicts for two years is likely tens of GB of RAM. That points to precomputing features offline.

### Gaps
- No verified per-day aggTrade record counts or uncompressed sizes for SUI and BTC.
- The official REST/archive aggregation rule for USDⓈ-M futures was not read from the primary page because the domain was blocked.

## 5. Tie-in with the user's own Freqtrade evidence

### Takeaway
The user's pre-registered FlushReversal test found that fading 15-minute moves made by one-sided taker flow lost money in every cell. Same-size moves *without* dominant taker flow did better in all four out-of-sample columns. That points to one-sided aggressor flow on Binance perps marking continuation. Footprint fade setups (exhaustion, absorption, delta-divergence reversals) are a finer-grained version of the same bet. Continuation readings (stacked imbalances in the move's direction) are the side the user's evidence supports, though that support is indirect.

### Cited Findings
- Design window 2023-05 to 2024-12, BTC and SUI 5m: none of the 48 pair-half-year-cell results reached PF 1.0, and the best was 0.97. Win rates were 45–63%, but losers outweighed winners after about 10 bp of fees. Deeper limit entries were worse in every column — `/home/user/freqtrade/user_data/NOTES.md:1098-1131` [L].
- Out of sample 2025 to 2026-10, PF (trades), selected cell vs low-flow control:

  | Pair, period | Selected cell | Low-flow control |
  | --- | --- | --- |
  | SUI 2025 | 0.74 (154) | 0.77 (79) |
  | SUI 2026 | 0.86 (127) | 1.29 (47) |
  | BTC 2025 | 0.59 (132) | 0.70 (29) |
  | BTC 2026 | 0.54 (147) | 0.93 (23) |

  The fill-through and fee-stress variants were lower still. The notes conclude: "conditioning on one-sided taker flow selects moves that are more likely to *continue*, not reverse", which matches Osler's stop-cascade finding better than the liquidity-premium reading. The control samples are too thin to trade — `/home/user/freqtrade/user_data/NOTES.md:1133-1163` [L].
- That test used **kline taker-buy volume** (bar-level delta), not per-level footprints — `/home/user/freqtrade/user_data/NOTES.md:1041-1045` [L].

### Inferences
- A footprint test would add per-level information that the user has not yet tested: where in the bar the aggression occurred, stacks, and unfinished extremes. The bar-level delta component is already shown to be a continuation marker rather than a fade trigger at 5m/15m.
- A reasonable first footprint hypothesis that respects this evidence is continuation, not fade. For example: a stacked ask imbalance (computed on volume, with diagonal zero-filled levels) in the top third of a breakout bar, with entry on a retest of the stack. It should be pre-registered with the same control design (same-size moves without stacks) and taker-fee stress.

### Gaps
- No footprint-level (per-price) test has yet been run on the user's data, so whether per-level structure adds anything beyond bar-level delta is unknown.
