# Market-neutral / non-directional strategy families in crypto derivatives (BTC, SUI, Binance), evidence 2019–2026

Research access note. arxiv.org, bis.org, bitmex.com and andrew.cmu.edu could not be reached from this session (DNS blocked). Every figure from those domains, and most of the other figures here, comes from **search-engine snippets or summaries, not the full text**. These are marked **[snippet]**. Verify them against the PDFs before quoting precise numbers. Source-type tags: [ACADEMIC], [INDUSTRY], [VENDOR], [PRACTITIONER], [EXCHANGE].

---

## Q1. Funding / basis carry (spot long + perp short; cash-and-carry on dated futures)

### Takeaway
The academic literature agrees that crypto carry was historically very large. It averaged above 10% a year, with in-sample gross Sharpe ratios in the mid-single digits up to about 10 for 2020–2023 samples. Even with retail taker costs, Sharpe was about 1.8 on BTC.

Carry has also compressed sharply:
- BTC funding averaged about 11% in 2024, 4.9% in 2025 and about 2.2% in 2026 to August, per Ethena's figures.
- A 2025 survey reports that BTC carry Sharpe fell from about 6.5 (2020–2025) to about 4 (2024 onward) and turned negative in 2025. This comes from a snippet only.
- High carry predicts crashes. Its tail risks are operational (liquidation of the short leg, auto-deleveraging (ADL), exchange failure, stablecoin depeg) rather than market beta.

### Cited Findings

