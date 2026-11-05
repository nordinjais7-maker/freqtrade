# Directional Strategy Families in Crypto: Evidence Grade, Out-of-Sample and After-Cost Results

**Access note (important for the report writer):** Every full-text fetch failed in this session. The hosts arxiv.org, link.springer.com, researchgate.net, monash.edu, concretumgroup.com and cxoadvisory.com do not resolve in the sandbox network. **All figures below come from search-engine snippets or summaries of abstracts, not from the papers' own tables.** Each one should be checked against the primary PDF before anyone relies on it. Tags: [A] = academic (peer-reviewed or working paper), [I] = industry or vendor, [P] = practitioner/blog/GitHub.

---

## 1. Time-series momentum (TSMOM) / trend following in crypto

### Takeaway
Single-asset and multi-coin TSMOM is the best-supported directional family in crypto. The academic evidence (Liu & Tsyvinski, RFS 2021; Detzel et al., FM 2021) shows daily/weekly trend predictability. Recent studies report net-of-cost Sharpe ratios of roughly 0.65–1.6 for simple trend rules. The main benefit is consistent: much smaller drawdowns than buy-and-hold. Excess returns over buy-and-hold are weaker and depend on the sample. Very high Sharpe figures (above 2) come from more complex, more heavily tuned models and should be discounted.

