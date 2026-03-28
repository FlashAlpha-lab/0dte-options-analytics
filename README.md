# 0DTE Options Analytics — Python Examples

[![CI](https://github.com/FlashAlpha-lab/0dte-options-analytics/actions/workflows/ci.yml/badge.svg)](https://github.com/FlashAlpha-lab/0dte-options-analytics/actions/workflows/ci.yml)

Real-time intraday analytics for zero days to expiration (0DTE) options using the
[FlashAlpha API](https://flashalpha.com). This repository contains working Python
examples, theory explainers, and test suites covering 0DTE gamma exposure, pin risk,
expected move, dealer hedging flows, theta decay, and trading strategies.

**Keywords:** 0dte options python, 0dte pin risk, 0dte gamma exposure, zero dte options
analytics, 0dte trading strategies python, 0dte expected move, same day options.

---

## What Are 0DTE Options?

Zero days to expiration (0DTE) options expire on the same calendar day they are traded.
SPY and QQQ now have options expiring every Monday, Wednesday, and Friday. SPX has
options expiring every weekday. This means traders can buy or sell options that expire
within hours — sometimes within minutes — of placing the trade.

0DTE options have grown from a niche instrument into roughly 40-50 percent of total SPX
options volume on active days. Their explosive growth is driven by:

- **Low premium cost** — a short-dated ATM option may cost $1-3 vs. $10-20 for a weekly
- **Defined risk** — buyers cannot lose more than the premium paid
- **High gamma** — small moves in the underlying produce large moves in the option price
- **Daily settlement** — no overnight risk for option buyers

Because 0DTE options have such short lifetimes, their behavior is dominated by gamma
and theta in ways that longer-dated options are not. Understanding these mechanics is
essential before trading them.

---

## Gamma Exposure Intraday

Gamma exposure (GEX) measures how much dealers must buy or sell the underlying as price
moves. When dealers are short gamma (net negative GEX), they must buy as price rises and
sell as price falls — amplifying moves. When dealers are long gamma (net positive GEX),
they do the opposite — dampening moves and creating range-bound conditions.

0DTE options contribute disproportionately to intraday GEX because gamma is highest
for near-the-money options approaching expiration. A 0DTE ATM option can have 5-10x the
gamma of an equivalent 7DTE option at the same strike. This means dealer hedging from
0DTE positions creates strong gravitational forces on price throughout the day.

The **gamma flip** is the price level where net dealer GEX transitions from positive to
negative. Above the flip, dealers are typically long gamma and dampen volatility. Below
the flip, dealers are short gamma and amplify it.

---

## Pin Risk Mechanics

Pin risk describes the tendency of an underlying to "pin" to a heavily concentrated
open interest (OI) strike near expiration. The mechanism works as follows:

1. Large OI builds at a specific strike — e.g., 500,000 contracts at SPY 595 calls
2. As expiration approaches, dealers who are short those calls hold negative delta at
   the strike (they must buy SPY to hedge when SPY is above 595, sell when below)
3. This creates a zone of support just below 595 (dealers buy) and resistance just
   above (dealers sell), pulling price toward the strike like a magnet

Pin risk is highest when:
- A single strike holds a large share of total 0DTE OI
- The underlying is within 0.5% of that strike
- Less than 2 hours remain until expiration

The FlashAlpha API returns a `pin_score` (0-100) measuring the strength of this effect,
a `magnet_strike` identifying the most likely pin level, and `max_pain` identifying the
strike where the total value of expiring options is minimized.

---

## Expected Move Calculation

The expected move for a 0DTE option is derived from the ATM straddle price. If an ATM
straddle (call + put at the same strike) costs $3.50, the market implies a one standard
deviation range of approximately ±$3.50 from the current price by end of day.

More precisely, the 1SD expected move = straddle price × 0.6827 (the probability that
a normally distributed variable falls within ±1 SD). In practice, the straddle price
itself is used as the ±1SD range because it is the simplest and most liquid estimate.

As the day progresses, the remaining expected move shrinks with the square root of
remaining time. If 4 hours remain out of a 6.5-hour session, roughly 78% of the day's
expected move remains (sqrt(4/6.5) ≈ 0.78). The FlashAlpha API computes this
`remaining_1sd` value in real time, allowing traders to compare current displacement
to the remaining implied range.

---

## Dealer Hedging Flows

Dealers (market makers) who sell options must delta-hedge their books continuously. As
price moves, their delta changes and they must transact in the underlying to stay neutral.
This creates predictable flows:

- At +0.5% from spot: dealers long gamma must sell, dealers short gamma must sell more
- At -0.5% from spot: dealers long gamma must buy, dealers short gamma must buy less

The FlashAlpha API estimates the total number of shares dealers would need to buy or
sell at various price displacements. These flows create natural support and resistance
zones that technically-oriented 0DTE traders use for entry and exit timing.

---

## Quick Start

```bash
pip install flashalpha
```

```python
import os
from flashalpha import FlashAlpha

fa = FlashAlpha(os.environ["FLASHALPHA_API_KEY"])
data = fa.zero_dte("SPY")
print(data["regime"]["label"])         # e.g. "positive_gamma"
print(data["pin_risk"]["pin_score"])   # 0-100
print(data["expected_move"]["remaining_1sd"])  # intraday remaining move
```

Get a free API key at [flashalpha.com](https://flashalpha.com) — no credit card required.

---

## Examples

| File | Description |
|---|---|
| [examples/0dte_pin_risk_analysis.py](examples/0dte_pin_risk_analysis.py) | Analyze pin risk: pin score, magnet strike, OI concentration, max pain |
| [examples/0dte_expected_move_calculator.py](examples/0dte_expected_move_calculator.py) | Calculate full-day and remaining intraday expected move |
| [examples/0dte_gamma_regime_tracker.py](examples/0dte_gamma_regime_tracker.py) | Track gamma regime: flip level, positive/negative gamma implications |
| [examples/0dte_dealer_hedging_flows.py](examples/0dte_dealer_hedging_flows.py) | Estimate dealer share flows at various price displacements |
| [examples/0dte_theta_decay_monitor.py](examples/0dte_theta_decay_monitor.py) | Monitor theta decay, charm regime, gamma acceleration near close |
| [examples/0dte_spy_intraday_playbook.py](examples/0dte_spy_intraday_playbook.py) | Complete intraday report: regime, expected move, pin risk, hedging, decay |
| [examples/0dte_trading_strategies.py](examples/0dte_trading_strategies.py) | 5 common 0DTE strategies with API data to inform each |
| [examples/0dte_vol_context_analysis.py](examples/0dte_vol_context_analysis.py) | Vol context: 0DTE/7DTE IV ratio, VIX, vanna exposure |

---

## Theory

| File | Description |
|---|---|
| [theory/what_is_0dte.md](theory/what_is_0dte.md) | What are 0DTE options, why they've grown, SPY/SPX schedule |
| [theory/pin_risk_mechanics.md](theory/pin_risk_mechanics.md) | Detailed pin risk mechanics and OI concentration |
| [theory/gamma_acceleration.md](theory/gamma_acceleration.md) | Why gamma accelerates near expiration and the math behind it |

---

## Further Reading

- [0DTE Gamma Exposure and Pin Risk: Intraday Options Analytics](https://flashalpha.com/articles/0dte-gamma-exposure-pin-risk-intraday-options-analytics)
- [0DTE SPY Complete Intraday Playbook: Same-Day Options](https://flashalpha.com/articles/0dte-spy-complete-intraday-playbook-same-day-options)
- [Guide to 0DTE Trading Strategies with Real-Time Data](https://flashalpha.com/articles/guide-to-0dte-trading-strategies-real-time-data)
- [Zero-DTE API: Complete Guide to the 0DTE Analytics Endpoint](https://flashalpha.com/articles/zero-dte-api-complete-guide-0dte-analytics-endpoint)
- [Zero-DTE Options API: Real-Time 0DTE Analytics](https://flashalpha.com/articles/zero-dte-options-api-real-time-0dte-analytics)

---

## SDK

Install the official Python SDK: `pip install flashalpha`

Full SDK documentation and API reference: [flashalpha.com](https://flashalpha.com)

GitHub: [github.com/FlashAlpha-lab/flashalpha-python](https://github.com/FlashAlpha-lab/flashalpha-python)

---

## See Also

- [FlashAlpha Python SDK](https://github.com/FlashAlpha-lab/flashalpha-python) — `pip install flashalpha`
- [GEX Explained](https://github.com/FlashAlpha-lab/gex-explained) — gamma exposure theory and code
- [Volatility Surface Python](https://github.com/FlashAlpha-lab/volatility-surface-python) — SVI, variance swap, skew analysis
- [Examples](https://github.com/FlashAlpha-lab/flashalpha-examples) — more tutorials
- [Awesome Options Analytics](https://github.com/FlashAlpha-lab/awesome-options-analytics) — curated resource list

---

## License

MIT — see [LICENSE](LICENSE)
