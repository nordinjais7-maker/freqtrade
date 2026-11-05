# Intraday edges from liquidity sweeps / stop hunts and liquidation flushes / positioning crowding in crypto perps (BTC, SUI and mid-cap alts)

Method note: research was done with web search plus fetches. arxiv.org, papers.ssrn.com and newyorkfed.org could not be fetched from this session (DNS blocked by the session's network allowlist). Claims about those papers therefore come from search-engine abstracts and snippets, not full texts. Effect sizes marked "(snippet)" should be checked against the PDF before anyone relies on them. Evidence tiers used below:
- **[R]**: peer-reviewed, or a documented working paper with out-of-sample (OOS) tests.
- **[W]**: academic working paper or preprint, not peer-reviewed, OOS status unclear.
- **[V]**: exchange, vendor or industry source.
- **[P]**: practitioner, blog or marketing source.

Cost benchmark used throughout: a taker round trip costs about 0.10% (2 x 0.05%) and a maker round trip about 0.04%. Slippage and funding come on top of that, and both get much worse during cascades and on thin alt books.

## 1. Stop-loss clustering, round numbers, prior highs/lows and sessions: do sweeps reverse or continue?

### Takeaway
The mechanism is well documented in FX: take-profits cluster at round numbers, which gives bounces, and stops cluster just beyond them, which gives faster moves once the level is crossed. The FX evidence says a *crossing* tends to **continue for hours, not days**. A failed crossing is not shown to reverse. In crypto, prices cluster strongly at round numbers, but those numbers act only as *weak barriers*. No rigorous crypto study shows that fading a sweep of prior highs/lows has a positive expectancy after costs.

### Cited Findings
- **[R] Osler (2003), *Journal of Finance*, "Currency orders and exchange rate dynamics".** Uses one large dealing bank's order book. Take-profit orders cluster particularly strongly at round numbers. Stop-loss orders cluster strongly just *beyond* round numbers: stop-sells just below, stop-buys just above. Osler argues this explains two technical-analysis predictions: trends reverse at support/resistance (the take-profit cluster), and trends speed up after a level is crossed (the stop cluster). — [NY Fed SR125](https://www.newyorkfed.org/medialibrary/media/research/staff_reports/sr125.pdf); [EconPapers](https://econpapers.repec.org/RePEc:fip:fednsr:125)
- **[R] Data scale (secondary, unverified).** About 9,655 orders, Aug 1999 to Apr 2000. About 9.9% of take-profit value ended in ".00", versus 3.8% for stops and about 1% expected under a uniform spread. These figures come from a secondary summary and could not be checked against the PDF. — [SUFE summary](https://academicnewsletter.sufe.edu.cn/info/361290)
- **[R] Osler (2005), *Journal of International Money and Finance*, "Stop-loss orders and price cascades in currency markets" (NY Fed SR150, 2002).**
  - Exchange-rate trends are unusually rapid when rates reach levels where stops are documented to cluster.
  - The response to stop-loss orders is larger and longer-lasting than the response to take-profit orders, which are negative-feedback trading.
  - Most results are **statistically significant for hours, not days**.
  - Stops "propagate trends and are sometimes triggered in waves", which helps explain fat tails.
  - (snippet) — [EconPapers](https://econpapers.repec.org/RePEc:fip:fednsr:150); [conference draft](https://icmaif.soc.uoc.gr/Year/8conf/docs/Osler-Price%20Cascades-03-03.doc); [FRASER](https://fraser.stlouisfed.org/title/staff-reports-federal-reserve-bank-new-york-9235/stop-loss-orders-price-cascades-currency-markets-673381)
- **[R] Urquhart (2017), *Economics Letters* 159:145–148, "Price clustering in Bitcoin".** More than 10% of prices end in round digits. There is **no significant pattern in returns after round numbers**. — [ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/S0165176517303233); [IDEAS](https://ideas.repec.org/a/eee/ecolet/v159y2017icp145-148.html)
- **[R] "Strong clustering and weak barriers at round numbers in Bitcoin markets", *Research in International Business and Finance* vol. 90 (2026).**
  - Data: more than 7 years of 1-minute Binance data.
  - Prices cluster at round numbers far more than random price formation predicts.
  - Round numbers are **weak barriers**: price spends about equal time above and below them, and volatility barely changes nearby.
  - The authors read this as round numbers *attracting order flow* without constraining price.
  - (snippet) — [IDEAS](https://ideas.repec.org/a/eee/riibaf/v90y2026ics0275531926002217.html)
- **[R] "Psychological barriers in the cryptocurrency market", *Review of Behavioral Finance* 12(2).** Finds consistent signs of barriers for 4 of 6 coins (BTC, DASH, LTC, XRP). This is a daily-level study, not a trading test. — [Emerald](https://www.emerald.com/rbf/article/12/2/151/362730/Psychological-barriers-in-the-cryptocurrency)
- **[R] Shen, Urquhart & Wang (2022), *Financial Review* 57(2):319–344, "Bitcoin intraday time-series momentum".**
  - The first half-hour return positively predicts the last half-hour return, both in-sample and OOS.
  - The effect is strongest in high-volume and high-volatility sessions and during downturns.
  - The authors attribute it to liquidity provision, not late-informed trading.
  - Data are from spot venues (Bitfinex, Bitstamp, Coinbase, Kraken, CEX.IO), not perps.
  - — [Birmingham](https://research.birmingham.ac.uk/en/publications/bitcoin-intraday-time-series-momentum/); [PDF](https://reading-9.eprints-hosting.org/100181/3/21Sep2021Bitcoin%20Intraday%20Time-Series%20Momentum.R2.pdf)
- **[R] "Turn-of-the-candle effect in bitcoin returns" (PLOS-hosted).** Positive returns of about 0.58 bp per minute concentrate at the turn of 15-minute candles. That is far below a 0.10% taker round trip. — [PMC](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC10015199/)
- **[W] "The Quarter-Hour Effect: Periodic Algorithmic Trading and Return Predictability in Cryptocurrency Futures" (arXiv 2607.09426).** Reports OOS intraday-timing predictability on Binance perps. Cost treatment was not seen. — [arXiv](https://arxiv.org/html/2607.09426v2)

### Inferences
- Osler's mechanism predicts **continuation when stop clusters beyond a level are hit** (hours horizon) and **bounces at the round number itself** (take-profits). A sweep-fade (entering after the level breaks and expecting reversal) bets against the stop-cascade leg. The evidence that a cascade does not mean-revert within hours is consistent with the user's failed Asia-session sweep-fade.
- The crypto evidence (Urquhart 2017; RIBAF 2026) shows round numbers attract orders but don't hold price. That also argues against a systematic fade edge at obvious levels.
- No peer-reviewed study was found that tests "prior session high/low sweep then reverse" in crypto at all. The concept rests on the FX order-clustering mechanism plus practitioner lore.

### Gaps
- No full-text access to Osler's PDFs, so the exact bp magnitudes and hour-by-hour continuation profile were not extracted.
- No crypto paper was found that uses actual stop-order data. Crypto venues don't publish resting stop orders. Hyperliquid's public order flow could make that possible, but no such study was found.
- No academic test of Asia/London/NY session-range sweeps in crypto was found.

## 2. Liquidation cascades in crypto perps: mechanics, predictability, tradability of post-cascade reversal

### Takeaway
There is solid recent work on cascade *mechanics*: ADL, branching ratios, early-warning signals, and how liquidity recovers. There is good evidence that **flow-driven moves partially revert at 15-minute to multi-hour horizons**, concentrated in smaller and illiquid assets. However, no rigorous study was found that demonstrates a *tradable, after-cost* post-liquidation reversal strategy. The best-documented reversal edge (Kitron & Wengrowicz 2026) is small in AUC terms, and its cost treatment is unverified.

### Cited Findings
- **[W] Kitron & Wengrowicz (2026), "Short-horizon mean reversion in cryptocurrency markets: a matched cross-market measurement" (arXiv 2608.21888), independent preprint.**
  - At 15-minute horizons, reversal appears in **90% of 183 Binance pairs, versus 2.7% of 187 US stocks/ETFs**, under one OOS protocol.
  - Reversal concentrates after moves driven by aggressive *taker* flow (Binance kline taker-buy volume) and grows with flow intensity.
  - Order-book depth consumed by the move does *not* condition the effect. The authors read this as compensated liquidity provision.
  - Effect size is small: class-mean AUC gap of +0.031 as designed, and +0.011 (95% CI +0.008 to +0.014) under the most conservative accounting.
  - Cost modelling was not visible in the snippets.
  - — [arXiv](https://arxiv.org/pdf/2608.21888); [IDEAS](https://ideas.repec.org/p/arx/papers/2608.21888.html)
- **[R] Riksbank WP 413 / *Journal of Banking & Finance* (2022), "Trading volume and liquidity provision in cryptocurrency markets".** Short-term reversal returns are primarily concentrated in smaller, less liquid, more volatile assets. — [Riksbank PDF](https://www.riksbank.se/globalassets/media/rapporter/working-papers/2022/no.-413-trading-volume-and-liquidity-provision-in-cryptocurreny-markets.pdf); [ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/S0378426622001418)
- **[R] "Returns from liquidity provision in cryptocurrency markets", *Journal of Banking & Finance* (2025).** A related liquidity-provision-returns study. Details were not extracted. — [ScienceDirect](https://www.sciencedirect.com/science/article/pii/S0378426625000317)
- **[R] "Unravelling cross-sectional patterns in cryptocurrencies: a four-factor asset pricing model", *China Accounting and Finance Review* 27(4).** Reports that the reversal effect is **amplified by momentum-driven liquidation in leveraged trading**, especially on exchanges offering high-leverage perps. — [Emerald](https://www.emerald.com/cafr/article/27/4/493/1271913/Unravelling-cross-sectional-patterns-in)
- **[R/W] "Liquidation, Leverage and Optimal Margin in Bitcoin Futures Markets" (BitMEX data).**
  - Daily forced liquidations average **3.51% of outstanding futures** (1.89% for longs and shorts per snippet).
  - Shows liquidations are a large, recurring flow, not rare tail events.
  - — [ResearchGate](https://www.researchgate.net/publication/349159585_Liquidation_Leverage_and_Optimal_Margin_in_Bitcoin_Futures_Markets)
- **[W] arXiv 2607.27070, "Where does the criticality live? Early-warning signals are event-heterogeneous across seven crypto-perpetual liquidation cascades".**
  - Covers 7 BTC cascades from 2022 to 2025, using 1-minute price and 5-minute leverage/order-flow data.
  - Critical slowing down appears in price for 5 of 7 events but not in the 2 tariff-news shocks.
  - This implies two types: endogenous build-up versus exogenous shock. Only the first is even potentially forecastable.
  - — [arXiv](https://arxiv.org/pdf/2607.27070); [IDEAS](https://ideas.repec.org/p/arx/papers/2607.27070.html)
- **[W] arXiv 2608.03616, "Measuring the engine of a liquidation cascade".** Uses a transparent venue's on-chain fill log for the Oct 2025 crash. The branching ratio is **subcritical**, and **most forced selling occurred within ~30 minutes**. — [arXiv](https://arxiv.org/pdf/2608.03616)
- **[R] Lim (2026), *Journal of FinTech and Digital Assets*.** Studies Hyperliquid L2 liquidity recovery after the 10 Oct 2025 cascade and finds a two-regime recovery pattern. — [journal](https://journals.lincoln.ac.nz/index.php/JFDA/article/view/1395)
- **[W] Autodeleveraging studies.**
  - "Autodeleveraging: Impossibilities and Optimization" (arXiv 2512.01112) replays the Hyperliquid 10 Oct 2025 data. ADL closed about **$2.1bn of positions in 12 minutes** (34,983 executions). It also lists 12 Mar 2020 ("Black Thursday") and 19 May 2021 as prominent ADL days.
  - A follow-up, "Risk-Based Auto-Deleveraging" (arXiv 2603.15963), finds about $2.05bn realized ADL notional in three waves.
  - — [arXiv 2512.01112](https://arxiv.org/pdf/2512.01112); [arXiv 2603.15963](https://arxiv.org/pdf/2603.15963)
- **[V] BitMEX "State of Crypto Perpetual Swaps 2025", via CoinDesk.**
  - In the 10 Oct 2025 crash, ADL closed market makers' *hedged* shorts. Market makers were left long inventory and pulled liquidity, which slowed trading afterwards.
  - Total liquidations were about $19–20bn; sources differ.
  - — [CoinDesk](https://www.coindesk.com/markets/2026/01/08/october-s-crypto-crash-left-market-makers-stuffed-with-coins-slowing-trading-bitmex)
- **[V] Kaiko, one year after 10 Oct 2025.**
  - BTC perp open interest (in BTC terms) is still about 16% below its pre-event level, and USD spot depth is down 27%.
  - Leverage per dollar of liquidity is about 20% lower.
  - — [Bloomingbit summary](https://en.bloomingbit.io/feed/news/122496)
- **[R] "Bitcoin option expiration, gamma exposure, and intraday price reversals", *Finance Research Letters* (2026).** Finds a significant intraday reversal around Deribit expiries, stronger when dealers are short gamma (about $50m per year in wealth transfers). This is an example of a documented *forced-flow* reversal that is not about liquidations. — [ScienceDirect](https://www.sciencedirect.com/science/article/pii/S1544612326008688)

### Inferences
- The mechanism (forced taker flow, then partial reversal as liquidity providers are compensated) is supported. Kitron & Wengrowicz and the Riksbank paper both say the reversal premium is a **liquidity-provision premium**. Such a premium is naturally earned with *maker* fills, and a taker strategy (about 0.10% round trip plus wide cascade spreads) may be eaten by costs. A +0.011 AUC gap is a weak classifier.
- Cascades are fast. Arxiv 2608.03616 finds most forced selling within about 30 minutes, and ADL completed in about 12 minutes. A 5m/15m bar strategy entering after a liquidation candle closes may miss most of the reversal or catch the second wave. Exogenous-news cascades show no early warning (arXiv 2607.27070).
- After the largest cascades, market-maker withdrawal (BitMEX, Kaiko) means wider spreads and slippage for a while. That raises the cost of trading the rebound exactly when the signal fires.

### Gaps
- No peer-reviewed study was found that directly regresses forward 1h/4h/24h BTC-perp returns on liquidation volume (Binance/OKX/Bybit forceOrder data) with OOS and costs.
- No full-text access to the arXiv cascade papers, so post-event return paths were not extracted.
- No dedicated academic study of the 12 Mar 2020 BitMEX cascade was found in this session.

## 3. Funding rate, open interest and long/short ratios as short-horizon return predictors

### Takeaway
Funding is the best-studied of the three. Funding *arbitrage* (basis/carry) has documented high Sharpe ratios but a declining premium. Funding as a *directional* contrarian signal has only weak support:
- an exchange blog showing an 8-hour reversal edge that comes mainly from collecting funding;
- a 2025–26 working paper showing extreme negative funding reverses only on up-market days.

Open interest and long/short (account or top-trader) ratios have essentially **no rigorous published OOS evidence** of short-horizon return predictability.

### Cited Findings
- **[W→R] He, Manela, Ross & von Wachter, "Fundamentals of Perpetual Futures" (arXiv 2212.06888, v6 Aug 2024).**
  - Derives no-arbitrage perp prices.
  - The mean absolute deviation from the benchmark is about **60–90% per year** across coins.
  - The arbitrage strategy earns a **Sharpe of 1.8 for BTC perps under retail-level costs, and up to 3.5 for fee-free market makers** (v5 figures, snippet).
  - This is a basis/carry arbitrage (perp versus spot), not a directional signal.
  - — [arXiv](https://arxiv.org/abs/2212.06888v6); [IDEAS](https://ideas.repec.org/p/arx/papers/2212.06888.html)
- **[R] Schmeling, Schrimpf & Todorov (2023), BIS, "Crypto carry".** Cited via an arXiv survey: funding carry trades (short perp, long spot) have historically been very profitable, but the premium is not guaranteed and profitability has declined. — [arXiv 2510.14435 survey](https://arxiv.org/pdf/2510.14435)
- **[W] Shek, "Conditional Arbitrage Capacity: Evidence from Crypto Perpetual Funding Rates" (SSRN 7520320).**
  - Studies extreme *negative* funding in BTC/ETH/SOL across 274 events.
  - Such events reverse on up-market days and keep falling on down days, with a gap of about 3.6 points (bootstrap CI excludes zero).
  - The author frames this as limits to arbitrage. It is **conditional, not a simple contrarian rule**, and the condition (the day's direction) is not known ex ante.
  - (snippet) — [SSRN](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=7520320)
- **[W] Inan, "Predictability of Funding Rates" (SSRN 5576424).** Double-AR models forecast BTC funding on Binance/Bybit OOS better than no-change. This predicts *funding*, not returns. — [SSRN](https://papers.ssrn.com/sol3/Delivery.cfm/fe1e91db-33b4-40b5-9564-38425a2495fc-MECA.pdf?abstractid=5576424&mirid=1)
- **[V] BitMEX blog, "XBTUSD Funding Mean Reversion Strategy".**
  - Large positive funding predicts a negative *next 8-hour* return.
  - BitMEX itself states that **receiving funding for bucking the trend provides a significant majority of the strategy's returns**.
  - The sample is about 524 funding periods. The source is an exchange with a commercial interest.
  - — [BitMEX](https://www.bitmex.com/blog/xbtusd-funding-mean-reversion-strategy)
- **[W] arXiv 1912.03270, "BitMEX Funding Correlation with Bitcoin Exchange Rate" (2019).** Funding is heteroskedastic (GARCH), and Granger causality runs between funding and the BitMEX perp. Return-prediction results were not seen. — [arXiv](https://www.arxiv.org/abs/1912.03270)
- **[P] OI measurement caveat.** OI in coin terms moves with price. USD OI rising can be a price effect rather than new positions. — [Axel Adler](https://axeladlerjr.com/bitcoin-open-interest-funding-rate/); [Bloomingbit](https://en.bloomingbit.io/feed/news/119833)
- **[V/P] Long/short ratios.**
  - Searches found no academic test of Binance/OKX/Bybit account or top-trader long/short ratios as return predictors.
  - Market commentary reports them descriptively, e.g. Binance top-trader accounts 68.9% long on 2 Nov 2026.
  - Commentary notes these ratios describe only that exchange's account cohort, and they differ across Binance, OKX and Bybit.
  - — [blockchain.news](https://blockchain.news/news/20261102-price-prediction-price-btc-pinned-below-every-key-average-as); [CryptoRank](https://cryptorank.io/news/feed/c1303-bitcoin-futures-long-short-ratios-analysis)

### Inferences
- The robust money in funding is **carry/basis** (delta-neutral), not directional timing. Directional "fade extreme funding" returns are largely the funding payment itself, so they only exist if the position is held through funding timestamps at the extreme rate.
- Shek's result implies that a contrarian funding fade is **momentum-dependent**. Fading crowded positioning works when the market turns your way and fails in trend continuation. That is consistent with the user's failed 6h-low breakdown short filtered by long/short ratio: crowding filters don't carry an unconditional sign.
- Long/short ratios are cohort- and exchange-specific, retail-heavy, and in "accounts" units (not size). Without any published OOS validation, they should be treated as unvalidated features. The user's own OOS failure is the best evidence available.

### Gaps
- Ackerer, Hugonnier & Jermann ("Perpetual futures pricing") was not retrieved this session. It is pricing theory and likely has no short-horizon return tests.
- No peer-reviewed study of ΔOI → next-hour or next-day BTC perp return with OOS and costs was found.
- No study of Binance "top trader" position ratio predictability was found at all.

## 4. SUI and comparable newer, lower-liquidity alt perps

### Takeaway
**No academic or rigorous study specific to SUI perps was found.** The indirect evidence (reversal concentrated in small, illiquid coins; thin books amplifying cascades; alt OI exceeding BTC OI in Sept 2025) suggests larger flushes and stronger short-horizon reversal in alts. Higher costs and slippage there are equally likely to absorb it.

### Cited Findings
- **[R]** Short-term reversal profits are concentrated in smaller, less liquid, more volatile cryptos. — [Riksbank WP 413](https://www.riksbank.se/globalassets/media/rapporter/working-papers/2022/no.-413-trading-volume-and-liquidity-provision-in-cryptocurreny-markets.pdf)
- **[W]** 15-minute reversal is present in 90% of 183 Binance pairs, which spans many alts. Per-coin results (SUI) were not extracted. — [arXiv 2608.21888](https://arxiv.org/pdf/2608.21888)
- **[V/P]** Coinalyze data (Sept 2025): altcoin perp OI exceeded BTC perp OI for the first time since Dec 2024, driven by ZEC at $2.4bn. Commentary says thin books plus crowding turn small moves into fast cascades. — [Bloomingbit](https://en.bloomingbit.io/feed/news/119833); [KuCoin news](https://www.kucoin.com/news/flash/the-open-interest-of-altcoin-perpetual-contracts-has-surpassed-that-of-bitcoin-for-the-first-time-in-21-months)
- **[V] SUI OI snapshots (undated).**
  - About $178m total OI on one aggregator.
  - Binance about $78m (around 17% of the listed total), OKX about $22m.
  - Hyperliquid about $32m.
  - Snapshots conflict in time, so treat them as illustrative only.
  - — [Sharpe SUI](https://www.sharpe.ai/futures/sui); [Buildix](https://www.buildix.trade/hyperliquid/SUI); [Coinglass SUI funding](https://www.coinglass.com/FundingRate/SUI)
- **[P]** Undated news: Binance, OKX and Bybit SUI long/short ratios rose while funding was negative, with about $5m of liquidations in a day. This is descriptive only. — [Bitcoinist](https://bitcoinist.com/sui-attracts-significant-liquidity-influx/amp/)

### Inferences
- For SUI, an effective round-trip cost (taker fees plus spread plus impact during a flush) is likely well above BTC's 0.10%. Any reversal edge must be gross-large to survive. Maker-entry designs, such as resting bids below liquidation clusters, are the only way the liquidity-provision premium logic applies.
- SUI's history on Binance perps is short (listed 2023). Combined with regime shifts (e.g. after Oct 2025), this leaves too few independent cascade events for meaningful OOS testing. That is a statistical-power problem, not just a strategy problem.

### Gaps
- No SUI-specific study of retail share, crowding or liquidation size was found.
- Hypotheses that are testable with Binance/Bybit liquidation and OI data (via Kaiko or Coinglass APIs) remain untested in public literature.

## 5. Practitioner claims (ICT/SMC sweeps, Hyblock/Coinglass liquidation heatmaps) and independent tests

### Takeaway
Independent mechanical tests of SMC/ICT sweep rules find **high win rates but no statistically significant edge, and negative or sub-benchmark returns**. Trend-following pieces of SMC hold up better than sweep fades. No independent backtest of Hyblock or Coinglass heatmap signals was found. The vendors themselves describe heatmaps as models or estimates with no timing information.

### Cited Findings
- **[P, independent test] IndicatorEdge.**
  - About 660,005 OOS backtests across 903 assets: the liquidity-sweep signal had a high median win rate but beat buy-and-hold in only **8% of assets**.
  - A second study on 738 assets: the sweep rule won **71.9% of trades yet returned −7.4%**.
  - Trend-following SMC components fared better than sweep-reversal components.
  - These are vendor-run, but with disclosed scale. Cost assumptions were not verified.
  - — [IndicatorEdge backtest](https://indicatoredge.io/learn/smc-ict-strategy-backtest-evidence-win-rate); [IndicatorEdge SMC](https://indicatoredge.io/smart-money)
- **[P, independent test] StatOasis, "I Backtested ICT / Smart Money Concepts — What Survives".** Mechanical daily-bar sweep rules detect real patterns but carry **no statistically significant edge**. Intraday performance is "an open, unverified claim". — [StatOasis](https://statoasis.com/overfit/research/ict-backtest-what-survives)
- **[P, promotional] FXNX.** Claims 58.2% "directional follow-through". The methodology is unverifiable. — [FXNX](https://fxnx.com/en/blog/smart-money-concepts-work-backtest-evidence)
- **[V/P] Liquidation heatmaps.** Third-party guides call them "a model; says nothing about timing" and "an estimation tool, not a prediction engine". The only support for profitability is an anecdotal TradingView user. — [Buildix guide](https://www.buildix.trade/blog/crypto-liquidation-heatmap-guide-coinglass-alternative); [TradingView idea](https://www.tradingview.com/chart/BTCUSDT.P/8MSmiY1E-Liquidation-Level-Trading); [mmt.gg](https://mmt.gg/learn/hyperliquid-heatmaps)

### Inferences
- "High win rate, negative expectancy" is the signature of a fade with a small target and a stop beyond the swept extreme. Rare continuation days (Osler-style stop cascades) wipe out many small wins. Practitioners report the win rate; the expectancy after a 0.10% round trip is what matters.
- Survivorship and selection bias are pervasive in practitioner sources: hand-picked charts, no pre-registration, no OOS.

### Gaps
- No peer-reviewed test of ICT/SMC concepts exists to my knowledge or in search results.
- No disclosed-methodology backtest from Hyblock or Coinglass was found.

---

### Cross-cutting: per-signal verdict after realistic costs (taker ~0.10% round trip, maker ~0.04%, plus funding and slippage)

| Signal | Best evidence | Direction / horizon | Survives costs? |
|---|---|---|---|
| Sweep of round number / prior high-low, fade | Osler 2003/2005 [R]; Urquhart 2017 [R]; RIBAF 2026 [R]; StatOasis/IndicatorEdge [P] | FX: crossing stop clusters → continuation, significant for hours. Crypto: weak barriers, no post-round-number return pattern | **No documented edge**; independent tests negative |
| Breakout continuation through stop clusters | Osler 2005 [R] (FX only) | Continuation, hours | Unknown for crypto; no crypto OOS test found |
| Post-liquidation / flow-driven reversal | Kitron & Wengrowicz 2026 [W]; Riksbank 2022 [R]; CAFR [R] | Reversal at 15m to a few hours, stronger in illiquid alts | **Unproven**; small AUC, likely needs maker execution |
| Funding extreme, directional fade | BitMEX blog [V]; Shek [W] | 8h reversal mostly from collected funding; conditional on market direction | **Weak / conditional** |
| Funding/basis carry (delta-neutral) | He et al. 2024 [W]; Schmeling et al. 2023 [R] | Carry, multi-day | **Yes historically** (Sharpe 1.8 retail BTC), declining |
| ΔOI, long/short ratios | None rigorous | n/a | **No evidence** |

### Relation to the user's failed pre-registered Freqtrade tests (Binance futures 2023–2026)
- **Asia-session sweep fade failed.** This is consistent with Osler's finding that stop-triggered moves continue for hours. It also matches the weak-barrier result for BTC round numbers, and the independent SMC tests (high win rate, negative return).
- **Range breakouts failed.** Osler's continuation evidence is FX-only and decays within hours. Crypto 15-minute flow-driven moves mostly *revert* (Kitron & Wengrowicz). Both breakout and fade can therefore fail depending on horizon and whether the move was liquidity-driven. Nothing in the literature contradicts the failure.
- **6h-low breakdown short filtered by long/short ratio failed.** No literature validates long/short ratios. Shek's conditional-funding result implies crowding signals flip sign with market direction. Liquidation-driven down-moves tend to revert at short horizons, which works against a breakdown short.
- **Possible contradiction to check.** The 15-minute reversal after aggressive taker flow (arXiv 2608.21888) and the BTC intraday half-hour momentum result (Financial Review 2022, spot) are the only rigorous short-horizon effects found. Neither is a sweep or crowding rule, and neither has been shown net of perp taker fees.