### Cited Findings
- **Liu & Tsyvinski, "Risks and Returns of Cryptocurrency", Review of Financial Studies 34(6), 2021, pp. 2689–2727 [A].** Reports a strong time-series momentum effect, and investor-attention proxies forecast crypto returns. The NBER version (w24877, 2018) finds significant TSMOM at daily and weekly frequencies for BTC, ETH and XRP. The sample ends in 2018, so this is pre-2019 and in-sample, gross of costs. — [IDEAS/RFS](https://ideas.repec.org/a/oup/rfinst/v34y2021i6p2689-2727..html); [NBER w24877](https://www.nber.org/system/files/working_papers/w24877/w24877.pdf)
- **Detzel, Liu, Strauss, Zhou & Zhu, "Learning and predictability via technical analysis: Evidence from bitcoin and stocks with hard-to-value fundamentals", Financial Management 50(1), 2021, pp. 107–137 [A].** Ratios of price to moving average forecast daily Bitcoin returns **both in and out of sample**. The paper also gives an equilibrium model in which technical analysis arises from rational learning. The trading test (summarised by CXO) holds BTC when price is above a 5/10/20/50/100-day SMA and cash otherwise. It performs well **gross**, and CXO cautions that market depth may not have supported large trades over the early sample. Exact Sharpe figures were not retrieved. — [IDEAS](https://ideas.repec.org/a/bla/finmgt/v50y2021i1p107-137.html); [CXO summary](https://www.cxoadvisory.com/currency-trading/timing-bitcoin-with-smas/) (snippet only). A practitioner note says daily predictability "may not survive transaction costs". — [GitHub issue (P)](https://github.com/cuauhtemocbe/btc-predictor/issues/181)
- **Zarattini, Pagani & Barbon, "Catching Crypto Trends: A Tactical Approach for Bitcoin and Altcoins", Swiss Finance Institute RP 25-80, 2025 (SSRN, revised 2 Oct 2025) [A, working paper].**
  - Method: an ensemble of Donchian-channel trend models with several lookbacks, plus volatility-based position sizing.
  - Data: survivorship-bias-free, aggregated across exchanges, 21,616 crypto assets, Jan 2010 to mid-Mar 2025.
  - Results: the "Combo" model reports CAGR 30%, **Sharpe 1.58**, Sortino 2.03 and annualised alpha of 14% vs BTC. Sharpe stays around 1.5 across portfolio sizes.
  - Costs and direction: tested at 0.10%, 0.25% and 0.50% costs. It is **long-only** (rotates into cash, no shorts).
  - These figures come from third-party summaries only. — [IDEAS RePEc](https://ideas.repec.org/p/chf/rpseri/rp2580.html); [Barbon page](https://abarbon.com/papers/catching-crypto-trends); [Concretum page](https://concretumgroup.com/catching-crypto-trends-a-tactical-approach-for-bitcoin-and-altcoins/); [CXO summary](https://www.cxoadvisory.com/technical-trading/crypto-asset-trend-following-strategies/)
- **Howden & Andreev, "Risk-Managed Time-Series Momentum in Crypto Majors: Crash-State De-Risking and Drawdown Control", SSRN 7115459 (2026) [A, preprint].**
  - Walk-forward test with a 30-day lookback.
  - **Net-of-25 bp Sharpe 1.41** vs 0.70 for buy-and-hold. Max drawdown −44.6% vs −84.4%.
  - The authors themselves record that the L = 30 optimum is a "sharp-parameter fragility", i.e. the lookback was in effect chosen ex post. — [SSRN](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=7115459) (snippet)
- **"Systematic Trend-Following with Adaptive Portfolio Construction" (arXiv 2602.11708, 2026) [A, preprint].**
  - Out-of-sample window Jan 2022 – Dec 2024, with 4 bp taker fee, slippage and funding costs included.
  - The "AdaptiveTrend" model reports Sharpe 2.41. **The plain TSMOM-1M benchmark gets only Sharpe 0.65** over the same window.
  - Some table figures (TSMOM-1M return/vol/Sharpe) reportedly do not reconcile. — [arXiv](https://arxiv.org/pdf/2602.11708) (snippet)
- **Le & Ruthbah, "Trend-following Strategies for Crypto Investors" (Monash working paper) [A].** Found in search, but the full text was unreachable and no figures were retrieved. — [Monash PDF](https://www.monash.edu/__data/assets/pdf_file/0011/3744821/Trend-following-Strategies-for-Crypto-Investors.pdf)
- **Practitioner, 2017–2025 BTC [P].** A trend strategy cut the deepest loss from 84% (buy-and-hold) to about 15%. A **plain volatility rule with no trend signal captured most of the same improvement**. The return side "mostly did not hold up" (6.3% annual return). — [Summitward](https://summitward.com/learn/crypto-trend-following)
- **BTC-USD trend algorithm, 2021–2025 (ResearchGate) [P/A-grey].** Max drawdown −36.6% during 2022. — [ResearchGate](https://www.researchgate.net/publication/395400190_Performance_Analysis_of_a_BTC-USD_Trend-Following_Algorithm_A_Comprehensive_Quantitative_Study_2021-2025)
- **Golden Cross (50/200 SMA) BTC backtest, 2022–2026 [P].** +87.3% with 37.1% max drawdown, vs buy-and-hold +22.8% with 67.0% max drawdown. Trend rules struggled in the ranging regimes of 2018–19, most of 2022 and the 2025–26 consolidation. — [Coinquant](https://www.coinquant.ai/blog/mean-reversion-crypto-strategy-backtested-when-it-beats-trend-following)
- **Quantpedia (Padyšák & Vojtko), "Trend-following and Mean-reversion in Bitcoin" (2022, SSRN "Seasonality, Trend-following, and Mean Reversion in Bitcoin") and its "Revisiting" follow-up [I/P with disclosed method].**
  - MAX rule: buy BTC when it closes at a 10–50-day high. MIN rule: buy at a 10–50-day low. Shorter lookbacks are better for both.
  - The MIN leg alone had drawdowns above 80%.
  - In the later **out-of-sample** period (about 2.5 years), MAX "retained its effectiveness" and MIN degraded. — [Quantpedia original](https://quantpedia.com/trend-following-and-mean-reversion-in-bitcoin/); [Quantpedia revisit](https://quantpedia.com/revisiting-trend-following-and-mean-reversion-strategies-in-bitcoin/)
- **Industry (AQR, Man Group, Kaiko, CF Benchmarks).** Searches found **no primary crypto trend-following research from these firms** with disclosed methodology. A BIT (exchange) research page claims trend following beat buy-and-hold over 10 years (68.4% vs 62.8% average annual return). That is a vendor backtest and unverified. — [BIT Research (I)](https://www.bit.com/research)

### Inferences
- **Realistic net Sharpe for a simple, pre-specified BTC TSMOM/MA rule is about 0.6–1.2.** The 1.4–1.6 figures come from ensembles, vol-targeting and multi-coin long-only rotation with long samples that include 2013–2017. The out-of-sample 2022–2024 TSMOM-1M Sharpe of 0.65 is probably the most honest anchor for recent years.
- **The robust benefit is drawdown control, roughly halving max drawdown, not alpha.** One practitioner test suggests volatility targeting alone delivers much of this benefit. This matters for any Freqtrade design.
- **Lookbacks:** evidence clusters at 1–4 weeks for TSMOM (Liu & Tsyvinski weekly; the 30-day walk-forward) and 10–50-day breakouts/MAs (Quantpedia; Detzel's 5–100-day SMAs; Grobys et al.'s 20-day VMA). Ensembles across lookbacks reduce sensitivity to the choice.

### Gaps
- No exact Sharpe or drawdown tables were retrieved for Detzel et al., Zarattini et al. or Le & Ruthbah, because full text was unreachable.
- No audited CTA or managed-futures crypto-sleeve returns for 2022–2026 were found.

---

## 2. Cross-sectional momentum (CMOM) across coins

### Takeaway
Cross-sectional momentum was strong gross and in-sample through 2018–2021: about 2.5–4% per **week** in Liu–Tsyvinski–Wu (LTW), concentrated in large coins. It is crash-prone, reportedly **failed in 2022–2023**, and its factor-momentum profits decline over time. Net-of-cost, out-of-sample evidence on a perp-tradable universe of a few dozen coins is thin. It is the weakest-supported candidate for a retail trader running two symbols, and with BTC and SUI only it cannot be implemented at all.

### Cited Findings
- **Liu, Tsyvinski & Wu, "Common Risk Factors in Cryptocurrency", Journal of Finance 77 (2022), pp. 1133–1177; NBER w25882 [A].**
  - Long-short momentum portfolios earn about 3% excess **weekly** return: 2.7% at a 1-week lookback, 3.3% at 2 weeks, 4.1% at 3 weeks and 2.5% at 4 weeks.
  - Momentum is significant only among large coins: 4.2% per week above median size vs an insignificant 0.6% below median.
  - Sample is 2014–2018, coins with market cap above $1m (109 growing to 1,583). Figures are **gross and in-sample**. Commentators flag data-snooping and costs on illiquid coins. — [NBER](https://www.nber.org/papers/w25882.pdf); [Cowles PDF](https://cowles.yale.edu/sites/default/files/2022-10/LiuTsyvinskiWu2019%20COMMON%20RISK%20FACTORS.pdf); [SSRN](https://papers.ssrn.com/abstract=3379131); [Alpha Architect commentary](https://alphaarchitect.com/factors-investing-in-cryptocurrency/)
- **Grobys, Kolari, Sandretto, Shahzad & Äijö, "Cryptocurrency momentum has (not) its moments", Financial Markets and Portfolio Management (2025) [A].**
  - Crypto momentum suffers severe crashes. A single coin can make the portfolio's return statistically insignificant.
  - Volatility-managed momentum earns significantly higher payoffs, with alphas significant at 5%.
  - **Tail risk is unchanged**: the power-law exponents are the same for plain and risk-managed versions. The effect is concentrated in large caps. — [Univ. Vaasa repository](https://osuva.uwasa.fi/handle/11111/18877); [Springer](https://link.springer.com/article/10.1007/s11408-025-00474-9)
- **Momentum crash.** A drop of about 255% for crypto momentum in December 2020, which lies within LTW's ex-post sample window, is reported in a decay/replication search result. — [search summary referencing "Cryptocurrency momentum has (not) its moments"](https://link.springer.com/article/10.1007/s11408-025-00474-9) (snippet; verify)
- **2014–2023 study ("The Efficiency of Momentum Factors in Cryptocurrency", Springer chapter) [A].** Momentum strategies produced significant excess returns in 2019–2021, but **"all momentum strategies failed from 2022 to 2023."** — [Springer chapter](https://link.springer.com/chapter/10.1007/978-981-95-2566-9_30) (snippet)
- **Auckland University of Technology working paper on TSMOM and XSMOM in crypto [A].**
  - After transaction costs, six long-short portfolios beat the market on Sharpe ratio.
  - Costs can reach **0.6% per rebalance**.
  - TSMOM outperformed cross-sectional momentum. — [AUT PDF](https://acfr.aut.ac.nz/__data/assets/pdf_file/0009/918729/Time_Series_and_Cross_Sectional_Momentum_in_the_Cryptocurrency_Market_with_IA.pdf) (snippet)
- **Dobrynskaya, "Cryptocurrency Momentum and Reversal" [A].** About 2,000 large cryptocurrencies: positive momentum at horizons up to 2–4 weeks, and significant reversal at longer horizons. — [HSE conference PDF](https://conference.hse.ru/files/download_file_ex?hash=FAE0AB2DC7A67656E89A0B1CB27D8C7D&id=3B5EE9A5-0B18-458A-9458-B4ED0F6C6664)
- **"Cryptocurrency Factor Momentum" [A].** Finds significant factor momentum, driven by price momentum, but profits **"decline substantially over time"**. — [ICM repository](https://open.icm.edu.pl/server/api/core/bitstreams/86a51c47-8cd3-4201-88ee-42f44fb89227/content)
- **"Taming crypto anomalies: A Lasso-type factor model" (2026, Research in International Business and Finance, ScienceDirect) [A].**
  - Covers 49 anomalies, split into in-sample and out-of-sample periods.
  - The selected DS3 model (market, **two-week momentum**, residual momentum) holds after the LTW sample.
  - The size/market-value effect weakens out of sample. — [ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/S0275531926000255)
- **arXiv 2510.14435, "Cryptocurrency as an Investable Asset Class: Coming of Age" [A].** LTW-style factors remain robust in the post-2020 sample. — [arXiv](https://arxiv.org/pdf/2510.14435) (snippet)
- **Practitioner GitHub cross-sectional momentum backtest [P].** Breakeven cost of about 35 bp. — [GitHub](https://github.com/prams2104/crypto-momentum-backtest)

### Inferences
- The evidence conflicts. Factor-level robustness post-2020 is supported by the Lasso paper and arXiv 2510.14435. Strategy-level failure in 2022–23 is reported by the Springer chapter. The difference is plausibly about weighting, universe and crash exposure.
- A perp-only universe of 20–40 liquid coins resembles LTW's "above-median size" bucket, where momentum was strongest. However, Binance taker fees plus funding on the short leg (shorting alts usually *earns* funding when funding is positive, so this may partly help) and crash risk have not been tested together in any source found.
- With only BTC and SUI, CMOM collapses to a 2-asset relative-strength pair. That is not what the literature tests.

### Gaps
- No study was found that runs cross-sectional momentum on **perpetual futures with funding costs** in 2022–2026.
- No net Sharpe for 2024–2026 was found.

---

## 3. Mean reversion / short-term reversal (intraday, daily, weekly)

### Takeaway
Short-horizon reversal exists in crypto: at 15-minute horizons in liquid Binance pairs, and at daily, weekly and monthly horizons cross-sectionally. It is strongest in small, illiquid coins and is interpreted as compensation for **liquidity provision**. The largest coins show *daily momentum*, not reversal. High-turnover taker implementations are destroyed by costs. This matches the user's failed intraday OOS tests.

### Cited Findings
- **"Short-horizon mean reversion in cryptocurrency markets: a matched cross-market measurement", arXiv 2608.21888 (2026) [A, preprint]. This is likely the 15-minute reversal preprint referenced by the earlier report.**
  - 183 Binance pairs vs 187 US stocks/ETFs.
  - In 15-minute OOS tests, **98% of crypto pairs show mean reversion**, vs a zero-centred distribution for stocks.
  - The authors call it a "small but persistent" signal. It "narrows under artifact-robust rescorings" (bid-ask bounce and similar).
  - No net-of-cost taker profitability was reported in the snippet. — [arXiv](https://arxiv.org/pdf/2608.21888) (snippet)
- **"Up or down? Short-term reversal, momentum, and liquidity effects in cryptocurrency markets" [A].** Reversal depends on liquidity in the cross-section. **"The handful of largest and most tradeable coins exhibit daily momentum rather than a reversal."** — [ResearchGate](https://www.researchgate.net/publication/354881251_Up_or_down_Short-term_reversal_momentum_and_liquidity_effects_in_cryptocurrency_markets) (snippet)
- **Kozlowski, Puleo & Zhou, "Cryptocurrency return reversals", Applied Economics Letters 28(11), 2021 [A].** 200 coins, 2015–2019. Reversals at daily, weekly and monthly rebalancing are attributed to inefficiency plus **compensation for liquidity provision**, and are strongest in smaller, less liquid coins. — [IDEAS](https://ideas.repec.org/a/taf/apeclt/v28y2021i11p887-893.html); [Fairfield](https://fairfield.elsevierpure.com/en/publications/cryptocurrency-return-reversals/)
- **Nakagawa & Sakemoto, "New behaviorally-based cross-sectional reversal portfolios in the cryptocurrency market and market uncertainty", Finance Research Letters 85 (2025) [A].** Reversal portfolios stay profitable under "conservative transaction costs" including the COVID period. The holding period was not retrieved. — [IDEAS](https://ideas.repec.org/a/eee/finlet/v85y2025ipas154461232501058x.html); [SSRN](https://doi.org/10.2139/ssrn.5001299)
- **Shen, Urquhart & Wang, "Bitcoin intraday time-series momentum", Financial Review 57(2), 2022, pp. 319–344 [A].**
  - The first half-hour return (with volume-defined sessions) predicts the last half-hour.
  - Gains are strongest in BTC downturns.
  - The effect is attributed to **liquidity provision**, not late-informed trading.
  - Some trimmed-sample specifications reportedly flip sign. — [Birmingham](https://research.birmingham.ac.uk/en/publications/bitcoin-intraday-time-series-momentum/); [Reading PDF](https://centaur.reading.ac.uk/100181/3/21Sep2021Bitcoin%20Intraday%20Time-Series%20Momentum.R2.pdf)
- **Munich thesis [A-grey].** Negative first-order autocorrelation in BTC at 1h, 2h and 4h horizons. — [LMU ePub](https://epub.ub.uni-muenchen.de/97651/)
- **GitHub 1-day cross-sectional reversal backtest [P].** "Completely destroyed by transaction costs": 138% daily turnover, −28.5% net. — [GitHub](https://github.com/prams2104/crypto-momentum-backtest)
- **Quantpedia [I/P].** The BTC "buy at a 10–50-day low" (MIN) rule degraded out of sample, with drawdowns above 80% standalone. — [Quantpedia revisit](https://quantpedia.com/revisiting-trend-following-and-mean-reversion-strategies-in-bitcoin/)

### Inferences
- The convergent picture: reversal at very short horizons is a liquidity/microstructure premium. It is earned by makers or patient limit orders and largely lost by takers paying spread plus about 4–5 bp fees. The user's failed 15m–1h OOS results fit this.
- For BTC specifically, the daily horizon tilts toward momentum, so daily mean reversion on BTC has weak support. SUI, a mid/large-cap alt, may sit in between, but no study tests it.

### Gaps
- No study was found that measures the reversal premium **net of maker-vs-taker execution** on Binance perps.
- Weekly reversal on liquid perps after 2022 was not found.

---

## 4. 2022–2026 performance and post-publication decay

### Takeaway
Trend rules mostly worked as drawdown control in the 2022 bear market: they sat flat or short, though there were whipsaws in ranging spells. They lagged in parts of 2023–24 and struggled in the 2025–26 consolidation and reversal. CMOM reportedly failed in 2022–23. Crypto anomaly decay is documented qualitatively (factor momentum profits decline over time; size weakens OOS), but **no McLean–Pontiff-style post-publication study specific to crypto momentum was found**.

### Cited Findings
- OOS 2022–2024 with fees and funding: simple TSMOM-1M Sharpe **0.65**. — [arXiv 2602.11708](https://arxiv.org/pdf/2602.11708) (snippet)
- BTC trend algorithm max drawdown −36.6% in 2022. — [ResearchGate](https://www.researchgate.net/publication/395400190_Performance_Analysis_of_a_BTC-USD_Trend-Following_Algorithm_A_Comprehensive_Quantitative_Study_2021-2025)
- Trend rules struggled in the ranging periods of 2022 and 2025–26. Golden Cross 2022–2026: +87% with 37% max drawdown vs buy-and-hold +23% with 67% max drawdown. — [Coinquant (P)](https://www.coinquant.ai/blog/mean-reversion-crypto-strategy-backtested-when-it-beats-trend-following)
- BTC fell nearly 30% from its October 2025 high to below $90k in Q4 2025. — [TradingView/99Bitcoins](https://www.tradingview.com/news/99Bitcoins:37c5f55d3094b:0-crypto-market-2025-year-end-review-expert-insights/); [Forex.com](https://www.forex.com/en-us/news-and-analysis/weekly-crypto-technical-outlook-the-market-continues-to-show-weakness-toward-the-end-of-2025/)
- "All momentum strategies failed from 2022 to 2023" (cross-sectional). — [Springer chapter](https://link.springer.com/chapter/10.1007/978-981-95-2566-9_30)
- Crypto factor momentum profits "decline substantially over time". — [ICM](https://open.icm.edu.pl/server/api/core/bitstreams/86a51c47-8cd3-4201-88ee-42f44fb89227/content)
- In equities, McLean & Pontiff (2016) find anomaly returns about 26% lower out of sample and about 58% lower post-publication. Secondary sources label these numbers inconsistently. — [Micro Alphas (secondary)](https://microalphas.com/factor-decay/)
- Hudson & Urquhart: no out-of-sample predictability **for Bitcoin**, though it remains for other coins (details in Q7). — [Springer](https://link.springer.com/article/10.1007/s10479-019-03357-1)

### Inferences
- The pattern fits the hypothesis that BTC, the most liquid and most institutionalised coin, has become more efficient for simple technical rules. Less mature alts retain more trend predictability, at higher cost and with more crash risk.
- No reliable year-by-year net returns for 2023, 2024 or 2025 were found for a standard specification. The report writer should not state yearly figures.

### Gaps
- Calendar-year 2023, 2024 and 2025–26 net returns for a canonical BTC TSMOM are missing.
- There is no crypto-specific post-publication decay estimate.

---

## 5. Timeframes: daily vs intraday trend following after costs

### Takeaway
Evidence favours **daily (and weekly) horizons**. Intraday trend rules are either explained by liquidity provision (Shen et al.) or killed by turnover once realistic costs are added. No peer-reviewed study of 4h breakouts with walk-forward and costs was found.

### Cited Findings
- A 200-day SMA rule evaluated on **minute** data with 0.1% one-way cost lost essentially all capital through excessive trading. — [CryptoQuant blog (P)](https://cryptoquant.dev/resources/blog/improve-buy-and-hold-btc)
- An ML paper on hourly BTC data finds a 24-hour momentum benchmark loses heavily after costs because it trades too often. — [arXiv 2606.00060](https://arxiv.org/html/2606.00060v1) (snippet)
- 69 MA and breakout rules on daily and 1-minute data, 2016–2021: costs lowered profitability for XRP and LTC. The snippet's phrasing for BTC and ETH is ambiguous. — [ScienceDirect, "On the intraday return curves of Bitcoin" / related](https://www.sciencedirect.com/science/article/abs/pii/S1057521921001228) (snippet; attribution uncertain)
- A daily MA-crossover GitHub test (Bitstamp from 2014, 0.1% cost): **the largest in-sample returns came with the worst unseen-year outcomes**. — [GitHub (P)](https://github.com/ahmadjafariaghdam/-btc-trend-following-backtest)
- Grobys, Ahmed & Sapkota (2020), 11 coins, 2016–2018: a 20-day variable MA rule earns 8.76% p.a. excess excluding BTC. Only shorter long-MA horizons were informative. For privacy coins, only DASH was profitable, and on aggregate there was no excess over buy-and-hold. — [Univ. Vaasa](https://osuva.uwasa.fi/handle/11111/619); [privacy coins](https://osuva.uwasa.fi/handle/11111/636)
- Multi-timeframe trend on BTC (combining signals across timeframes) is discussed by Quantpedia and QuantSeeker, without retrieved figures. — [Quantpedia](https://quantpedia.com/how-to-design-a-simple-multi-timeframe-trend-strategy-on-bitcoin/); [QuantSeeker](https://www.quantseeker.com/p/combining-bitcoin-trend-signals-across)

### Inferences
- Cost math: a Binance USDT-M taker round trip at the standard tier is about 0.08–0.10% before slippage. Daily rules flip a few dozen times a year, roughly 2–5% annual cost drag. 1h–4h rules can flip hundreds of times, 10–30%+ drag, which overwhelms Sharpe-0.5-type edges. This is consistent with the user's failed 1h breakout with 4h trend alignment. (Fee level is background knowledge; the user should verify their VIP tier.)

### Gaps
- No academic out-of-sample evidence for 4h trend rules was found.

---

## 6. Implementability in Freqtrade (BTC and SUI on Binance USDT-M perps)

### Takeaway
The most defensible design is a **daily-bar, single-asset TSMOM / Donchian-breakout ensemble** for BTC (and SUI) with **volatility-targeted sizing**, either long/flat or long/short, rebalanced at most daily with a no-trade band. Funding is a material cost for longs held for long periods. SUI has no academic out-of-sample evidence specific to it: its history only starts in 2023 and covers mostly a single regime.

### Cited Findings
- Volatility-based sizing is part of the best-documented specification (Zarattini et al. ensemble). — [IDEAS](https://ideas.repec.org/p/chf/rpseri/rp2580.html)
- Vol-managed momentum improves payoffs but does not remove tail risk. — [Grobys et al. 2025](https://osuva.uwasa.fi/handle/11111/18877)
- Volatility rules alone captured most of the drawdown reduction in a 2017–2025 BTC test. — [Summitward (P)](https://summitward.com/learn/crypto-trend-following)
- Average perp funding (secondary, unverified) was about +0.004% (2022), +0.007% (2023) and +0.011% (2024). The interval and venue are unclear in the snippet. — [Elm Wealth (I)](https://elmwealth.com/perpetual-futures/)
- Funding-rate changes track price trends but are **not** a leading indicator of price. — [Coinbase Institutional (I)](https://www.coinbase.com/institutional/research-insights/research/market-intelligence/a-primer-on-perpetual-futures)
- The one out-of-sample 2022–24 TSMOM test that includes funding costs found Sharpe 0.65 for the plain benchmark. — [arXiv 2602.11708](https://arxiv.org/pdf/2602.11708)

### Inferences
- **Practical spec (inference, not tested by any cited source):**
  - Bars and signal: 1d candles. Signal = sign of an ensemble of 20/40/60/120-day returns or Donchian(20/55) breakouts.
  - Position size: target annualised volatility of about 20–40% ÷ realised 20–30-day vol, capped at 1–2x.
  - Execution: rebalance once a day only when the target changes by more than about 20–25%, with limit/post-only entries to cut fees.
  - Freqtrade setup: `timeframe='1d'` (or 4h bars with a daily signal), `custom_stake_amount` for vol sizing, `adjust_trade_position` for re-sizing, and `can_short=True` in futures mode.
- **Funding:** Binance's default funding is 0.01% per 8h, about 11% a year if a long is held continuously in a positive-funding market. Bull regimes, when trend rules are long, often carry above-baseline funding. Model funding explicitly; Freqtrade futures backtests support historical funding-rate data. This drag can wipe out much of a long-only trend excess return relative to spot.
- **Long/flat vs long/short:** most positive evidence (Zarattini, Detzel, Quantpedia MAX) is long/flat. Shorting adds 2022-type gains but whipsaw cost in ranging markets.
- **Expectation setting:** for BTC, plan around a net Sharpe of about 0.5–1.0 with max drawdown of about 25–45%, not 1.5+. SUI's 2023–2026 sample is too short and too regime-specific for a meaningful out-of-sample test. Any SUI result will have very wide confidence intervals.

### Gaps
- No published study tests trend rules on SUI.
- No study measures funding-cost drag on a TSMOM held on Binance USDT-M perps specifically.

---

## 7. Data-snooping and survivorship

### Takeaway
The flagship data-snooping-corrected study (Hudson & Urquhart) finds technical rules look significant in-sample even after multiple-testing corrections, but **out of sample there is no predictability for Bitcoin**, while it persists for smaller coins. Survivorship-bias-free universes are rare. Zarattini et al. is a notable exception.

### Cited Findings
- **Hudson & Urquhart, "Technical trading and cryptocurrencies", Annals of Operations Research 297 (2021), pp. 191–220 (online 2019) [A].**
  - About 15,000 rules in five classes, across two BTC markets plus three other cryptocurrencies.
  - Uses multiple-hypothesis (data-snooping) procedures. In-sample significant predictability and profitability are found for every class and coin, with higher risk-adjusted returns and reduced drawdowns.
  - **Out of sample: "no predictability for Bitcoin", but predictability remains in other cryptocurrency markets.** — [Springer](https://link.springer.com/article/10.1007/s10479-019-03357-1); [Reading repository](https://reading-clone.eprints-hosting.org/85715)
- **Deprez & Frömmel (later study, stricter conditions) [A].** Contrary to Hudson & Urquhart, their rules "still can significantly outperform buy-and-hold out-of-sample, mainly risk-return wise." — via [arXiv crypto trading survey / search snippet](https://arxiv.org/pdf/2003.11352) (exact citation not retrieved; verify)
- **Zarattini et al.** use survivorship-bias-free data covering 21,616 assets. — [CXO summary](https://www.cxoadvisory.com/technical-trading/crypto-asset-trend-following-strategies/)
- **LTW universe.** Coins above $1m market cap expanded from 109 to 1,583 over the sample. Commentators flag data-snooping across many tested factors and gross-only returns. — [Alpha Architect](https://alphaarchitect.com/factors-investing-in-cryptocurrency/)
- **Howden & Andreev** self-report parameter fragility at L = 30. — [SSRN](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=7115459)

### Inferences
- For the user: any Freqtrade parameter sweep should be scored with a deflated Sharpe ratio, White's Reality Check or Hansen's SPA, or be locked before testing. Ensembles across lookbacks are the cheapest guard.
- Perp universes on Binance carry their own survivorship bias, because delisted perps disappear from data. This matters only for multi-coin CMOM, not for BTC/SUI single-asset tests.

### Gaps
- No Hansen SPA application to crypto trend rules after 2022 was found.
- The full Deprez & Frömmel citation is unverified.

---

## Evidence-grade summary (for report writer)

| Strategy family | Best evidence | Out-of-sample? | Net of costs? | Realistic net Sharpe | Retail Freqtrade BTC/SUI fit |
|---|---|---|---|---|---|
| Daily single-asset TSMOM / MA / Donchian, vol-sized | Detzel 2021 (OOS), Zarattini 2025, Howden 2026, arXiv 2602.11708 | Partly (Detzel OOS; walk-forward preprints) | Yes in preprints (10–50 bp; fees+funding) | ~0.6–1.2 (1.4–1.6 in tuned/long-sample studies) | **Best fit** |
| Breakout to new highs (MAX) on BTC | Quantpedia | Yes (~2.5 yr) | Unclear | Not retrieved | Good fit |
| Cross-sectional momentum | LTW 2022 (gross, 2014–18) | Mixed; failed 2022–23 | Weak | Unknown; crash-prone | Not implementable with 2 coins |
| Daily/weekly reversal | Kozlowski 2021; Nakagawa 2025 | Some | Claimed robust (FRL 2025); contradicted by high-turnover practitioner test | Small-cap liquidity premium | Poor fit for BTC (BTC shows daily momentum) |
| Intraday reversal / momentum (15m–4h) | arXiv 2608.21888; Shen et al. 2022 | Yes (stat), no (economic) | Generally fails for takers | ≤0 for takers | Poor fit; consistent with user's failed tests |
| Technical rules with data-snooping control | Hudson & Urquhart 2021 | Yes | n/a | No OOS BTC predictability | Caution |