**Academic**
- **He, Manela, Ross & von Wachter, "Fundamentals of Perpetual Futures" (arXiv 2212.06888, v1 2022 to v6 Aug 2024) [ACADEMIC, snippet].**
  - Derives no-arbitrage perp prices. Cost-adjusted no-arbitrage bounds use "random-maturity arbitrage".
  - Deviations of crypto perps from no-arbitrage prices are "considerably larger than those documented in traditional currency markets".
  - The v5 text reports that the random-maturity arbitrage strategy on BTC perps has a **Sharpe of 1.8 "under high trading costs typical of retail investors"** and **up to 3.5 for highly-active market makers who pay no fees**.
  - The later abstract says the strategy yields "large Sharpe ratios even for investors paying the highest trading costs on Binance".
  - Table 6 gives zero-cost Sharpe ratios for 5 cryptocurrencies, all "high" (values not seen).
  - The exact sample period and cost assumptions were not visible in the snippets. These are in-sample backtests.
  - Ackerer, Hugonnier & Jermann note that an early-version pricing formula was incorrect, so use the latest version.
  - Sources: [arXiv abs v6](https://arxiv.org/abs/2212.06888v6); [arXiv pdf](https://arxiv.org/pdf/2212.06888); [AHJ (EPFL)](https://www.epfl.ch/labs/sfi-jh/wp-content/uploads/2025/03/AHJ-main-12.pdf)
- **Christin, Routledge, Soska & Zetlin-Jones, "The Crypto Carry Trade" (CMU working paper, 2022) [ACADEMIC, snippet].**
  - The abstract reports that the carry trade is "unusually profitable", with **in-sample annual Sharpe ratios in the range of 7 to 10** for the spot-long / perp-short funding trade.
  - A secondary summary attributes figures of about 23.55 (Drift) and 6.50 (ApolloX) to a later version, against 2.89 for HODL. **These are unverified**, and DEX venues are not comparable to Binance.
  - Sources: [CMU PDF](https://www.andrew.cmu.edu/user/azj/files/CarryTrade.v1.0.pdf); [TradingStrategy.ai summary [VENDOR]](https://tradingstrategy.ai/docs/learn/carry-trade.html)
- **Schmeling, Schrimpf & Todorov, "Crypto carry", BIS Working Paper 1087 (Apr 2023), later CEPR DP20719 (2025) [ACADEMIC, snippet].**
  - Carry is defined as the futures–spot basis, i.e. the return on cash-and-carry.
  - Carry **averages above 10% p.a.**, which is "much larger" than carry in equities, fixed income, FX or commodities.
  - Interest-rate differentials explain little of it. Variation comes from convenience yields and trend-chasing demand for leverage.
  - **High carry predicts future price crashes**, and rises in carry coincide with a higher price of crash insurance.
  - There is some evidence of segmentation between crypto exchanges and traditional finance.
  - Sources: [BIS WP 1087](https://www.bis.org/publ/work1087.pdf); [CEPR DP20719](https://cepr.org/publications/dp20719); [Mondo Visione summary](https://mondovisione.com/news/bis-crypto-carry-202344/)
- **Borri, Liu, Tsyvinski & Wu, "Cryptocurrency as an Investable Asset Class: Coming of Age" (arXiv 2510.14435, Oct 2025; revised Feb 2026) [ACADEMIC, snippet].**
  - Builds BTC carry from 8-hour perp, funding and spot-index data, following Schmeling et al.
  - A search snippet attributed to this survey states: **"over the full sample, 2020 to 2025, the annualized Sharpe ratio of the cryptocurrency carry is 6.45. Beginning in 2024, the Sharpe ratio falls to 4.06, and it turns negative in 2025."**
  - A second search could **not** re-locate these numbers in the retrieved text, so treat them as plausible but unverified. They may come from v1 only.
  - Sources: [arXiv 2510.14435](https://arxiv.org/pdf/2510.14435); [Quantpedia summary](https://quantpedia.com/cryptocurrency-as-an-investable-asset-class-10-lessons/)

**Industry and vendor data on compression, 2024–2026**
- **BTC funding averages, as reported by Ethena [VENDOR], relayed by FXStreet and CoinSpot [INDUSTRY].** These are the most consistently reported annual figures. I found no independent primary source for them.
  - **2024: about 11%**
  - **2025: 4.9%**
  - **2026 through 11 Aug: 2.2%**
  - Sources: [FXStreet, Aug 2026](https://www.fxstreet.com/cryptocurrencies/news/ethena-looks-beyond-crypto-to-squeeze-yield-from-booming-equity-perpetuals-202608281313); [CoinSpot](https://coinspot.io/en/company/ethena-perpetual-equity-contracts-ethena-seeks-new-yield-for-usde-in-perpetual-equity-contracts/)
- **Ethena risk docs [VENDOR]:** BTC/ETH funding averaged about **7.8–9% annualised over roughly 3 years, including the 2022 bear market**. — [Ethena docs, funding risk](https://docs.ethena.fi/protocol-overview/risks/funding-risk)
- **Flowdesk [INDUSTRY]:** the annualised CME front-month BTC basis **stayed below 9% through 2025** despite near-record open interest. It **briefly turned negative in early December 2025**, tied to a large unwind of basis positions. — [Flowdesk, Crypto Credit Markets](https://flowdesk.co/updates/blogs/6f3b8c1a2e9d4f7c8a5b2e91/)
- **Blockworks [INDUSTRY]:** sUSDe yields fell from peaks above 20% to about **3.5–4.5%** as institutional capital competed for the basis trade. Ethena has pivoted to equity and commodity perp basis. — [Blockworks, The Breakdown](https://blockworks.com/newsletter/the-breakdown/issue/post_999b16ee-0fe0-4631-a1d0-2aa15a1d18a7)
- **sUSDe yield history [VENDOR/aggregator, low quality, conflicting]:**
  - Realised APY ranged about 4–30% across 2024–25, with "most periods 8–18%".
  - Average since Jan 2024 was about 10.9%.
  - **The August 2024 funding inversion cut APY from about 19% to about 4% in 11 days.**
  - Aavescan's 30-day sUSDe supply APY fell from **7.44% (1 Sep 2025) to 3.74% (1 Mar 2026)**. This is the Aave market rate, not Ethena's own yield.
  - Sources: [eco.com](https://eco.com/support/en/articles/15254002-ethena-usde-and-susde-2026-delta-neutral-yield); [Aavescan](https://aavescan.com/rates/ethena-susde); [stablecoininsider Q1 2026](https://stablecoininsider.org/ethena-usde-q1-2026-report/)
- **Point-in-time snapshot:** the average BTC perp funding across 6 exchanges was **−0.7% annualised on 25 Sep 2026**. — [DeFi Rate snapshot [VENDOR]](https://defirate.com/perp/snapshot/2026-09-25T1925/)
- **BitMEX Q3-2025 derivatives report, "The Anchor and the Ceiling" [EXCHANGE]:** it argues that funding is structurally anchored at the baseline interest rate, capped by arbitrage capital. The content could not be fetched. — [BitMEX blog](https://www.bitmex.com/blog/2025q3-derivatives-report)
- **Galaxy Research [INDUSTRY]:** BTC futures basis and funding "remain relatively muted amidst bullish price action" in the post-ETF period. Only the headline was seen. — [Galaxy](https://www.galaxy.com/insights/perspectives/bitcoin-futures-basis-and-funding-rates-remain-relatively-muted-amidst)

**Altcoins (SUI)**
- No published 2025 average SUI funding rate was found. CoinGlass and Sharpe.ai provide per-exchange SUI funding histories, but the snippets did not include the figures. — [CoinGlass SUI](https://www.coinglass.com/FundingRate/SUI); [Sharpe.ai SUI [VENDOR]](https://www.sharpe.ai/funding-rates/sui)
- Sharpe.ai [VENDOR] makes two claims:
  - Binance and Bybit retail venues "often over-extend" relative to OKX and Deribit.
  - Persistent 8-hour rates above 0.03% (about 33% APR) "often precede corrections". This is a heuristic, not a measured result.
  - Source: [Sharpe.ai](https://www.sharpe.ai/funding-rates/sui)

**Tail events**
- **October 10–11, 2025 crash [ACADEMIC + INDUSTRY]:**
  - About **$19bn** was liquidated.
  - Hyperliquid's ADL closed about **$2.1bn of positions in 12 minutes**. An academic estimate puts the winning-trader PnL taken by ADL at about $660m (simulated) to $2.1bn (realised). Hyperliquid claims ADL net-benefited shorts.
  - **USDe briefly depegged to about $0.65 on Binance only**, and Binance reportedly spent about $188m covering bad debt.
  - Before the crash, longs were paying "70–80 bp per day" in funding. That figure is from one source.
  - I found no source that quantifies losses specifically for delta-neutral or basis traders.
  - Sources: [arXiv 2512.01112, Autodeleveraging](https://arxiv.org/html/2512.01112v2); [The Defiant autopsy](https://thedefiant.io/newsletter/defi-daily/the-ultimate-10-10-crash-autopsy); [Datawallet](https://www.datawallet.com/crypto/october-10-crypto-crash-explained); [insights4vc](https://insights4vc.substack.com/p/inside-the-19b-flash-crash)
- **Negative-funding regime:** when funding is negative, the short legs pay, and Ethena-style yield goes to zero or below. Ethena relies on a reserve fund for this; one source reports about $61m against about $5.6bn of supply in March 2026, roughly 1.1%. — [Ethena docs](https://docs.ethena.fi/protocol-overview/risks/funding-risk); [eco.com](https://eco.com/support/en/articles/15002228-ethena-susde-vs-usde-yield-mechanism-explained)

### Inferences

**Why the premium fell.** The pre-2024 papers measured a premium that has since been arbitraged by ETFs plus CME basis desks and by delta-neutral protocols (USDe reached multi-$bn supply). The decline in the 2024 → 2025 → 2026 averages (about 11 → 4.9 → 2.2%) is consistent with "the ceiling" being lowered by arbitrage capital. In-sample Sharpe figures of 7–10 from 2020–2022 samples should **not** be extrapolated.

**What the literature predicts for the user's pre-registered test.** The test is spot long / perp short on BTC and SUI, 2023–2026, taker fees, 2x perp leverage. The pass bar is ≥ 4% a year, Sharpe ≥ 1 and drawdown ≤ 5%.
- **Capital efficiency.** With spot fully paid and the perp at 2x, capital is about 1.5× the notional. The return on capital is therefore about **0.67 × the funding rate**. If idle collateral earns nothing:
  - 2024 (11%): about 7.3% on capital
  - 2025 (4.9%): about 3.3%
  - 2026 YTD (2.2%): about 1.5%
- **BTC always-on.**
  - Likely to **pass ≥ 4% only if the 2023–2024 years carry the average.** It likely **fails in 2025–2026 sub-periods**.
  - Sharpe could stay at or above 1 in years with positive average funding, because spot-perp mark-to-market noise is small. Sharpe could be ≤ 0 in 2026 if the survey's "negative in 2025" claim holds.
  - A drawdown ≤ 5% is plausible for BTC if the short leg is never liquidated. With a 2x short margined separately from the spot, a rally of about +40–50% would liquidate the perp unless the position is rebalanced. This is an engineering risk, not a market risk.
- **Switched (3-day average funding > 5/10/20%).**
  - It cuts negative-funding bleed.
  - Each switch costs roughly **0.3% of notional** at taker fees: entering and exiting both legs. That assumes about 0.05% perp taker and about 0.1% spot taker; the spot fee was not verified here.
  - High thresholds (20%) make the strategy mostly inactive in 2025–26. Returns then depend on a few bursts, and **the BIS crash-prediction result means those high-carry windows are the ones that precede crashes**, when the funding spike can reverse within days.
  - Expect the threshold variants to have a higher Sharpe but a lower absolute return than always-on. It is likely to **fail the 4% bar after 2024**.
- **SUI.**
  - Funding is likely higher on average than BTC during bull phases and negative more often in drawdowns. Neither claim has a cited figure.
  - The price path is far more volatile, so the risk of liquidating a 2x short leg and of a basis gap (perp vs spot during crashes, as on 10/10) is materially higher.
  - Drawdown ≤ 5% is the criterion most at risk.
  - Exchange-specific events (the USDe depeg on Binance only) show that collateral and mark-price failures are venue-specific.
- **Realistic 2026 expectation for retail BTC funding carry: about 1–4% a year on capital.** That is at or below T-bill/stablecoin-lending yields. Mid-cap alts could add a few percentage points opportunistically, at much higher tail risk.

### Gaps
- Exact sample periods and cost assumptions behind He et al.'s 1.8 and 3.5 Sharpe ratios (arXiv was blocked).
- Exact Christin et al. sample, drawdowns and crash episodes (the CMU PDF was blocked).
- Exact BIS figures per asset (the PDF was blocked).
- No independent (non-Ethena) source for the 2024/2025/2026 annual average BTC funding.
- No sourced 2025–2026 SUI funding average. It should be computed from Binance `fundingRate` history.
- No source quantifying delta-neutral or basis P&L on 10 Oct 2025.
- I did not verify Binance's funding formula parameters (default interest component, about 0.01% per 8h, i.e. about 10.95% p.a. when the premium is near zero; clamp; 4-hour intervals on many alts). They should be checked in Binance's funding FAQ. This matters because a positive floor near 11% a year is the "anchor" that has historically made always-on BTC carry positive.

---

## Q2. Volatility selling (options / variance risk premium)

### Takeaway
A bitcoin variance risk premium (VRP) exists and is larger than the S&P 500's. However, there is **no peer-reviewed, out-of-sample, net-of-cost Sharpe for systematic BTC vol selling** in the material I found. Practitioner backtests on Deribit show double-digit APRs with drawdowns of roughly 9–27%. Short vol is not market-neutral in crashes, and Deribit access is restricted for many retail jurisdictions.

### Cited Findings
- **Alexander & Imeraj (2020), "The Bitcoin VIX and its Variance Risk Premium", *Journal of Alternative Investments* [ACADEMIC, snippet].**
  - Builds Deribit-based implied-volatility indices from 1 week to 3 months using a CBOE-style variance-swap formula. Uses 15-minute data, **Mar 2019–Mar 2020**.
  - Documents the BTC VRP.
  - No strategy Sharpe was visible.
  - Source: [Sussex repository](https://sro.sussex.ac.uk/id/eprint/91094/)
- **"Risk Premia in the Bitcoin Market" (arXiv 2410.15195, 2024) [ACADEMIC, snippet].** BTC has a higher VRP than the S&P 500. The "Sharpe about 0.8" in that paper refers to BTC itself, not to vol selling. — [arXiv 2410.15195](https://arxiv.org/html/2410.15195v2)
- **Harbourfront Quant summary [PRACTITIONER]:** VRP is about 0.17 in low-volatility regimes and about 0.12 in high-volatility regimes. — [Substack](https://harbourfrontquant.substack.com/p/return-and-variance-risk-premia-in)
- **Deribit Insights backtests [EXCHANGE/PRACTITIONER, gross or partially costed, in-sample]:**
  - Daily selling of 2-day, 0.35-delta BTC strangles: **APR 23.8%, maximum drawdown 26.5%**. The author calls it "profitable on average… not optimal".
  - Another backtest, **Jan–Aug 2024** (35 trades): +0.1395 BTC net, **maximum drawdown 8.8%**. The author warns that the drawdown is "likely an underestimate".
  - Sources: [Deribit Insights p=99807](https://insights.deribit.com/?p=99807); [p=88953](https://insights.deribit.com/?p=88953)
- **Block Scholes backtest-tool example [VENDOR]:** a short-vol carry strategy showing **Sharpe −0.91, drawdown −18.4%**. This is an illustrative window only. — [Block Scholes](https://console.blockscholes.com/products/strategy-backtest)
- **Panoptic [VENDOR]:** a BTC short straddle over about 7 weeks in spring 2024 returned +10.32% annualised. The sample is too short to be meaningful. — [Panoptic](https://panoptic.xyz/research/low-volatility-panoptic-insights)
- **Practitioner flow [INDUSTRY]:** BTC call-writing came "back in vogue as cash-and-carry loses shine". This suggests that capital rotating out of basis compresses the VRP too. — [Yahoo/CoinDesk](https://malaysia.news.yahoo.com/bitcoin-call-writing-back-vogue-093618974.html)

### Inferences
- Short vol has the classic negatively skewed payoff: steady premium, then gap losses during crashes such as Mar 2020, May 2021, Nov 2022 and Oct 2025. A 5% drawdown cap is incompatible with naked short vol. Defined-risk structures (iron condors, put spreads) cut the premium heavily.
- Retail implementability is limited.
  - Binance has European options and "Dual Investment" (packaged short options). These are not covered by evidence here.
  - Deribit is unavailable to residents of several jurisdictions. This is general knowledge and was not verified in this session.
  - Freqtrade does not trade options.

### Gaps
- No peer-reviewed, out-of-sample, net-of-cost BTC short-variance or short-straddle Sharpe for 2019–2026 was found.
- No evidence was found on SUI options. Liquidity is negligible or absent.

---

## Q3. Market making

### Takeaway
Market making at retail latency and standard Binance maker fees (0.02%) is **negative after fees in every documented Binance backtest found**. Breaking even needs maker rebates, which are only available at high VIP or market-maker-programme tiers.

### Cited Findings
- **Earlier findings in this project** (`research_notes/BTC SUI futures orderflow edges/orderflow_book_imbalance.md`, Q5):
  - arXiv 2502.18625 ("Market Maker's Dilemma"): naive and imbalance-based maker variants are all negative net of fees.
  - A Binance L2 practitioner backtest finds passive quotes lose about 1.2 bp to adverse selection, so about a 1.2 bp rebate is needed. Cutting latency from 200 ms to 5 ms barely helps.
  - A Binance XRPUSDT tick backtester shows −6.9 bp per round trip, and still −2.5 bp with a 1 bp rebate.
  - The hftbacktest tutorial assumes a −0.005% rebate, "the highest market maker rebate available on Binance Futures".
  - Sources: [arXiv 2502.18625](https://arxiv.org/pdf/2502.18625); [SAIndustries/LOB-Market-Making](https://github.com/SAIndustries/LOB-Market-Making); [sgzju/orderflow-alpha-backtester](https://github.com/sgzju/orderflow-alpha-backtester); [hftbacktest docs](https://hftbacktest.readthedocs.io/en/latest/tutorials/Market%20Making%20with%20Alpha%20-%20Order%20Book%20Imbalance.html)
- **Binance USDⓈ-M fees [EXCHANGE via aggregators]:**
  - The regular tier (under $15m 30-day volume, or under 25 BNB) pays **0.02% maker and 0.05% taker**. Paying in BNB gives about 10% off, so about 0.045% taker.
  - VIP 9 taker is about 0.017%.
  - USDC-M is quoted at **0.00% maker / 0.04% taker**. That is from one source and conflicts with others, so verify it.
  - Sources: [Binance support 360033544231](https://www.binance.com/es/support/articles/360033544231); [CryptoPotato](https://cryptopotato.com/binance-fees/); [Bitsgap](https://bitsgap.com/blog/binance-trading-fees-explained-what-it-costs)

### Inferences
- A **0% maker fee on USDC-M perps**, if current, would remove the fee hurdle but **not** the adverse-selection loss of about 1–7 bp. Market making remains unattractive for a retail account.
- Maker execution is still useful as a cost reducer for carry entries and exits: it halves or eliminates the perp-leg fee.

### Gaps
- No verified Binance page with the current 2026 VIP and market-maker-programme rebate schedule.

---

## Q4. Statistical arbitrage, pairs trading, cross-exchange and triangular arbitrage

### Takeaway
Cross-exchange arbitrage has largely disappeared since April 2018. Crypto pairs trading is mostly unprofitable after realistic costs, especially on intraday or hourly data. The occasional exception is daily cointegration, which is highly sensitive to parameters. There is no robust out-of-sample evidence of a net edge for retail.

### Cited Findings
- **Crépellière, Pelster & Zeisberger (2023), "Arbitrage in the market for cryptocurrencies", *Journal of Financial Markets* 64 [ACADEMIC].** Cross-exchange price deviations "decreased greatly from April 2018 onward" and have "almost disappeared". Exploiting them is "barely feasible", and the decline is linked to informed trading. — [Paderborn WP](https://wiwi.uni-paderborn.de/fileadmin-wiwi/cetar/TAF_Working_Paper_Series/TAF_WP_067_CrepellierePelsterZeisberger2022_rev.pdf); [RIS record](https://ris.uni-paderborn.de/record/34449)
- **IEEE Access (2020) [ACADEMIC]:** distance and cointegration pairs on 26 liquid Binance coins at 5-minute, 1-hour and daily frequencies **underperform benchmarks**. — [IEEE 9200323](https://ieeexplore.ieee.org/document/9200323)
- **Charles University thesis (Binance, 2018 data) [ACADEMIC, thesis]:** "mostly unprofitable under transaction costs". It reports more than 5% a month "under ideal conditions", with real-world feasibility unclear. — [CUNI](https://dspace.cuni.cz/handle/20.500.11956/109634)
- **University of Turku thesis [ACADEMIC, thesis]:** after costs, **only cointegration on daily data was profitable**. All methods were loss-making on hourly data. — [UTUPub](https://www.utupub.fi/handle/11111/24573)
- **QFE 2026 copula study [ACADEMIC]:** at 0.08% round-trip cost, market-neutral copula strategies had low risk but **negative net returns**. It cites Do & Faff's finding of declining but significant returns in equities. — [AIMS QFE 2026](https://www.aimspress.com/aimspress-data/qfe/2026/2/PDF/QFE-10-02-016.pdf)
- **Dynamic cointegration paper (arXiv 2109.10662) [ACADEMIC]:** criticises earlier distance-method studies for assuming zero costs. — [ar5iv](https://ar5iv.labs.arxiv.org/html/2109.10662)
- **Funding-rate spread across venues [PRACTITIONER/VENDOR]:** cross-exchange funding arbitrage is "often more about overall position cost". Funding can flip, and fees and slippage must be covered. — [CoinGlass learn](https://www.coinglass.com/ko/learn/fr-arbitrage-en); [Sharpe.ai guide](https://www.sharpe.ai/arbitrage/guide/funding-rate-arbitrage)

### Inferences
- Triangular and cross-exchange price arbitrage is HFT territory and not viable for retail.
- Cross-exchange **funding** arbitrage (long the perp on the low-funding venue, short on the high-funding venue) avoids spot but doubles the counterparty exposure and needs collateral on two venues. No independent return evidence was found.

### Gaps
- No peer-reviewed study of crypto pairs trading or stat-arb with 2023–2026 out-of-sample data and Binance taker fees was found.
- No academic estimate of cross-exchange funding-arbitrage returns was found.

---

## Q5. Overall ranking, 2026 expected return, and implementability (Freqtrade, Hummingbot, exchange products)

### Takeaway
**Funding/basis carry on BTC has the strongest independent, after-cost evidence** of any non-directional family: He et al. report a Sharpe of 1.8 at retail costs, and BIS and Christin et al. also document it. But the evidence is pre-2024 and in-sample, and the premium has since compressed to about 2–5% a year in funding terms. A realistic 2026 expectation for a small retail BTC carry book is **about 1–4% a year on capital**, with low volatility but operational tail risk. Vol selling, market making and pairs trading have weaker or negative after-cost retail evidence.

Freqtrade cannot natively run a hedged spot plus perp pair. Hummingbot ships cross-exchange funding-arbitrage scripts, which are documented only in release notes and with known bugs. Ethena's sUSDe is the "productised" version, currently yielding about 3.5–5%, with smart-contract and depeg risk.

### Cited Findings
- **He et al. (2022–2024) [ACADEMIC, snippet]:** BTC perp arbitrage Sharpe of **1.8 at retail cost** and 3.5 at zero fees, in-sample. This is the best after-cost academic number found. — [arXiv](https://arxiv.org/pdf/2212.06888)
- **Borri et al. (2025) [ACADEMIC, snippet, unverified]:** carry Sharpe **6.45 over 2020–25, 4.06 from 2024, negative in 2025**. — [arXiv 2510.14435](https://arxiv.org/pdf/2510.14435)
- **Ethena [VENDOR]:** BTC funding was 11% (2024), 4.9% (2025) and 2.2% (2026 to August). — [FXStreet](https://www.fxstreet.com/cryptocurrencies/news/ethena-looks-beyond-crypto-to-squeeze-yield-from-booming-equity-perpetuals-202608281313)
- **Hummingbot [PRACTITIONER/OSS]:**
  - Funding-rate arbitrage arrived in **v1.27** as a *sample script* that "scans for differentials between funding rates across perpetual exchanges". It is cross-exchange perp vs perp, not spot vs perp.
  - GitHub issues from May 2024 report errors in the funding-arb script ("unexpected error running clock tick").
  - Hummingbot's V2 "arbitrage executor" is documented separately.
  - Sources: [Hummingbot v1.27 release notes](https://hummingbot.org/release-notes/1.27.0); [Arbitrage executor docs](https://hummingbot.org/strategies/v2-strategies/executors/arbitrage-executor/); [GitHub issues](https://fr.github.com/hummingbot/hummingbot/issues)
- **Binance position modes [EXCHANGE, connector docs]:** One-way mode uses positionSide=BOTH, and Hedge mode requires LONG or SHORT. The setting is **account-wide across all symbols**. — [binance-futures-connector-python](https://github.com/binance/binance-futures-connector-python/blob/main/binance/um_futures/account.py)
- **Freqtrade:** the search did not return the official Freqtrade futures docs, so no citation is available here. See Gaps.

### Inferences
- **Ranking by after-cost evidence quality for a small retail account:**
  1. BTC funding carry: positive but compressed.
  2. Opportunistic alt funding carry: higher yield, much higher tail risk, little independent evidence.
  3. Defined-risk BTC vol selling: positive VRP, no out-of-sample after-cost evidence, skewed losses.
  4. Pairs and stat-arb: mostly negative after costs.
  5. Retail market making: negative without rebates.
  6. Cross-exchange and triangular price arbitrage: gone since 2018.
- **Implementation options for spot plus perp carry:**
  - Two Freqtrade instances, one spot long and one futures short. They are not atomically linked, so the user must handle leg risk and rebalancing externally.
  - Custom scripts using CCXT.
  - Hummingbot V2 controllers or executors.
  - Exchange-native products such as Binance's Portfolio Margin or "Arbitrage Bot". These are not verified here.
  - Holding sUSDe outright, which outsources execution but adds protocol, custody and depeg risk (USDe hit $0.65 on Binance on 10 Oct 2025).
- **Note on comparisons:** the 4.9% (2025) funding figure is roughly equal to or below USD T-bill or stablecoin-lending yields over the same period. A carry book that leaves the USDT perp margin idle is therefore likely to *underperform cash*, on a risk-adjusted basis, after operational risk.

### Gaps
- I could not retrieve Freqtrade's official documentation stating it lacks native hedged spot plus perp support. That limitation is from the caller's brief and my general knowledge of Freqtrade's one-pair, one-trade, one-trading-mode-per-bot design. The likely docs page is freqtrade.io/en/stable/leverage/.
- I could not fetch the official Hummingbot funding-arb doc page or its stated caveats.
- Binance exchange-native arbitrage or "Smart Arbitrage" products and their historical yields were not researched.
