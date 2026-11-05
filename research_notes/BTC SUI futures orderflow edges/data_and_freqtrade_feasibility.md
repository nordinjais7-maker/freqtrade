# Data sources and Freqtrade feasibility for order-flow and positioning strategies on BTC and SUI USDT-M perps

Research date: 2026-11-02. The local Freqtrade repo is at version `2026.10`, commit a2e8850, dated 2026-11-02 (`/home/user/freqtrade/freqtrade/__init__.py`).

Network limits in this session: developers.binance.com, docs.tardis.dev, tardis.dev, public.bybit.com, quote-saver.bycsi.com and okx.com could not be fetched directly. They resolved to nothing or were refused by the proxy. Claims about those sites come from search-result snippets and are marked as such. To verify them directly, those hosts have to be allowed in the session's network settings. The Binance public-data bucket was reachable through its S3 endpoint (`https://s3-ap-northeast-1.amazonaws.com/data.binance.vision`). The bucket listings below were queried live on 2026-11-02.

## Q1. Free exchange archives: Binance (data.binance.vision), OKX and Bybit. Which datasets exist, from when, at what granularity, and is SUIUSDT covered?

### Takeaway
Binance's free archive covers almost everything except liquidations and full L2 depth for USDT-M futures. It has tick trades and aggTrades, 1s-to-1M klines, mark, index and premium klines, monthly funding, 5-minute OI and long/short "metrics", and 30-second aggregated "bookDepth" (cumulative depth at ±0.2/1/2/3/4/5% from mid). SUIUSDT is covered from 2023-05-03 for all of these. bookTicker (top of book) stops at the end of March/April 2024. There is no USDT-M liquidationSnapshot dataset (COIN-M only, ending in 2024-10). Bybit publishes free trades and order-book (L2 snapshot plus delta) archives. Its 500-level depth reportedly ended around 2025-09. I could not verify the OKX archive.

