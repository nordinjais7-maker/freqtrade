# Vendor and Educator Claims: Order-Flow / Liquidity-Hunt Ecosystem vs Independent Evidence

Method note: these notes come from about 20 web searches made on 2026-11-03. quantpedia.com and thortradecopier.com would not resolve from this environment, so WebFetch could not open them. **Most figures below come from search-result snippets, not from pages I read in full.** Snippet-only figures are marked [snippet]. Source tags: academic / regulator / industry / vendor / educator / anecdotal.

Already covered in the earlier report, mentioned here only once: the IndicatorEdge SMC study (sweep rule had a 71.9% win rate but returned −7.4%; it beat buy-and-hold on 8% of 903 assets — https://indicatoredge.io/smart-money-research) and the StatOasis study, which found no significant edge.

---

## 1. Platforms: what they claim, published accuracy statistics, conflicts of interest

### Takeaway
None of the order-flow or liquidity platforms I checked publishes performance or win-rate statistics for its tools. The claims are about how the tools work: detecting icebergs and showing liquidity or estimated liquidations. The vendors' own documentation is more cautious than their forum or marketing copy. Affiliate programmes that pay recurring commissions are common, which pushes "reviews" and educator content toward recommending the platforms.

### Cited Findings
- **Bookmap Stops & Icebergs (SI) Tracker:** a Bookmap forum post claims "100% accurate detection of native Iceberg orders (except their still hidden size)" on CME MBO data. The detection logic is described as based on internal research and specific to CME's matching-engine event sequences. Synthetic icebergs are found with a heuristic "Resistance" method that counts orders added immediately after a price change. [snippet] (vendor) — [Bookmap forum, MBO Bundle addon](https://bookmap.com/forum/viewtopic.php?p=2099); [Bookmap forum, Iceberg detector](https://bookmap.com/forum/viewtopic.php?p=2974)
- A Bookmap forum post about the cheaper non-MBO iceberg detector says false positives can occur because it relies on microstructural events. A user reported that it does not alert every time. [snippet] (vendor/anecdotal) — [Bookmap forum](https://bookmap.com/forum/viewtopic.php?p=2974)
- Bookmap's knowledge base warns that when automatic data aggregation switches on under load, "SI indicators may become unpredictable (lose detections, show fake detections, etc.)". [snippet] (vendor) — [Bookmap KB, Addons-SIT](https://bookmap.com/knowledgebase/docs/Addons-SIT)
- Bookmap's 2025 education blog says the stop and iceberg tools are not "magic arrows" or trading signals. [snippet] (vendor) — [Bookmap blog](https://bookmap.com/blog/stops-and-icebergs-how-to-detect-hidden-orders-using-mbo-data)
- **No accuracy or performance statistic** turned up for Bookmap's absorption or heatmap features, ATAS, Sierra Chart, Exocharts, Quantower, TradingLite, Jigsaw, or NinjaTrader Order Flow+. I did not do a dedicated search for each one, so this is a gap rather than proof that none exist.
- **CoinGlass** calls its liquidation heatmap a tool "designed to predict the price levels at which large-scale liquidations may occur" and tells users to read it as a relative figure, not an absolute one. [snippet] (vendor) — [CoinGlass intro](https://www.coinglass.com/tr/learn/coinglass-intro-en)
- Third-party explainers say no exchange publishes individual liquidation prices, so heatmaps are estimates built from open interest, assumed leverage and book depth. They show where liquidations *could* cluster, not confirmed positions. [snippet] (industry) — [Bitsgap](https://bitsgap.com/blog/crypto-liquidation-heatmap-explained); [Mobee](https://mobee.com/en/mobee-academy/blog/liquidation-heatmap). A TradingView author calls CoinGlass a "prediction based algorithm" rather than true data. [snippet] (anecdotal) — [TradingView idea](https://www.tradingview.com/chart/BTCUSD/08iU4E6T-BTC-Drawing-your-own-Heatmaps-and-Understanding-how-BTC-Moves)
- **Hyblock:** I found no published methodology or accuracy figures for its liquidation levels or heatmaps. Gap.
- **Conflicts of interest and affiliate programmes:**
  - Bookmap runs a referral programme that pays commission on referred subscriptions. The rate rises with the number of referrals, the payout minimum is $200, and refunds are clawed back. A third-party listing gives a 30-day cookie. [snippet] (vendor) — [Bookmap affiliate](https://bookmap.com/affiliate); [LinkClicky](https://linkclicky.com/affiliate-program/bookmap/)
  - ATAS advertises "up to 35% of the payments from each client you refer" with "lifetime affiliation" and a €50 withdrawal minimum. [snippet] (vendor) — [ATAS referral program](https://atas.net/referral-program/)
  - **Prop-firm tie-up:** Topstep gives free ATAS access to every trader with an active Trading Combine. [snippet] (industry) — [Topstep help centre](https://intercom.help/topstep-llc/en/articles/8284185). ATAS also has a co-branded page for the prop firm Legends Trading. (vendor) — [ATAS for Legends Trading](https://atas.net/legends-trading/)
  - Jigsaw Trading: I found no affiliate programme. A review site lists pricing from $579 one-time; another review gives $879 Professional and $1,979 Institutional. [snippet] (industry) — [thegodfunded](https://thegodfunded.com/en/tools/jigsaw-trading/)
  - Educator-owned platform: Fabio Valentini co-founded **Deepcharts**, an order-flow platform built on Volumetrica, priced from about $45/month. So a well-known order-flow educator also sells the software he teaches with. [snippet] (industry) — [kagels-trading Deepcharts review](https://www.kagels-trading.de/deepcharts-erfahrungen/); [NexusFi listing](https://nexusfi.com/d/indicators/deepcharts-acfv-tech-solutions/)

### Inferences
- Iceberg detection on CME MBO data can be verified mechanically: native icebergs show up as refills in the matching engine. "Detects icebergs accurately", however, is a different claim from "trading on detected icebergs is profitable", and no vendor makes or tests the second claim.
- Liquidation heatmaps are model outputs built on assumed leverage distributions, not observed data. Saying "price hunts liquidity" from these maps rests on an estimated input.
- Recurring, lifetime affiliate commissions of up to 35% are paid on subscriptions. Many "best order-flow platform" reviews and educator recommendations should therefore be treated as sales material unless they state they are not affiliated.

### Gaps
- I did not visit the claims pages for ATAS, Sierra Chart, Exocharts, Quantower, TradingLite, NinjaTrader Order Flow+ or Hyblock. I found no accuracy or performance statistics for any of them.
- I did not find Bookmap's exact commission tiers.

---

## 2. Educators: ICT/SMC, Axia, Trader Dale, Fabio Valentini, crypto order-flow, and how their performance claims are evidenced

### Takeaway
Michael Huddleston (ICT), whose concepts underpin most of the "liquidity hunt / sweep / order block / FVG" vocabulary, has never published a broker-verified or audited track record. The best-evidenced order-flow educator I found, Fabio Valentini, points to trading-competition results (Robbins World Cup). His specific return figures, however, appear mainly in his own marketing or in sites that repeat it, and he co-owns a platform. I found nothing on Axia Futures or Trader Dale performance evidence.

### Cited Findings
- ICT/Huddleston: several sites state he "has never published a verified live track record" or a broker-verified one, and that his results have never been audited by an independent third party. Critics cite a failed 2016 public attempt to grow an account to $1m and a public account failure in 2024. [snippet] Note the sources are biased: Phidias sells prop evaluations, and Backtrex sells backtesting software. (industry/anecdotal) — [Phidias "Is ICT legit"](https://phidiaspropfirm.com/education/is-ict-legit); [Backtrex ICT bio](https://backtrex.com/en/blog/ict-real-name-michael-huddleston); [Forex Peace Army review](https://www.forexpeacearmy.com/forex-reviews/13001/inner-circle-trader-ICT)
- I found no primary evidence of an ICT track record, such as broker statements, an audit or a regulatory filing. A search for ICT entering the Robbins World Cup returned nothing relevant. Gap.
- Fabio Valentini is listed among UAE futures day-trading competitors in the Robbins Cup and World Cup. [snippet] (industry) — [Quantamental Trader Substack](https://quantamentaltrader.substack.com/p/world-cup-trading-championship-and)
- A PickMyTrade blog, which says it is not affiliated with him, repeats claims of "top-three audited finishes" in the Robbins World Cup futures division, including a 218% quarter. [snippet] (industry, secondary) — [PickMyTrade blog](https://blog.pickmytrade.trade/fabio-valentini-pro-scalper-nasdaq-scalping-strategy/). His LinkedIn profile calls the results "audited" (CME Group Equity Cup, World Trading Cup). (educator) — [LinkedIn](https://ae.linkedin.com/in/fabervaale)
- On evidence quality: competitions such as the Robbins Cup rank short-window percentage returns among self-selected entrants, often on small accounts. They show that real money was traded, but a top-3 finish among many entrants is consistent with high variance and selection. I did not check this against official results pages. (inference)
- Commercial SMC/ICT indicator vendors label themselves "backtest-verified, non-repainting" without publishing methodology. Some more honest TradingView scripts say their calibration figures are "IN-SAMPLE, close-to-close, with NO costs or slippage" and "NOT a validated edge". [snippet] (vendor/anecdotal) — [TradingView SMC scripts](https://www.tradingview.com/scripts/fair-value-gap/); [UAlgo SMC script](https://ru.tradingview.com/script/RdfnBPYp-Smart-Money-Concepts-UAlgo)
- Backtrex, a no-code backtest vendor, markets ICT/SMC backtesting with results "in under 30 seconds". Its own "Liquidity Sweep Strategy: 5-Year Backtest" blog reports 1,247 trades on EURUSD/XAUUSD from 2019 to 2024 using sweep, displacement and FVG-retest rules. It gives no stated timeframe or cost model, and the post is vendor marketing. [snippet] (vendor) — [Backtrex sweep backtest](https://backtrex.com/en/blog/liquidity-sweep-strategy-backtest-results); [Backtrex SMC features](https://backtrex.com/en/features/smc)

### Inferences
- The evidence ranges from **none** (ICT: claims, screenshots and live YouTube sessions only) to **competition placings** (Valentini). No educator found offered audited multi-year live accounts. Prop-firm payout screenshots are a common type of evidence in this space, but they are selected and say nothing about the denominator (see section 4).
- Every educator found earns money from courses, software or prop-firm affiliations, so none of them is an independent source.

### Gaps
- I found nothing on the claims or evidence of Axia Futures, Trader Dale, or crypto order-flow educators (for example TradingLite or Hyblock-affiliated educators). Searches did not reach them within the budget.
- I could not verify the official Robbins Cup results for Valentini.

---

## 3. Independent tests of ICT/SMC concepts (beyond IndicatorEdge and StatOasis)

### Takeaway
I found **no peer-reviewed or arXiv study** that tests order blocks, FVGs, liquidity sweeps or BOS/CHoCH as trading rules with out-of-sample data and costs. The available material is open-source indicator code without performance results, vendor "backtests", and one blog citing random-walk base rates. Together they suggest FVGs and "sweeps" occur often in random data, so their existence alone carries little directional information.

### Cited Findings
- **Most-used open-source code:** the Python package `joshyattridge/smart-money-concepts` on GitHub implements ICT concepts: order blocks, liquidity, FVG, swing highs and lows, BOS and CHoCH. Its README documents the indicators but publishes no backtest performance. [snippet] (anecdotal/code) — [GitHub joshyattridge/smart-money-concepts](https://github.com/joshyattridge/smart-money-concepts); fork [DACILAE1777/smart-money-concepts-1](https://github.com/DACILAE1777/smart-money-concepts-1)
- A trade-copier vendor blog states that ICT/SMC "have no demonstrated edge as trading rules". It reports that Crossref searches on 27 September 2026 combining "smart money concepts" with "trading" found no journal article testing them. It also claims that "in a pure random walk such gaps [FVGs] appear on almost a third of bars". [snippet only; domain unreachable, not verified] (industry) — [Thor Trade Copier](https://thortradecopier.com/blog/does-ict-smart-money-concepts-work)
- Another review says the three-candle FVG is "a charting heuristic with no peer-reviewed test" and that order-block and BOS/CHoCH constructs have "no peer-reviewed validation located at all". [snippet] (industry) — [PineConnector "SMC as Testable Rules"](https://www.pineconnector.com/blogs/pico-blog/smc-ict-concepts-as-rules); [XS.com SMC explained](https://www.xs.com/en/test-blog/smc-smart-money-concepts-explained/)
- One snippet mentions a mechanical "FVG-after-sweep" strategy backtested on 2,553,973 one-minute EURUSD bars (2019-01-01 to 2025-12-31). A targeted search could not find the original source, so the result is unverified. Gap.
- Claims that "70–80% of FVGs eventually fill" come from trading blogs with no methodology. [snippet] (anecdotal) — [fxnx](https://fxnx.com/en/blog/smart-money-concepts-work-backtest-evidence); [chartwhisperer](https://chartwhisperer.ca/blog/order-blocks-fair-value-gaps-smart-money-guide)
- **Quasi-academic:** an IJNRD paper (2024, low-tier journal) feeds SMC features into ML trading models and reports that FVG features gained importance in volatile periods. It is not an out-of-sample profitability test of SMC rules. [snippet] (academic, low quality) — [IJNRD2411009](https://www.ijnrd.org/papers/IJNRD2411009.pdf)
- An arXiv search on "smart money" only returned an unrelated Polymarket paper. (academic) — [arXiv 2610.34754](https://arxiv.org/html/2610.34754)

### Inferences
- A rule that "price returns to fill the gap" has a high base rate in any mean-reverting or random series, so high fill rates or win rates are expected even without an edge. This matches the IndicatorEdge result of a high win rate with a negative return.
- The burden of proof has not been met. Apart from IndicatorEdge and StatOasis, the independent evidence is absence of evidence plus base-rate arguments, not a body of negative tests.

### Gaps
- I found no GitHub repository with published walk-forward or out-of-sample results including costs for ICT/SMC rules, no thesis, and no quant-blog test (beyond the earlier two) that I could verify within the budget.

---

## 4. Survivorship and selection bias: prop firms and retail loss statistics

### Takeaway
Topstep's own disclosures, as reported by third parties, show a steep funnel. About 12–17% of paid evaluations pass, about one-third of funded traders ever receive a payout, and under 1% of Express Funded traders reach a live account. Combined estimates put the share of buyers who reach any payout in the low single digits. Industry payout totals in the hundreds of millions are gross, firm-reported figures with no denominator. EU regulators found 74–89% of retail CFD accounts lose money.

### Cited Findings
- **Topstep 2025 disclosure** (via third parties; not read on topstep.com): 16.8% of Trading Combines initiated were completed. 51.8% of *participants* (people, across attempts) reached the Funded Level at least once. 33.3% of funded participants received a payout. 0.71% of Express Funded traders were called up to Live. [snippet] (industry, citing vendor) — [WikiFX Topstep review](https://www.wikifx.com/en/news/details/202609281264561516.html); [Curved Trading Topstep review](https://curvedtrading.com/articles/en/reviews/topstep-review/); [Fortunly pass-rate stats](https://fortunly.com/statistics/prop-firm-challenge-pass-rate-statistics/)
- Topstep's 2024 disclosure: 12.4% of Trading Combines were completed. [snippet] (industry) — [Fortunly](https://fortunly.com/statistics/prop-firm-challenge-pass-rate-statistics/)
- PropScorer reports a 99.26% approval rate for eligible payout requests, but an overall start-to-payout success rate of about 2.8%. It describes the 99% figure as "the last stage of a funnel where most traders have already dropped out". [snippet, translated page, low confidence] (industry) — [PropScorer](https://www.propscorer.com/hi/blog/topstep-payout-claims-vs-reality)
- In late April 2026 Topstep reportedly cut payout caps on new Express Funded accounts (50K Standard path down to about $2,000 from about $5,000). [snippet] (anecdotal) — [NexusFi](https://nexusfi.com/showthread.php?p=911770)
- The Funded Trader's own client data: only about 1 in 20 traders pass prop-firm challenges. This covers a single firm. (industry) — [Finance Magnates](https://www.financemagnates.com/forex/only-1-in-20-traders-pass-prop-firm-challenges-reports-the-funded-trader/)
- Prop Firm Match tracked about $325m in payouts across firms in 2025, with FundedNext at about $108m. These are firm-reported, some gross and some net. (industry) — [Finance Magnates](https://www.financemagnates.com/forex/prop-firm-match-tracked-about-325-million-in-payouts-to-traders-in-2025/). FundedNext reported 2024 revenues above $100m, so payouts are of the same order as fee revenue. (industry) — [TradeInformer](https://tradeinformer.com/broker-news/fundednext-revenues-exceeded-100m-in-2024)
- **ESMA 2018:** national regulators' analyses found that "74-89% of retail accounts typically lose money", with average losses per client of €1,600–€29,000. This led to leverage limits (30:1 to 2:1) and mandatory disclosure of each firm's percentage of losing accounts. (regulator) — [ESMA, 27 Mar 2018](https://www.esma.europa.eu/node/84933); [ESMA final measures](https://www.esma.europa.eu/press-news/esma-news/esma-adopts-final-product-intervention-measures-cfds-and-binary-options)

### Inferences
- Payout screenshots and "$X million paid" banners are the main proof offered by order-flow and ICT educators who teach for prop challenges. They are survivorship evidence: under Topstep's own numbers, roughly 2–6% of evaluation buyers ever reach a payout (16.8% pass × 33.3% paid ≈ 5.6% per Combine, before repeat purchases). Funded accounts are also mostly simulated (0.71% reach Live), so payouts are funded by evaluation fees rather than by market profits.
- With many educators and students buying many evaluations, some payouts are statistically certain even with zero edge. Payout evidence cannot tell skill from luck without the denominator.

### Gaps
- I could not read Topstep's primary disclosure page. Figures are as reported by third parties.
- I found no independent, audited, cross-firm statistic on the share of prop traders paid. I found no AMF or other regulator study specific to retail futures order-flow day traders.

---

## 5. Academic studies of day-trader performance

### Takeaway
The two largest complete-population studies both find that persistent profitable day trading is very rare. In Taiwan fewer than 1% of day traders are predictably profitable after costs. In Brazilian mini-index futures 97% of those who persisted more than 300 days lost money and about 1% earned more than the minimum wage. The Brazil paper explicitly challenges the claims of course providers.

### Cited Findings
- **Chague, De-Losso & Giovannetti (2019/2020), "Day Trading for a Living?"** The study observes *all* individuals who began day trading Brazilian equity (mini-index) futures in 2013–2015. Secondary sources give the sample as 19,646. 97% of those who persisted more than 300 days lost money. Only 1.1% earned more than the Brazilian minimum wage (about $16/day). The abstract concludes it is "virtually impossible for an individual to day trade for a living, contrary to what course providers claim". (academic) — [SSRN 3423101](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3423101); [FGV repository](https://repositorio.fgv.br/items/e87d04fc-4b4c-4a56-ab5a-1c84c1afde1b); [RePEc](https://ideas.repec.org/p/fgv/eesptd/525.html). The 19,646 and 1.1% figures are [snippet], from secondary summaries (Quantpedia, CXO Advisory), and Quantpedia was unreachable — [CXO Advisory](https://www.cxoadvisory.com/investing-expertise/day-trading-a-bust/)
- Caveat: the 97% applies to traders who persisted more than 300 days, not to everyone who tried. (academic) — same sources.
- **Barber, Lee, Liu & Odean, "Do Day Traders Rationally Learn About Their Ability?"** (later titled "Learning, Fatal Attraction, and Fast or Slow"). Taiwan, 1992–2006, complete market data. In aggregate, day traders lose money and the vast majority are unprofitable. Only the roughly 4,000 most profitable from the prior year, "less than 1% of the population", go on to earn reliably positive returns net of fees. Losing traders keep trading at nearly the same rate as profitable ones. (academic) — [Odean, Haas working paper](https://faculty.haas.berkeley.edu/odean/papers/day%20traders/day%20trading%20and%20learning%20110217.pdf); [eScholarship version](https://www.escholarship.org/content/qt7k75v0qx/qt7k75v0qx.pdf?t=ohrd1z); [PUC-Rio "Learning fast or slow"](https://www.econ.puc-rio.br/uploads/adm/seminarios/Learning_fast_or_slow_180606.pdf)
- The companion Barber–Lee–Liu–Odean paper "The Cross-Section of Speculator Skill: Evidence from Day Trading" uses the same Taiwan data to study skill persistence. (academic) — [Haas PDF](https://faculty.haas.berkeley.edu/odean/papers/day%20traders/Day%20Trading%20Skill%20110523.pdf)

### Inferences
- These studies cover discretionary intraday futures and equity traders in general, not order-flow or ICT users specifically. Nothing suggests order-flow tools change the base rate, and no vendor or educator has published evidence that they do.
- The Brazil setting (index futures, 2013–2015, a boom in day-trading courses) is the closest academic analogue to today's futures order-flow and prop-challenge retail cohort.

### Gaps
- I found no study that isolates retail users of order-flow software (Bookmap, ATAS and similar) or of ICT/SMC methods. I also found no crypto-perpetuals equivalent of the Brazil or Taiwan studies within the budget.
