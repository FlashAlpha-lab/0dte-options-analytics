# What Are 0DTE Options?

Zero days to expiration (0DTE) options are options contracts that expire on the same
calendar day they are traded. When you buy or sell a 0DTE option, the contract has
hours — not days or weeks — until it settles.

---

## Why 0DTE Options Have Exploded in Popularity

For most of options market history, the shortest available expiration was weekly.
Then exchanges began listing SPX options with expirations every weekday, and in 2022
SPY joined with Monday/Wednesday/Friday expirations. QQQ followed. The effect on volume
has been dramatic.

By 2023-2024, 0DTE options accounted for roughly 40-50 percent of total SPX options
volume on active trading days. On major macro events (FOMC, CPI, NFP), that fraction
can exceed 60 percent.

The drivers of this growth:

**Low cost of entry.** An ATM 0DTE option on SPY may cost $1-4. A comparable weekly
option costs $8-20. Retail traders and institutions alike use 0DTE to express
short-term views cheaply.

**Defined risk.** Option buyers cannot lose more than the premium paid — their maximum
loss is fixed at entry. This contrasts with short futures or leveraged ETFs where
losses are theoretically unlimited.

**High leverage.** Because the option is cheap, a $1 move in SPY might cause a 100%
or larger move in the option's value. This leverage is far higher than any other
instrument with defined risk.

**Daily settlement.** 0DTE buyers carry no overnight risk. The position is closed —
either profitably or at zero — by the end of the session.

**Institutional hedging.** Large funds use 0DTE puts as same-day tail hedges. Instead
of maintaining a rolling monthly put hedge, they buy protection only on days when
it is needed (e.g., FOMC days).

---

## 0DTE Expiration Schedules

Not every symbol has 0DTE options every day. The current schedule (as of 2024):

| Symbol | 0DTE Days |
|---|---|
| SPX (S&P 500 Index) | Every weekday (Mon, Tue, Wed, Thu, Fri) |
| SPXW (SPX weeklies) | Every weekday |
| SPY (S&P 500 ETF) | Monday, Wednesday, Friday |
| QQQ (Nasdaq-100 ETF) | Monday, Wednesday, Friday |
| IWM (Russell 2000 ETF) | Friday only |
| XSP (Mini-SPX) | Every weekday |

SPX is the most liquid 0DTE market. SPY is popular among retail traders because it
allows smaller position sizes (the underlying is roughly one-tenth of SPX in dollar
terms) and offers better accessibility for accounts under $25,000.

---

## Key Differences from Weekly or Monthly Options

**Theta decay is compressed into hours.** A weekly option decays its remaining premium
over 5 trading days. A 0DTE option decays the same remaining premium in hours. This
makes theta decay extremely rapid and nonlinear — most of the day's decay occurs in
the final 2-3 hours.

**Gamma is extreme near the money.** Gamma measures how quickly delta changes as price
moves. For near-the-money 0DTE options, gamma can be 5-10x higher than an equivalent
7DTE option. This means small price moves produce large delta changes, which in turn
produce large dealer hedging flows.

**Implied volatility reflects today only.** The IV of a 0DTE option captures the
market's expectation of intraday volatility — nothing more. It is not anchored to
longer-term vol estimates. IV can spike dramatically on news and collapse within minutes.

**Pin risk is meaningful.** When large open interest concentrates at a nearby strike,
the gravitational effect from dealer hedging is strong enough to measurably anchor
price near expiration. This pin risk is much more pronounced in 0DTE than in longer
expirations because the hedging response is faster and more concentrated.

---

## Risks of 0DTE Trading

**Total loss is common for buyers.** If the expected move does not occur, a 0DTE option
expires worthless and the buyer loses 100% of premium. This happens frequently.

**Bid/ask spreads are wide in illiquid strikes.** Only the front few strikes around
the money have tight markets. OTM strikes can have $0.05-$0.20 wide spreads on a
$0.10 option — a massive percentage cost.

**Execution risk is high.** 0DTE options can move rapidly. Market orders in volatile
conditions can fill far from the midpoint.

**Assignment risk for spreads.** Short legs of spreads can be assigned when they go
deep in the money near close, especially for cash-settled index options where the
settlement price can differ from the last traded price.

---

## Further Reading

- [0DTE Gamma Exposure and Pin Risk: Intraday Analytics](https://flashalpha.com/articles/0dte-gamma-exposure-pin-risk-intraday-options-analytics)
- [0DTE SPY Complete Intraday Playbook](https://flashalpha.com/articles/0dte-spy-complete-intraday-playbook-same-day-options)
- [Guide to 0DTE Trading Strategies with Real-Time Data](https://flashalpha.com/articles/guide-to-0dte-trading-strategies-real-time-data)