### Cited Findings
**Binance data.binance.vision, USDT-M (`data/futures/um/`). Live bucket listing on 2026-11-02:**
- The `daily/` prefixes are aggTrades, bookDepth, bookTicker, indexPriceKlines, klines, markPriceKlines, metrics, premiumIndexKlines and trades. The `monthly/` prefixes are aggTrades, bookTicker, fundingRate, indexPriceKlines, klines, markPriceKlines, premiumIndexKlines and trades. **There is no `liquidationSnapshot` under `um`.** Source: [S3 listing, daily](https://s3-ap-northeast-1.amazonaws.com/data.binance.vision?delimiter=/&prefix=data/futures/um/daily/); [S3 listing, monthly](https://s3-ap-northeast-1.amazonaws.com/data.binance.vision?delimiter=/&prefix=data/futures/um/monthly/)
- First daily files found:
  - BTCUSDT: trades 2019-09-08, aggTrades 2019-12-31, metrics 2020-09-01, bookDepth 2023-01-01, bookTicker 2023-05-16.
  - SUIUSDT: trades, aggTrades, metrics and bookDepth all from 2023-05-03; bookTicker from 2023-05-16.

  Source: [S3 listing](https://s3-ap-northeast-1.amazonaws.com/data.binance.vision?prefix=data/futures/um/daily/metrics/SUIUSDT/&max-keys=1). Other keys were queried the same way.
- Latest files found on 2026-11-02:
  - Trades, aggTrades and metrics run to 2026-11-01 for BTC and 2026-10-31 to 2026-11-01 for SUI.
  - bookDepth runs to 2026-10-31 for both.

  So the lag is about 1 to 2 days. Source: [S3 listing](https://s3-ap-northeast-1.amazonaws.com/data.binance.vision?list-type=2&prefix=data/futures/um/daily/bookDepth/SUIUSDT/SUIUSDT-bookDepth-2026-1)
- **bookTicker is discontinued.** The last daily BTCUSDT file is 2024-03-30, and the last monthly file is 2024-04. Source: [S3 listing](https://s3-ap-northeast-1.amazonaws.com/data.binance.vision?list-type=2&prefix=data/futures/um/monthly/bookTicker/BTCUSDT/)
- **The liquidationSnapshot dataset exists only for COIN-M** (`data/futures/cm/daily/liquidationSnapshot/`). BTCUSD_PERP files run from 2023-06-25 to 2024-10-14, so it is also stale. Source: [S3 listing](https://s3-ap-northeast-1.amazonaws.com/data.binance.vision?list-type=2&prefix=data/futures/cm/daily/liquidationSnapshot/BTCUSD_PERP/)
- The fundingRate monthly files for SUIUSDT run from 2023-05 to 2026-10. Source: [S3 listing](https://s3-ap-northeast-1.amazonaws.com/data.binance.vision?list-type=2&prefix=data/futures/um/monthly/fundingRate/SUIUSDT/)
- **metrics file format.** I inspected SUIUSDT-metrics-2026-10-01. It has 288 rows per day, which is 5-minute granularity, and these columns: `create_time, symbol, sum_open_interest, sum_open_interest_value, count_toptrader_long_short_ratio, sum_toptrader_long_short_ratio, count_long_short_ratio, sum_taker_long_short_vol_ratio`. Rows were not sorted by time in the file. Source: [file](https://s3-ap-northeast-1.amazonaws.com/data.binance.vision/data/futures/um/daily/metrics/SUIUSDT/SUIUSDT-metrics-2026-10-01.zip)
- **bookDepth file format.** I inspected SUIUSDT-bookDepth-2026-10-01. It has columns `timestamp, percentage, depth, notional`. The percentage levels are ±0.20, ±1, ±2, ±3, ±4 and ±5. Snapshots come roughly every 30 seconds (00:00:01, 00:00:32, 00:01:00, ...), giving 34,560 rows per day. This is cumulative depth within a percentage band, **not price-level L2**. Source: [file](https://s3-ap-northeast-1.amazonaws.com/data.binance.vision/data/futures/um/daily/bookDepth/SUIUSDT/SUIUSDT-bookDepth-2026-10-01.zip)
- **Column schemas from the official README:**
  - aggTrades: agg id, price, qty, first/last trade id, timestamp, `is_buyer_maker`.
  - trades: id, price, qty, quoteQty, time, isBuyerMaker.
  - klines include "Taker buy base asset volume" and "Taker buy quote asset volume", which makes bar-level delta possible from klines alone.

  Daily data is published the next day. Monthly data is published on the first Monday of the month. Source: [binance-public-data README](https://github.com/binance/binance-public-data/blob/master/README.md)
- **Size over 24 monthly zip files, 2024-11 to 2026-10:**

  | Dataset | BTCUSDT | SUIUSDT |
  | --- | --- | --- |
  | aggTrades | 13.8 GB | 4.2 GB |
  | trades | 21.4 GB | 11.3 GB |

  All sizes are compressed. Source: S3 listing size fields, e.g. [BTC aggTrades monthly](https://s3-ap-northeast-1.amazonaws.com/data.binance.vision?list-type=2&prefix=data/futures/um/monthly/aggTrades/BTCUSDT/BTCUSDT-aggTrades-2025)

**Bybit (search snippets only; not fetched directly):**
- Bybit's derivatives "history-data" page is the official source of free historical order-book files. The REST API only returns the current book. Source: [KatanaQuant blog](https://blog.katanaquant.com/p/scraping-historical-orderbook-data)
- The files are snapshot plus delta records, up to 200 or 500 levels per side, served from quote-saver.bycsi.com. Trades are at public.bybit.com. Source: [Anton495/bybit-data-downloader](https://github.com/Anton495/bybit-data-downloader); [bybit-history PyPI](https://pypi.org/project/bybit-history/)
- One project says Level-500 contract order-book data is available from 2024-01-01. Tardis says Bybit's orderbook.500 feed ran from 2023-04-05 until 2025-09-05, which suggests 500-level depth was retired. Source: [gptcompany/bybit_historical_data_download](https://github.com/gptcompany/bybit_historical_data_download); [Tardis Bybit docs (search snippet)](https://docs.tardis.dev/historical-data-details/bybit)
- Freqtrade docs say Bybit has full open-interest history through the API, unlike Binance. Source: `/home/user/freqtrade/docs/data-download.md` (lines ~104-107)

**OKX:**
- The OKX REST order book returns only a current snapshot, capped at 400 levels (or 1/5/400/4000 depending on channel). Trade history is paginated; one source says it covers "several months" and another says "full", which conflict. Source: [dccd OKX docs](https://download-crypto-currencies-data.readthedocs.io/en/latest/_modules/dccd/sources/okx.html)

### Inferences
- Several strategy families can be backtested for free on Binance for both symbols, from mid-2023 for SUI:
  - OHLCV sweeps.
  - CVD/delta, from aggTrades, or bar-level delta from klines' taker-buy volume.
  - OI and long/short positioning at 5-minute resolution.
  - Funding.
  - Coarse book-depth imbalance at ±0.2% to ±5% and 30-second cadence.
- Free Binance data cannot reconstruct the true L2 queue, iceberg refills or absorption at specific price levels. There has been no top-of-book quote history since 2024-04, so spreads can't be backtested from Binance for 2024-05 onward.
- No free Binance USDT-M liquidation history exists. Liquidation signals need Coinglass, Tardis or other vendors, or self-recording the forceOrder stream going forward. Self-recorded data would still be throttled; see Q4.

### Gaps
- I could not fetch Bybit's or OKX's official historical-data pages. The exact date ranges for SUIUSDT on Bybit and OKX are unverified.
- I did not verify whether the bookDepth sampling cadence varies over time; only one day was sampled.

## Q2. Commercial sources: Tardis.dev, Coinglass, Kaiko, Amberdata, CoinAPI. What do they cover and roughly what would BTC + SUI over 2 years cost?

### Takeaway
Tardis is the realistic tick-level L2, trades and liquidations source for a retail trader. The "Solo" perpetuals plan reportedly costs about $700/month, and history depth depends on billing period, with up to 4 years on yearly billing. Coinglass is the cheap source of aggregated liquidation, OI and long/short history ($29 to $79/month for personal tiers), but its history depth on cheap tiers is limited. I found no reliable public pricing for Kaiko, Amberdata or CoinAPI; they are enterprise and quote-based.

### Cited Findings
**Tardis.dev:**
- Plans reportedly cost about $700/month for Solo, $1,000 for Professional and $3,000 for Business. Solo covers all perpetual swaps (Binance Futures, OKX Swap, Bybit Derivatives, Hyperliquid and others). These figures come from a garbled pricing-page snippet plus a third-party comparison, and need confirming. Source: [tardis.dev](https://tardis.dev/); [aperiodic.io comparison](https://aperiodic.io/compare/aperiodic-vs-tardis); [GitHub PR summarizing pricing, ~March 2026](https://github.com/qOeOp/trade/pull/1809)
- History depth depends on billing interval: 4 months for monthly billing, 12 months for quarterly, 4 years for yearly. There are no per-instrument or date-range purchases. This is a secondary source. Source: [GitHub PR #1809](https://github.com/qOeOp/trade/pull/1809)
- Solo and Academic plans include CSV downloads only. Pro and Business add the raw replay API and tardis-machine. Source: [Tardis billing FAQ](https://docs.tardis.dev/faq/billing-and-subscriptions)
- Data for the first day of each month is free for every exchange and data type, as CSV or replay, without an API key. Source: [Tardis FAQ (search snippet)](https://docs.tardis.dev/faq/data)
- Tardis offers tick-by-tick order book snapshots and updates, trades, open interest, funding and liquidations. Liquidations come from exchange-native feeds, e.g. Binance forceOrder. Source: [tardis.dev](https://tardis.dev/); [tardis-machine data types](https://docs.tardis.dev/tardis-machine/data-types)

**Coinglass API:**
- Hobbyist costs $29/month, with 70+ endpoints and 30 requests/min. Startup costs $79/month, with 80+ (or 130+) endpoints and 80 requests/min. Both are personal-use only. Standard, at $299/month, is the first commercial tier. Prices were reportedly cut on 2026-06-28 from $35 and $95. Source: [ComparEdge](https://comparedge.com/tools/coinglass); [GitHub listing](https://github.com/jrxmnq629/CoinGlass)
- History depth on Hobbyist is reportedly about 6 to 90 days for short intervals. Startup and above offer about 180 to 720 days of hourly history. This is a secondary source. Source: [ComparEdge](https://comparedge.com/tools/coinglass)
- Endpoints include pair-level `/api/futures/liquidation/history`, `/api/futures/liquidation/aggregated-history`, and a liquidation WebSocket. Source: [coinglass-go](https://pkg.go.dev/github.com/tigusigalpa/coinglass-go)

**Others:**
- Amberdata has documented futures-liquidations and long/short-ratio endpoints, but I found no pricing. Source: [Amberdata liquidations](https://docs.amberdata.io/reference/futures-liquidations-historical); [Amberdata long/short](https://docs.amberdata.io/data-dictionary/market/longshort-ratio.md)
- Coin Metrics notes that Binance's forceOrder throttling, which dates from April 2021, makes scraped liquidation data incomplete. Source: [Coin Metrics liquidations docs](https://gitbook-docs.coinmetrics.io/market-data/market-data-overview/liquidations/futures-liquidations)

### Inferences
- **Two-year BTC + SUI cost estimate:**
  - Tardis Solo, yearly billing (needed for more than 12 months of history): roughly $700 × 12 ≈ $8,400/year. One month on monthly billing ($700) only reaches about 4 months back.
  - Coinglass Startup: about $79/month (about $948/year). It covers aggregated liquidations and positioning, but probably not 2 years at intraday resolution.
  - These are inferences from the reported plan prices, not quotes.
- Tardis Binance liquidation history inherits Binance's 1-second throttling, so it is a lower bound on true liquidations. It is not a complete record.

### Gaps
- I could not open the official Tardis pricing page or the Binance-futures coverage page. The exact start dates for Binance-futures `incremental_book_L2`, `book_snapshot_25` and `liquidations` are unverified. My training-era knowledge suggests 2019-11 to 2020 for book data and 2021 for liquidations.
- I found no public prices for Kaiko, Amberdata or CoinAPI. They are presumed enterprise and quote-based.
- I did not verify Coinglass history depth per endpoint and tier from an official source.

## Q3. Freqtrade capabilities: orderflow/public trades, data download, backtesting, order book, and live latency

### Takeaway
Freqtrade (2026.10) can backtest and run trade-based orderflow per candle. This covers footprint per price bin, bid/ask volume, delta, min/max intra-candle delta, trade count, imbalances and stacked imbalances. On Binance futures it downloads the trades data from data.binance.vision aggTrades. Since 2026, Freqtrade can also download open interest (Binance: last 30 days only) plus funding and mark candles. **Freqtrade does not store or backtest order-book data.** `dp.orderbook()` returns live data only. The bot's main loop defaults to 5 seconds and trades are refreshed via REST per candle, so sub-second reaction is out of reach.

### Cited Findings
- **Orderflow setup and status:**
  - Orderflow is enabled with `"exchange": {"use_public_trades": true}` plus an `orderflow` config block (`cache_size`, `max_candles`, `scale`, `stacked_imbalance_range`, `imbalance_volume`, `imbalance_ratio`).
  - The feature is marked **beta**, has not been tested with FreqAI, and needs large raw trade data, so startup is slow and memory use increases.
  - It adds the columns `trades, orderflow (footprint dict), imbalances, bid, ask, delta, min_delta, max_delta, total_trades, stacked_imbalances_bid, stacked_imbalances_ask`. CVD is computed by the user as `delta.cumsum()`.

  Source: `/home/user/freqtrade/docs/advanced-orderflow.md`; [freqtrade.io advanced-orderflow](https://www.freqtrade.io/en/latest/advanced-orderflow)
- **Backtest data download.** The command is `freqtrade download-data -p BTC/USDT:USDT --trading-mode futures --timeframes 5m --dl-trades`. Not all exchanges provide public trades. Source: `/home/user/freqtrade/docs/advanced-orderflow.md`
- **Binance trades come from the archive.** On Binance, `--dl-trades` fetches daily aggTrades zips from data.binance.vision (`data/futures/um/daily/aggTrades/...`) and falls back to the REST API on error. Source: `/home/user/freqtrade/freqtrade/exchange/binance_public_data.py` (lines 216-225, 304-335); `/home/user/freqtrade/freqtrade/exchange/binance.py` (~line 440)
- **Orderflow is computed in the strategy, from stored trades, in both live and backtest.** `_if_enabled_populate_trades` loads `dp.trades(pair, timerange)` and calls `populate_dataframe_with_trades`. In live mode, trades are refreshed via `refresh_latest_trades` in the dataprovider. Source: `/home/user/freqtrade/freqtrade/strategy/interface.py` (lines ~1790-1815); `/home/user/freqtrade/freqtrade/data/converter/orderflow.py`; `/home/user/freqtrade/freqtrade/data/dataprovider.py` (lines 476-483); `/home/user/freqtrade/freqtrade/exchange/exchange.py` (lines 3485-3530)
- **Version history.** The public-trades/orderflow work came from PR #9066, with commits from February 2024. My memory is that it shipped around release 2024.7; I did not verify this against the changelog. Source: [PR #9066](https://github.com/freqtrade/freqtrade/pull/9066). The local clone's history is shallow, so I could not see the first-introduction commit.
- **Trades data format and warning.** Trades are stored as `<pair>-trades.feather`, and incremental download is supported. The general docs warn "Do not use [dl-trades] unless you're a kraken user" for OHLCV-building purposes. That warning is about speed, not orderflow. Source: `/home/user/freqtrade/docs/data-download.md` (lines ~289-311)
- **Futures candle types.** Futures downloads automatically include `mark` and `funding_rate` candles. **Open interest** has to be requested with `--candle-types open_interest` and gives `open_interest_amount` and `open_interest_value`. "Binance … only serves the last 30 days, while Bybit has the full history available. Downloads reaching further back will silently return no data." Source: `/home/user/freqtrade/docs/data-download.md` (lines 63-107)
- Freqtrade has **no download path for Binance `metrics` (OI and long/short ratios), `bookDepth`, long/short ratios or liquidations.** The binance_public_data module only builds klines and aggTrades URLs. Source: `/home/user/freqtrade/freqtrade/exchange/binance_public_data.py` (lines 187-225)
- **Order book is live-only.** `dp.orderbook(pair, maximum)` returns the live book. "The order book is not part of the historic data which means backtesting and hyperopt will not work correctly if this method is used." Source: `/home/user/freqtrade/docs/strategy-customization.md` (lines 882-914)
- **Latency settings:**
  - The default `internals.process_throttle_secs` is 5 seconds, the minimum loop duration. Source: `/home/user/freqtrade/freqtrade/constants.py` (line 17); `/home/user/freqtrade/docs/configuration.md` (line 272)
  - On Binance futures, Freqtrade uses websockets for the order book but **not for OHLCV** (`"ws_enabled": {"ohlcv": False, "orderbook": True}`), and the futures OHLCV REST limit is 499 candles. Source: `/home/user/freqtrade/freqtrade/exchange/binance.py` (lines 55-73)
  - Binance futures requires using the order book for pricing, because there is no ticker price for futures. Source: `/home/user/freqtrade/docs/exchanges.md` (line 108)

### Inferences
- The following strategy families are testable in Freqtrade:
  - OHLCV sweeps: yes.
  - CVD, delta and footprint imbalances at candle resolution: yes. Backtest from data.binance.vision aggTrades; for SUI that is about 4 GB zipped over 2 years, and much larger in memory.
  - OI and funding signals: only via mark/funding/OI candles. OI goes back just 30 days on Binance through the API. For longer history, load Binance `metrics` CSVs yourself, e.g. via `informative` data merged in `populate_indicators`.
  - L2 book imbalance, iceberg and absorption: **not backtestable in Freqtrade.** At best, a coarse ±% depth signal from `bookDepth` can be merged as an external feature.
  - Liquidation maps: not available natively.
- All signals are evaluated at candle close and the loop runs every 5 seconds by default. Effective reaction time is seconds-to-a-candle, plus REST order placement. Freqtrade fits strategies on 1m+ bars and is unsuitable for sub-second sweep-reclaim, absorption or iceberg reaction. Those need a custom websocket engine.
- Backtests of orderflow fill at candle open/close prices with configured fees. They do not simulate queue position or spread, which matters most for SUI.

### Gaps
- I did not benchmark backtest runtime or memory for 2 years of aggTrades. The docs only warn qualitatively.
- I did not measure the real order round-trip latency from a retail VPS to Binance futures.

## Q4. Live data: Binance futures websocket streams and REST history endpoints

### Takeaway
The liquidation stream is a throttled snapshot. It pushes only the latest liquidation per symbol per 1000 ms, so self-recorded liquidations undercount. The REST OI and long/short history endpoints only reach back about 30 days, which matches Freqtrade's docs. The archived 5-minute `metrics` files are the way to get longer positioning history.

### Cited Findings
- `<symbol>@forceOrder` and `!forceOrder@arr` update every 1000 ms. They report only the latest liquidation per symbol in each window, and nothing is pushed if no liquidation occurred. Source: [Binance USDⓈ-M Liquidation Order Streams (search snippet)](https://developers.binance.com/docs/derivatives/usds-margined-futures/websocket-market-streams/Liquidation-Order-Streams); [All Market Liquidation Streams](https://developers.binance.com/docs/derivatives/usds-margined-futures/websocket-market-streams/All-Market-Liquidation-Order-Streams)
- Coin Metrics says that since the April 2021 change, scrapers miss liquidations. They now sum quantity per interval instead. Source: [Coin Metrics](https://gitbook-docs.coinmetrics.io/market-data/market-data-overview/liquidations/futures-liquidations)
- Binance OI history is limited to the last 30 days. Source: `/home/user/freqtrade/docs/data-download.md` (lines 104-107). The long/short ratio endpoints use periods "5m" through "1d". Source: [Binance Long-Short Ratio doc (COIN-M, search snippet)](https://developers.binance.com/docs/zh-CN/derivatives/coin-margined-futures/market-data/Long-Short-Ratio)
- Freqtrade's Binance futures configuration uses a websocket order book of depth 100. Its allowed L2 limit range is `[5, 10, 20, 50, 100, 500, 1000]`. Source: `/home/user/freqtrade/freqtrade/exchange/binance.py` (lines 45-48)

### Inferences
- A forward-recording pipeline outside Freqtrade can capture full depth and liquidation snapshots for future backtests. It would record aggTrade, `depth@100ms` and `forceOrder`, but liquidation counts will remain a lower bound.

### Gaps
- I could not fetch the official docs for `openInterestHist`, `topLongShortAccountRatio`, `globalLongShortAccountRatio` and `takerlongshortRatio`, so I could not quote their exact "latest 30 days" wording or rate limits.
- I did not verify the `depth` stream update speeds (250 ms / 500 ms / 100 ms) or `aggTrade` stream details against the official docs in this session.

## Q5. Fees, funding, spreads and slippage on Binance USDT-M perps (BTCUSDT vs SUIUSDT)

### Takeaway
At the retail base tier (VIP 0), Binance USDT-M fees are 0.02% maker and 0.05% taker, with a 10% discount when paying in BNB. A taker round trip therefore costs about 0.10%, before spread and slippage. Funding settles periodically; SUI's monthly funding files are available back to 2023-05. I found no sourced, current spread or slippage figures for SUIUSDT versus BTCUSDT.

### Cited Findings
- VIP 0 (under $15M 30-day volume) pays 0.02% maker and 0.05% taker on USDⓈ-M. Paying in BNB gives a 10% discount. One source (finantres) says 0.04% taker, which is an outlier and conflicts with the others. Source: [Finder](https://www.finder.com/cryptocurrency/trading/binance-futures-fees); [CryptoPotato](https://cryptopotato.com/binance-fees/); conflicting: [finantres](https://finantres.com/?p=201499). Official schedule: [Binance fee article](https://www.binance.com/en/support/articles/360033544231)
- Freqtrade downloads funding-rate and mark candles automatically in futures mode. Funding is stored as `date` and `funding_rate`. Source: `/home/user/freqtrade/docs/data-download.md` (lines 63-64)
- Binance publishes monthly fundingRate archives for SUIUSDT from 2023-05 through 2026-10. Source: [S3 listing](https://s3-ap-northeast-1.amazonaws.com/data.binance.vision?list-type=2&prefix=data/futures/um/monthly/fundingRate/SUIUSDT/)
- The bookDepth sample for SUIUSDT on 2026-10-01 00:00:01 showed about $344k notional within -0.2% and about $400k within +0.2%. This is a proxy for near-touch liquidity. Source: [file](https://s3-ap-northeast-1.amazonaws.com/data.binance.vision/data/futures/um/daily/bookDepth/SUIUSDT/SUIUSDT-bookDepth-2026-10-01.zip)

### Inferences
- **Fee hurdle.** A strategy using taker entries and exits needs a gross edge above about 0.10% per trade, or about 0.09% with BNB, plus slippage. This kills most small-target sweep/scalp ideas on SUI. Maker entries reduce the cost but add fill risk, which Freqtrade backtests cannot model.
- **SUI depth.** SUI has roughly $0.3-0.4M within ±0.2% of mid in this one sample. Market orders in the tens of thousands of dollars should be absorbed near the top. Spread is likely 1 tick, but this is unverified. BTCUSDT depth is far larger. Comparable bookDepth files exist for BTCUSDT and were not sampled here.

### Gaps
- I found no current, sourced typical-spread or slippage statistics for BTCUSDT or SUIUSDT. bookTicker history ended in 2024-04, so spreads after that would need Tardis quotes or self-recording.
- I could not fetch Binance's official current fee table or funding interval/cap specifics for SUIUSDT (e.g. whether it is 8h or 4h) in this session.
