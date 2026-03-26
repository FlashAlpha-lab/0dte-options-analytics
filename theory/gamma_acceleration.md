# Gamma Acceleration in 0DTE Options

Gamma measures how quickly an option's delta changes as the underlying moves. For 0DTE
(zero days to expiration) options, gamma is dramatically higher than for options with
days or weeks remaining — and it accelerates as the session progresses. This is one of
the most important and least understood aspects of same-day options trading.

---

## The Math Behind Gamma and Time to Expiration

Under Black-Scholes, gamma for an at-the-money option is approximately:

```
Gamma_ATM ≈ 1 / (S * sigma * sqrt(T))
```

where:
- S = underlying price
- sigma = implied volatility (annualized)
- T = time to expiration in years

Since T appears in the denominator under a square root, gamma grows as T shrinks. For
an ATM option, the relationship is:

- T = 30 DTE: Gamma_ATM ≈ 1 / (S * sigma * sqrt(30/252))
- T = 7 DTE:  Gamma_ATM is about sqrt(30/7) ≈ 2.07x higher
- T = 1 DTE:  Gamma_ATM is about sqrt(30/1) ≈ 5.48x higher
- T = 0.1 DTE (about 4 hours): Gamma is sqrt(30/0.1) ≈ 17.3x higher than 30 DTE

This is why a $1 move in SPY can cause enormous option price swings in the final hours
of a 0DTE session. The option's delta changes so rapidly that premium values swing from
near-worthless to near-intrinsic within minutes.

---

## Gamma vs. Strike Distance: Two Regimes

Gamma behaves very differently depending on whether the option is near or far from the
money at the time of expiration:

**Near the money (within 0.5% of spot):**
Gamma is maximized and rising rapidly. A $1 move can change delta by 0.05-0.20 or more.
This creates cascading dealer hedging flows as dealers scramble to rehedge their books.
The feedback loop between price movement and hedging can produce sharp, self-reinforcing
intraday moves.

**Far out of the money (>1.5% from spot):**
Gamma collapses toward zero. These options have very small delta and small gamma — they
are almost binary (worth something or worth nothing). Their hedging contribution is small
until a rapid move brings them closer to the money.

This distribution means that the gamma exposure from 0DTE options is highly concentrated
in a narrow range around the current price. Unlike longer-dated options where gamma is
spread across a wider strike range, 0DTE gamma is a precise, localized force.

---

## Intraday Gamma Acceleration

During a 0DTE session, gamma does not stay constant — it grows as time passes. Consider
an ATM SPY option at 10:00 AM vs. 3:30 PM:

| Time (EST) | Hours Remaining | Relative Gamma (vs. open) |
|---|---|---|
| 9:30 AM    | 6.5 h           | 1.0x (baseline)           |
| 11:00 AM   | 5.0 h           | 1.14x                     |
| 1:00 PM    | 2.5 h           | 1.61x                     |
| 2:30 PM    | 1.0 h           | 2.55x                     |
| 3:30 PM    | 0.17 h          | 6.20x                     |

The final hour sees gamma roughly 6x what it was at the open. This is why 0DTE traders
describe the last 30-60 minutes as "dangerous" — the same dollar move in the underlying
that was manageable at noon can cause catastrophic P&L swings at 3:30.

---

## Dealer Gamma and Intraday Volatility

The sign and magnitude of dealer net gamma determines how dealers respond to price moves
and therefore how intraday volatility behaves.

**Positive gamma regime (dealers are long gamma):**
When price moves up by $1, dealer delta increases (they have more long delta than they
need) and they sell. When price moves down by $1, their delta decreases and they buy.
This is the classic "buy low, sell high" hedging behavior that dampens volatility and
creates range-bound conditions. Intraday realized vol tends to be lower than implied vol.

**Negative gamma regime (dealers are short gamma):**
When price moves up, dealers need to buy more to rehedge. When price moves down, they
need to sell more. This "buy high, sell low" behavior amplifies whatever directional
move is occurring. Intraday realized vol tends to be higher than implied vol.

0DTE options' massive gamma contribution means that even a small shift in open interest
composition — e.g., a large block of calls sold to dealers at a specific strike — can
flip the net gamma regime from positive to negative for that strike cluster.

---

## Gamma Explosion Near Expiration: Practical Implications

**For premium buyers:** Options bought ATM in the morning can double or triple in value
on a moderate intraday move in the afternoon, purely due to gamma acceleration. The
option is more sensitive to price movement as time passes. This favors "wait and hold"
strategies for call/put buyers if the directional thesis is correct.

**For premium sellers:** The same gamma acceleration that benefits buyers destroys sellers.
A short 0DTE straddle sold at noon with $2 premium can see that position go deeply
negative on a $3 move at 3:00 PM because each dollar of underlying move is worth far
more to the option than it was at noon. This is why 0DTE sellers typically target the
final 60-90 minutes of the session when theta decay is most powerful and gamma
acceleration works against the option buyer.

**For scalpers:** Gamma scalping (buying a straddle and delta-hedging it) generates
profits proportional to the difference between realized vol and implied vol. With 0DTE
gamma accelerating, the P&L from each gamma scalp hedge increases through the day.
Scalpers prefer high-gamma environments — 0DTE options are among the highest-gamma
instruments available.

---

## The Gamma Flip: Where the Regime Changes

The gamma flip is the spot price where net dealer GEX transitions from positive to
negative. It represents the boundary between the dampening regime (above) and the
amplifying regime (below). The FlashAlpha API computes this in real time using live
open interest data.

The gamma flip is important because:

- Breakouts above the flip back into positive gamma territory tend to fail — dealers
  sell into the move.
- Breakouts below the flip into negative gamma territory tend to accelerate — dealers
  sell with the move.
- The flip level itself is often a consolidation zone where gamma from both sides
  partially cancel.

---

## Further Reading

- [0DTE Gamma Exposure and Pin Risk: Intraday Analytics](https://flashalpha.com/articles/0dte-gamma-exposure-pin-risk-intraday-options-analytics)
- [Zero-DTE Options API: Real-Time 0DTE Analytics](https://flashalpha.com/articles/zero-dte-options-api-real-time-0dte-analytics)
- [Zero-DTE API: Complete Guide to the 0DTE Analytics Endpoint](https://flashalpha.com/articles/zero-dte-api-complete-guide-0dte-analytics-endpoint)
