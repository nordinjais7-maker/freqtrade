# Trade slow trends, not footprints or hunts

No strategy is universally "best", but the evidence leaves a clear ranking for a retail trader on Binance USDT-M perpetuals in BTC and SUI. **The best-supported choice is a slow, daily-bar, volatility-sized trend-following rule on BTC.** Its realistic net Sharpe is about **0.5–1.0**, with maximum drawdowns of about **25–45%**. Its most reliable benefit is roughly halving buy-and-hold drawdowns, not beating buy-and-hold returns ([Howden & Andreev, SSRN 7115459](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=7115459); [arXiv 2602.11708](https://arxiv.org/pdf/2602.11708)). Delta-neutral funding carry has the strongest *historical* after-cost evidence, with a Sharpe of about 1.8 at retail costs in earlier samples ([He et al., arXiv 2212.06888](https://arxiv.org/abs/2212.06888v6)). Since then the premium has compressed toward cash yields: BTC funding averaged about **11% in 2024, 4.9% in 2025 and 2.2% in 2026 to August** ([FXStreet relaying Ethena](https://www.fxstreet.com/cryptocurrencies/news/ethena-looks-beyond-crypto-to-squeeze-yield-from-booming-equity-perpetuals-202608281313)). On those numbers, your pending carry test is likely to fail its 4%-a-year bar for BTC in both out-of-sample years.

Footprint charts add nothing proven. **No systematic out-of-sample, after-cost test of any footprint setup was found**, and your own FlushReversal result shows that one-sided aggressor flow on these perps marks continuation, which undercuts the fade-style footprint setups most courses teach. Order-flow and "liquidity hunt" methods are sold through affiliate commissions of up to 35% and prop-firm tie-ups. They are evidenced by payout screenshots, while complete-population studies find that **97% of Brazilian futures day traders who persisted more than 300 days lost money** ([Chague et al., SSRN 3423101](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3423101)).

Every intraday family you tested is now either measured to fail or untested. The next step is therefore a frozen, literature-specified daily trend rule, tested once on 2022–2026 BTC data against a volatility-targeted buy-and-hold control. The pass and fail rules are written out in the final section.

One caveat applies throughout. arxiv.org, ssrn.com, bis.org, atas.net, developers.binance.com and several other vendor and journal domains were unreachable from the research environment. **Most quantitative figures here come from search-engine snippets or abstracts, not from the papers' tables.** Check every number you intend to act on against the primary source.

## Footprint charts re-slice aggressor flow, and no one has shown the slices predict

A footprint chart splits each bar's traded volume by price level and by aggressor side. "Bid" volume is sellers hitting the bid, "ask" volume is buyers lifting the offer, and delta is ask minus bid ([LuxAlgo, Footprint Concepts](https://www.luxalgo.com/library/concept/footprint-concepts.md); [NinjaTrader](https://ninjatrader.com/futures/blogs/footprint-charts-guide/)). Nearly every named pattern is a threshold rule on that grid:

- **Diagonal imbalance.** Ask volume at one price is compared with bid volume one tick below, usually at a 300% ratio with a minimum-volume filter ([LuxAlgo, Bid/Ask Imbalance](https://www.luxalgo.com/library/concept/bid-ask-imbalance/); [Sierra Chart thread 6802](https://www.sierrachart.com/SupportBoard.php?ThreadID=6802)).
- **Stacked imbalance.** Three or more consecutive same-side imbalances, read as support or resistance on a retest ([The Right Trader](https://therighttrader.com/learn/volume-and-order-flow/stacked-imbalances)).
- **Point of control and value area.** The value area is about 70% of volume around the busiest price, although CQG itself uses both 70% and 68% ([CQG MPVA help](https://help.cqg.com/cqgic/25/Documents/marketprofilevalueareasmpva.htm); [CQG primer 2026](https://news.cqg.com/workspaces/2026/07/cqg-one-primer-volume-profile-study)).
- **Unfinished auctions.** Two-sided trade at a bar extreme.
- **Absorption, exhaustion and delta divergence** ([NexusFi Academy](https://nexusfi.com/a/strategies/advanced-footprint-chart-patterns)).

Vendors agree on the concepts but not the parameters. Even "exhaustion" has two incompatible definitions: thin volume at the extreme in one source, unusually large delta in another ([Delta Microstructure script](https://www.tradingview.com/script/WBhuasLl-Delta-Microstructure-Analysis)). Every threshold (ratio, minimum volume, stack length, bin size) is a free parameter, and each one raises the overfitting risk of any backtest.

The tested evidence is close to empty. The only performance figure found anywhere is a **48% win rate for single stacked imbalances, which the educator who reports it concedes is below breakeven after commissions**, with no dataset or method stated ([NexusFi Academy](https://nexusfi.com/a/strategies/advanced-footprint-chart-patterns)). ATAS, which sells footprint software, says unfinished-auction levels come with "no 100% guarantee" of a revisit and "can hardly be considered an independent instrument" ([ATAS](https://atas.net/volume-analysis/basics-of-volume-analysis/unfinished-auction-what-it-is-and-how-to-trade-it), snippet). No peer-reviewed test of value-area or volume-profile trading was found. Steidlmayer's books present Market Profile as a method, not a tested result ([Steidlmayer & Hawkins](https://dokumen.pub/steidlmayer-on-markets-trading-with-market-profiletm-2nbsped-0471215562.html)). The one vendor "10-year test" of volume-profile support covers Thai equities on daily bars. It found that 41% of touches broke the level by more than 3% within 10 days, and it gave no baseline to compare against ([Deepscope](https://deepscope.com/support-resistance-volume-profile/)).

The academic work that does exist is about mechanism, not prediction:

- Support and resistance levels coincide with peaks in limit-order depth. The authors argue technical rules "locate depth already in place" ([Kavajecz & Odders-White, RFS 2004](https://ideas.repec.org/a/oup/rfinst/v17y2004i4p1043-1071.html)).
- On BitMEX's BTC perpetual, signed trade-flow imbalance, which is what footprint delta measures, explains **contemporaneous** price changes ([Silantyev 2019](https://ideas.repec.org/a/spr/digfin/v1y2019i1d10.1007_s42521-019-00007-w.html)).

A buy-dominated bar is usually an up bar by construction. That says nothing about the next bar.

Your own data points in one direction. In the pre-registered FlushReversal test, fading 15-minute moves made by one-sided taker flow lost in every out-of-sample cell. Profit factors were 0.74 and 0.86 on SUI and 0.59 and 0.54 on BTC. Same-size moves *without* dominant flow did better in all four columns, at 0.77, 1.29, 0.70 and 0.93 (`/home/user/freqtrade/user_data/NOTES.md`, §4h). Exhaustion, absorption and delta-divergence fades are finer-grained versions of that losing bet. Stacked imbalances in the direction of the move are the continuation reading your evidence indirectly supports, but they remain untested. Costs set the hurdle: a 5m footprint rule paying about 10 bp per taker round trip needs an average gross move per trade well above that, and nothing public shows one.

## Freqtrade builds footprints from trade counts and silently truncates backtests

Freqtrade's orderflow feature is marked beta and is "not tested with freqAI" (`/home/user/freqtrade/docs/advanced-orderflow.md`). It is enabled with `exchange.use_public_trades: true`, which then requires an `orderflow` block with `max_candles`, `scale`, `stacked_imbalance_range`, `imbalance_volume` and `imbalance_ratio` (`freqtrade/config_schema/config_schema.py:906-949`; `freqtrade/configuration/config_validation.py:408-411`).

For backtests, `download-data --dl-trades` pulls Binance's data.binance.vision **aggTrades** archives. Side comes from `is_buyer_maker`: buyer-is-maker means the taker sold, so the trade is counted as bid (`freqtrade/exchange/binance_public_data.py:337-375`). Prices are binned as `round(price/scale)*scale`. Each candle gets:

- an `orderflow` dict per price bin with `bid_amount`, `ask_amount`, bid and ask trade counts, delta and totals;
- bar-level `bid`, `ask` and `delta = ask − bid`;
- `min_delta` and `max_delta`, which are the extremes of cumulative delta *within* the candle;
- `imbalances`, `stacked_imbalances_bid` and `stacked_imbalances_ask`;
- the raw trade list (`freqtrade/data/converter/orderflow.py:157-217`).

Several details matter for strategy design. Each is easy to miss, and each changes what a backtest is measuring.

| Behaviour (repo HEAD `dfc1ae1`) | Where | Consequence |
|---|---|---|
| Imbalance ratios use per-level trade **counts**, not volume | `orderflow.py:202-203, 213, 220-242` | Unlike every vendor definition. Binance aggTrades merge fills, so counts depend on the aggregation rule, not on size. |
| Diagonal compares bid at bin P with ask at the next *traded* bin above; the ask flag is stored at P, not P+1 | `orderflow.py:220-242` | Standard diagonal logic, but the label sits one level low. In fast or thin markets "next level" can be several ticks away, because empty bins have no rows. |
| One side zero gives `x/0 = inf`, so the level flags as an imbalance; `0/0` gives False; the top level never flags | same | One-sided levels always count as imbalances once they pass the volume filter. |
| Volume filter checks level P's total volume only; comparison is strict `>` | same | `imbalance_ratio: 3` means more than 300%. The docs call it a "difference". |
| Stacked output is a list of start prices; a run of 5 with range 3 yields 3 overlapping entries | `orderflow.py:245-265` | The strategy has to derive counts or nearest levels itself. |
| `max_candles` keeps only the last N candles of trades | `orderflow.py:105-109` | In a backtest, everything earlier stays NaN. Two years of 5m bars is about 210k candles, which defeats the memory cap. |
| Docs say `bid_amount` is "volume bought" | `docs/advanced-orderflow.md:116-119` | The docs are backwards. The code follows the standard convention, with bid meaning sell-aggressor. |
| Default `scale` 0.5 | docs example | A BTC-sized bin. It is wrong for SUI at $1–5, where 0.0001–0.001 fits. |

The data compounds the count problem. Binance documents that the USDT-M aggregate-trade stream merges fills "with same price and taking side every 100 milliseconds" ([Binance docs](https://developers.binance.com/docs/derivatives/usds-margined-futures/websocket-market-streams/Aggregate-Trade-Streams), snippet). Whether the archive follows the same rule was not verified. **Per-level volume and delta are exact under aggregation, but trade counts are not.** Freqtrade also drops the first and last trade ids that would let you recover true fill counts.

Two other limits apply:

- **No order book.** Absorption can only be approximated as high volume with little price progress. Icebergs and pulled or stacked orders are invisible.
- **Size.** Two years of USDT-M aggTrades is about **13.8 GB for BTC and 4.2 GB for SUI, compressed** ([data.binance.vision S3 listing](https://s3-ap-northeast-1.amazonaws.com/data.binance.vision?list-type=2&prefix=data/futures/um/monthly/aggTrades/BTCUSDT/BTCUSDT-aggTrades-2025)). The converter is a per-candle Python loop.

The practical route for any footprint research is to precompute per-candle features offline from the CSVs: volume-based diagonal imbalances on a zero-filled tick grid, POC, unfinished-auction flags and stacked counts. Then merge them the way your existing taker-volume pipeline does (`user_data/scripts/fetch_binance_taker.py`), rather than using the built-in columns.

## The order-flow industry sells tools, courses and evaluations, not tested edges

None of the platforms checked publishes accuracy or performance statistics for trading on its signals. Where vendors document their tools, the documentation is more cautious than the marketing:

- **Bookmap** claims "100% accurate detection of native Iceberg orders" on CME market-by-order data ([Bookmap forum](https://bookmap.com/forum/viewtopic.php?p=2099)). Its own knowledge base warns that under data aggregation the indicators "may become unpredictable (lose detections, show fake detections)" ([Bookmap KB](https://bookmap.com/knowledgebase/docs/Addons-SIT)). Its blog says the tools are not "magic arrows" ([Bookmap blog](https://bookmap.com/blog/stops-and-icebergs-how-to-detect-hidden-orders-using-mbo-data)).
- **CoinGlass** calls its heatmap a tool "designed to predict" liquidation levels, to be read as relative, not absolute ([CoinGlass](https://www.coinglass.com/tr/learn/coinglass-intro-en)). No exchange publishes individual liquidation prices, so every heatmap is a leverage-assumption model ([Bitsgap](https://bitsgap.com/blog/crypto-liquidation-heatmap-explained)).

Detecting an iceberg and profiting from one are different claims, and no vendor makes or tests the second.

The incentives are visible. ATAS pays affiliates "up to 35% of the payments from each client you refer" for life ([ATAS referral program](https://atas.net/referral-program/)), and Bookmap runs a tiered referral programme ([Bookmap affiliate](https://bookmap.com/affiliate)). Topstep gives free ATAS access to every trader in an active Trading Combine ([Topstep help centre](https://intercom.help/topstep-llc/en/articles/8284185)). Order-flow educator Fabio Valentini co-founded the Deepcharts platform ([kagels-trading](https://www.kagels-trading.de/deepcharts-erfahrungen/)). His best evidence, top placings in the Robbins World Cup, is real-money but short-window and self-selected ([PickMyTrade](https://blog.pickmytrade.trade/fabio-valentini-pro-scalper-nasdaq-scalping-strategy/)). ICT's Michael Huddleston, the source of most "liquidity sweep" vocabulary, has never published a broker-verified track record ([Phidias](https://phidiaspropfirm.com/education/is-ict-legit); that source sells prop evaluations itself). No peer-reviewed test of order blocks, fair-value gaps or BOS/CHoCH was found ([PineConnector](https://www.pineconnector.com/blogs/pico-blog/smc-ict-concepts-as-rules)). The earlier independent tests still stand: a sweep rule won **71.9% of trades but returned −7.4%** and beat buy-and-hold on 8% of 903 assets ([IndicatorEdge](https://indicatoredge.io/smart-money-research)). That is the high-win-rate, negative-expectancy pattern your Asia-range fades reproduced.

Outcome statistics supply the missing denominator for payout screenshots:

- **Topstep's 2025 disclosure**, relayed by third parties: **16.8%** of Trading Combines were completed, **33.3%** of funded participants received a payout, and **0.71%** of Express Funded traders were called up to Live ([WikiFX](https://www.wikifx.com/en/news/details/202609281264561516.html); [Fortunly](https://fortunly.com/statistics/prop-firm-challenge-pass-rate-statistics/)). Roughly 5% of evaluations end in any payout, and those payouts come mostly from simulated accounts funded by evaluation fees.
- **Brazil.** Every individual who started day trading mini-index futures in 2013–2015 was observed. Of those who persisted beyond 300 days, 97% lost money and about 1.1% earned more than the minimum wage. The authors call day trading for a living "virtually impossible… contrary to what course providers claim" ([SSRN 3423101](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3423101); [CXO summary](https://www.cxoadvisory.com/investing-expertise/day-trading-a-bust/)).
- **Taiwan, 1992–2006.** Fewer than 1% of day traders earned reliably positive returns net of fees ([Barber, Lee, Liu & Odean](https://faculty.haas.berkeley.edu/odean/papers/day%20traders/day%20trading%20and%20learning%20110217.pdf)).
- **EU regulators** found that 74–89% of retail CFD accounts lose money ([ESMA 2018](https://www.esma.europa.eu/node/84933)).

None of these studies isolates order-flow users. Nothing suggests the tools change the base rate, and no vendor has published evidence that they do.

## Daily trend following is the one directional family that survives costs out of sample

Time-series momentum has the deepest crypto evidence:

- Liu & Tsyvinski document daily and weekly TSMOM in BTC, ETH and XRP. Their sample ends in 2018 and returns are gross ([RFS 2021](https://ideas.repec.org/a/oup/rfinst/v34y2021i6p2689-2727..html)).
- Detzel et al. show that price-to-moving-average ratios forecast daily Bitcoin returns **both in and out of sample** ([Financial Management 2021](https://ideas.repec.org/a/bla/finmgt/v50y2021i1p107-137.html)).
- Zarattini, Pagani & Barbon use a survivorship-free universe of 21,616 assets and an ensemble of Donchian channels with volatility sizing. They report **Sharpe 1.58** long-only, at costs of 10–50 bp ([SFI RP 25-80](https://ideas.repec.org/p/chf/rpseri/rp2580.html)).
- Howden & Andreev's walk-forward BTC/ETH test reports a **net Sharpe of 1.41 versus 0.70 for buy-and-hold, with maximum drawdown −44.6% versus −84.4%**. They concede that the 30-day lookback shows "sharp-parameter fragility" ([SSRN 7115459](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=7115459)).

The most honest recent anchor is the plain one-month TSMOM benchmark in a 2026 preprint. Out of sample over January 2022 to December 2024, with taker fees, slippage and funding, it reached only **Sharpe 0.65**. The headline 2.41 belongs to a heavily engineered model ([arXiv 2602.11708](https://arxiv.org/pdf/2602.11708)).

The counter-evidence is serious and specific to BTC. Hudson & Urquhart tested about 15,000 technical rules with data-snooping corrections. They found strong in-sample results but **"no predictability for Bitcoin" out of sample**, while other coins retained it ([Annals of OR 2021](https://link.springer.com/article/10.1007/s10479-019-03357-1)). A practitioner study of 2017–2025 BTC adds a second warning. A trend rule cut the worst drawdown from 84% to about 15%, but **a plain volatility rule with no trend signal captured most of the same improvement**, and the return advantage "mostly did not hold up" ([Summitward](https://summitward.com/learn/crypto-trend-following)). Vol-managed momentum also leaves tail exponents unchanged ([Grobys et al. 2025](https://osuva.uwasa.fi/handle/11111/18877)).

Together these set the bar for any test. Trend following must beat a **volatility-targeted always-long** control, not just raw buy-and-hold.

Horizon decides whether costs eat the edge. At a Binance taker round trip of about 0.08–0.10%, a daily rule that flips a few dozen times a year pays roughly 2–5% a year. A 1h–4h rule can pay 10–30% or more. Minute-bar and hourly implementations of otherwise valid trend signals lose heavily to turnover ([CryptoQuant](https://cryptoquant.dev/resources/blog/improve-buy-and-hold-btc); [arXiv 2606.00060](https://arxiv.org/html/2606.00060v1)). That fits your 1h 4h-trend/1h-RSI rule failing out of sample at a minimum PF of 0.72. It also suggests the failure was partly about horizon, not about trend itself.

Behaviour across 2022–2026 is regime-dependent. Trend rules mostly protected capital in the 2022 bear market but whipsawed in ranging spells. A practitioner 50/200 golden-cross test returned **+87% with a 37% maximum drawdown in 2022–2026, against +23% with a 67% drawdown for buy-and-hold**, and struggled in the 2025–26 consolidation ([Coinquant](https://www.coinquant.ai/blog/mean-reversion-crypto-strategy-backtested-when-it-beats-trend-following)). BTC fell nearly 30% from its October 2025 high in Q4 2025 ([Forex.com](https://www.forex.com/en-us/news-and-analysis/weekly-crypto-technical-outlook-the-market-continues-to-show-weakness-toward-the-end-of-2025/)). No reliable calendar-year net figures for a canonical specification were found, so this report gives none.

Other directional families rank lower:

- **Cross-sectional momentum** earned about 3% a *week* gross in 2014–2018, concentrated in large coins ([Liu, Tsyvinski & Wu, JF 2022](https://www.nber.org/papers/w25882.pdf)). It reportedly "failed from 2022 to 2023" ([Springer chapter](https://link.springer.com/chapter/10.1007/978-981-95-2566-9_30)). It needs a universe of dozens of coins, so it cannot be built from BTC and SUI alone.
- **Short-horizon reversal** is real. A 2026 preprint finds mean reversion in about **98% of 183 Binance pairs at 15 minutes** (the earlier snippet read 90%), but it narrows under artifact-robust scoring ([arXiv 2608.21888](https://arxiv.org/pdf/2608.21888)). It is a liquidity-provision premium concentrated in small coins, while "the largest and most tradeable coins exhibit daily momentum rather than a reversal" ([ResearchGate](https://www.researchgate.net/publication/354881251_Up_or_down_Short-term_reversal_momentum_and_liquidity_effects_in_cryptocurrency_markets)). A 1-day reversal backtest was "completely destroyed by transaction costs" ([GitHub](https://github.com/prams2104/crypto-momentum-backtest)).

## Funding carry was the best-evidenced trade, and it now pays about what cash pays

Three academic sources document very large historical carry:

- Christin et al. report in-sample Sharpe ratios of 7–10 for the spot-long / perp-short trade ([CMU WP](https://www.andrew.cmu.edu/user/azj/files/CarryTrade.v1.0.pdf)).
- The BIS finds average carry above 10% a year. It also finds that **high carry predicts crashes** ([Schmeling, Schrimpf & Todorov, BIS WP 1087](https://www.bis.org/publ/work1087.pdf)).
- He et al. report a BTC Sharpe of **1.8 at retail costs** and 3.5 for zero-fee market makers ([arXiv 2212.06888](https://arxiv.org/abs/2212.06888v6)).

A 2025 survey snippet puts carry's Sharpe at 6.45 over 2020–2025, 4.06 from 2024, and "negative in 2025". A second search could not re-locate that sentence, so treat it as unverified ([Borri et al., arXiv 2510.14435](https://arxiv.org/pdf/2510.14435)).

The compression is consistent across sources:

- BTC funding averaged 11%, 4.9% and 2.2% in 2024, 2025 and 2026 to August, per Ethena's figures, which no independent source confirmed ([FXStreet](https://www.fxstreet.com/cryptocurrencies/news/ethena-looks-beyond-crypto-to-squeeze-yield-from-booming-equity-perpetuals-202608281313)).
- sUSDe yields fell from above 20% to about 3.5–4.5% ([Blockworks](https://blockworks.com/newsletter/the-breakdown/issue/post_999b16ee-0fe0-4631-a1d0-2aa15a1d18a7)).
- The CME basis stayed below 9% through 2025 and briefly turned negative in December 2025 ([Flowdesk](https://flowdesk.co/updates/blogs/6f3b8c1a2e9d4f7c8a5b2e91/)).
- On 25 September 2026, cross-exchange BTC funding stood at −0.7% annualised ([DeFi Rate](https://defirate.com/perp/snapshot/2026-09-25T1925/)).

Tail risk is operational. On 10–11 October 2025 about $19bn was liquidated, and USDe briefly traded at about $0.65 on Binance only ([arXiv 2512.01112](https://arxiv.org/html/2512.01112v2); [The Defiant](https://thedefiant.io/newsletter/defi-daily/the-ultimate-10-10-crash-autopsy)).

**What the literature predicts for your pre-registered test** (`user_data/NOTES.md` §4i; `user_data/scripts/carry_backtest.py`). Your structure puts 2/3 of capital into spot and shorts an equal perp notional with 1/3 margin. Return on capital is therefore about **0.67 × funding**, less costs. One entry and one exit across both legs cost roughly 0.34% of notional, about 0.23% of capital, before rebalances. Clearing 4% on capital needs Binance BTCUSDT funding of roughly **6.4% annualised or more in every out-of-sample year**.

| Year | BTC funding (Ethena avg) | Implied always-on return on capital | vs 4% bar |
|---|---|---|---|
| 2024 (design) | ~11% | ~7% | pass |
| 2025 (OOS) | ~4.9% | ~3% | likely fail |
| 2026 to Oct (OOS) | ~2.2% | ~1–1.5% | fail |

**Expected verdicts by criterion:**

- **BTC return.** Expect BTC always-on to fail on return in both out-of-sample years, while likely clearing the doubled-cost "> 0%" line.
- **Sharpe.** Sharpe ≥ 1 is plausible in positive-funding stretches, because basis noise is small.
- **Drawdown.** A drawdown within 5% is plausible for BTC if the short leg is never squeezed.
- **Switched variants.** The 5/10/20% rules (enter on the 3-day mean, exit at X/4) should improve Sharpe but sit idle most of 2025–26 and earn less in absolute terms. The BIS crash result implies that the windows where they do switch on are the ones most likely to reverse sharply.
- **SUI.** SUI has no sourced funding average. It probably pays more in bull phases and goes negative more often. Its volatility makes the **5% drawdown line the criterion most at risk**, through basis gaps and pressure on the 2x short's margin, which your `margin_ev` counter will show.

**The one thing that would overturn the BTC prediction.** Ethena's averages are multi-venue. If Binance BTCUSDT spent most of 2025 pinned at its default interest-rate floor of 0.01% per 8 hours (about 11% a year, unverified here), always-on BTC could earn about 7% and pass. Read the Binance funding file before assuming either outcome.

Even a pass would mean roughly cash-like yield with exchange and stablecoin tail risk. The vendor framing is that Binance and Bybit retail venues "often over-extend" ([Sharpe.ai](https://www.sharpe.ai/funding-rates/sui)), which is a heuristic, not a measurement.

The other market-neutral families are weaker:

- **Volatility selling.** BTC has a variance risk premium larger than the S&P 500's ([arXiv 2410.15195](https://arxiv.org/html/2410.15195v2)). Deribit's own strangle backtest shows **23.8% APR with a 26.5% maximum drawdown** ([Deribit Insights](https://insights.deribit.com/?p=99807)), and Freqtrade cannot trade options.
- **Market making** at a 0.02% maker fee loses to adverse selection of about 1.2 bp even before fees ([SAIndustries](https://github.com/SAIndustries/LOB-Market-Making); [arXiv 2502.18625](https://arxiv.org/pdf/2502.18625)).
- **Pairs trading** on 26 Binance coins underperformed at 5-minute, hourly and daily frequencies ([IEEE Access 2020](https://ieeexplore.ieee.org/document/9200323)). A 2026 copula study was negative net of a 0.08% round trip ([QFE 2026](https://www.aimspress.com/aimspress-data/qfe/2026/2/PDF/QFE-10-02-016.pdf)).
- **Cross-exchange arbitrage** has "almost disappeared" since April 2018 ([Crépellière et al., JFM 2023](https://wiwi.uni-paderborn.de/fileadmin-wiwi/cetar/TAF_Working_Paper_Series/TAF_WP_067_CrepellierePelsterZeisberger2022_rev.pdf)).

## Ranked recommendation with evidence grades

Grades:

- **A**: peer-reviewed, out of sample and net of costs.
- **B**: peer-reviewed or credible preprint, with partial out-of-sample or cost treatment.
- **C**: in-sample, gross, or a practitioner test with a disclosed method.
- **D**: vendor or educator claims, or untested.

Sharpe and drawdown expectations are my synthesis of the figures above, not numbers any single source reports.

| Rank | Strategy | Grade | Realistic net expectation | Data needs | Freqtrade feasibility |
|---|---|---|---|---|---|
| 1 | Daily vol-targeted trend ensemble on BTC, long/flat (long/short as a variant) | B (C for 2024–26) | Sharpe 0.5–1.0; max DD 25–45%; main gain is drawdown control | Binance 1d perp candles, mark and funding (free; Freqtrade downloads them) | Good: `timeframe='1d'`, `custom_stake_amount`, `adjust_trade_position`, `can_short`, funding applied in backtests |
| 2 | BTC spot-long / perp-short funding carry | B historically, C for 2025–26 | ~1–4% a year on capital now; Sharpe can exceed 1; operational tail risk | Spot and perp 1h plus funding (free) | Not native (one trading mode per bot); your standalone simulator; live needs two bots or a CCXT script |
| 3 | Benchmark, not a strategy: vol-targeted BTC holding, or cash/stablecoin yield | — | Captures much of the trend rule's drawdown benefit | Same as rank 1 | Trivial |
| 4 | Opportunistic SUI funding carry | C/D | Higher bursts, high basis and drawdown risk | Same as rank 2 | As rank 2 |
| 5 | Trend rule on SUI | D (no study; history from 2023 only) | Unknowable; wide intervals | Same as rank 1 | Good, but report-only |
| 6 | Defined-risk BTC option selling | C | Double-digit APR with 9–27% drawdowns in vendor tests; skewed | Deribit or Binance options | None |
| 7 | Cross-sectional momentum | B gross, failed 2022–23 | Unknown net; crash-prone | 20–40 perps with funding | Possible but awkward; not with 2 coins |
| 8 | Footprint continuation (stacked imbalances with the move) | D | Unknown; cost hurdle about 10 bp a trade | aggTrades (free, 18 GB) | Feasible only with offline features |
| 9 | Daily or intraday reversal, pairs, market making, sweeps, crowding, iceberg, book imbalance, heatmaps | B–D, negative | ≤ 0 after retail costs; several measured by you | Varies | Drop |

## Pre-registered next test: a frozen daily trend ensemble on BTC

The idea is to take parameters fixed by literature published before 2022, so that **2022-01-01 to 2026-10-31 is genuinely post-publication out-of-sample data.** Commit this specification and its git hash before downloading anything beyond warm-up data.

**Data.** Binance BTC/USDT:USDT 1d candles plus mark and funding. Download them with `freqtrade download-data --trading-mode futures --timeframes 1d`. Use 2020-01-01 to 2021-12-31 only as a code sanity window, with no tuning. Run SUI/USDT:USDT from 2023-05 as report-only.

**Signal**, computed on the daily close and acted on at the next open:

- s = the mean of four components, sign(20-day return), sign(60-day return), sign(120-day return) and sign(close − SMA50), giving s ∈ [−1, 1].
- Long/flat variant: exposure = max(s, 0). Long/short variant: exposure = s.

**Sizing and trading:**

- Target notional = exposure × min(30% ÷ realised 30-day annualised volatility, 1.5) × capital.
- Rebalance only when the target changes by at least 0.20 of capital.
- No stops, no other filters.

**Costs.** Taker 0.05% per side, plus 2 bp slippage on BTC and 5 bp on SUI. Funding comes from Binance history. Run a stress case at double costs.

**Controls:**

- C1: the same sizing with s ≡ 1, i.e. vol-targeted always-long.
- C2: 1x perp buy-and-hold with funding.

**Verification.** Freqtrade's result must match an independent pandas simulation of the same rules to within 0.1 Sharpe.

**Pass rule.** Each variant is judged separately on BTC, and every line must hold.

| Criterion (2022-01-01 → 2026-10-31) | Threshold |
|---|---|
| Net daily-return Sharpe, annualised | ≥ 0.50 |
| Stationary block bootstrap (20-day blocks, 10,000 draws), one-sided 90% lower bound of Sharpe | > 0 |
| Sharpe minus C1 Sharpe | ≥ +0.15 |
| Max drawdown | ≤ 35% and ≤ 0.75 × C1's max drawdown |
| Worst calendar year (2022, 2023, 2024, 2025, 2026 YTD) | no loss worse than −20% |
| Double-cost Sharpe | ≥ 0.35 |
| Robustness: each single component run alone | ≥ 3 of 4 with positive net Sharpe |

**Interpreting the result:**

- With under five years of data, the bootstrap line in practice needs a Sharpe of about 0.6 or more. A narrow miss is a fail, not a "nearly".
- Report turnover and total funding paid.
- A SUI result counts only as "consistent" or "inconsistent" (Sharpe above or below 0), never as a pass.
- **Prior.** My subjective prior of passing is about 25–35%. The C1 line is the most likely to fail, given the practitioner evidence that volatility sizing alone does most of the work.

**After a pass:** six months of dry-run from November 2026. Judge it on execution fidelity, not P&L, because six months is too short: fills within 10 bp of the modelled daily price, and funding matching the backtest model.

**After a fail:** do not re-tune on this window. Conclude that no tested directional rule beats vol-targeted holding for this account. The remaining choice is between vol-targeted exposure, carry if §4i passes, and cash.

## Conclusion

The pattern across your two years of pre-registered tests and this literature is consistent. The shorter the horizon and the more a method claims to see other traders' intentions, the weaker the independent evidence and the stronger the commercial packaging. The only edges with out-of-sample support are slow, crude risk premia: trend persistence over weeks, and the leverage-demand premium in funding. Both are now partly arbitraged, and both deliver most of their value as **risk reduction or cash-like yield, not as alpha**. For this account, "best strategy" therefore means the cheapest exposure with the shallowest drawdown that survives costs, judged against a vol-targeted hold. It does not mean a setup.

Two results would genuinely change this view. One is the daily trend ensemble clearing the C1 control after 2022, which would show that trend timing adds something beyond volatility sizing post-publication. The other is Binance-specific BTC funding staying near its 11% floor through 2025–26 despite the multi-venue averages, which would revive carry as a 6–7% product. Both are checkable with free data in days. The ranking above should be revised only on those results. Before relying on any figure, open the primary texts that were seen only as snippets here: arXiv 2602.11708, 2212.06888, 2510.14435 and 2608.21888, SSRN 7115459, BIS WP 1087, and Topstep's own disclosure.
