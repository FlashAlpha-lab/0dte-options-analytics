"""
0DTE Gamma Regime Tracker — Python example using the FlashAlpha API.

Tracks the intraday gamma regime for 0DTE (zero days to expiration)
options on SPY. Prints the regime label (positive/negative gamma),
the gamma flip level, spot price vs. flip, and the share of total GEX
attributable to 0DTE options. Understanding the gamma regime is the
foundation of intraday options analytics.

Install: pip install flashalpha
Docs:    https://flashalpha.com/articles/0dte-gamma-exposure-pin-risk-intraday-options-analytics
"""

import os
from flashalpha import FlashAlpha

API_KEY = os.environ.get("FLASHALPHA_API_KEY", "YOUR_API_KEY")
fa = FlashAlpha(API_KEY)


def track_gamma_regime(symbol: str = "SPY") -> None:
    """
    Fetch 0DTE analytics and print the gamma regime report.

    The gamma regime determines how dealers must hedge as price moves.
    In positive gamma regimes, dealer hedging dampens volatility and
    keeps price in a tighter range. In negative gamma regimes, dealer
    hedging amplifies moves, making breakouts more likely to sustain.

    The gamma flip is the price level where net dealer GEX crosses from
    positive to negative. It is often the most important intraday level.
    Price above the flip -> positive gamma (dampened vol, mean-revert).
    Price below the flip -> negative gamma (amplified vol, trend-follow).
    """
    data = fa.zero_dte(symbol)

    if data.get("no_zero_dte"):
        print(f"No 0DTE expiration today for {symbol}.")
        return

    regime = data.get("regime", {})
    spot = data.get("spot", data.get("underlying_price"))

    print(f"=== 0DTE Gamma Regime Tracker: {symbol} ===")
    print()

    # Regime label classifies the current dealer positioning.
    # "positive_gamma" -> dealers are net long gamma (they own options).
    # "negative_gamma" -> dealers are net short gamma (they sold options).
    label = regime.get("label", regime.get("regime_label", "unknown"))
    print(f"Regime:             {label}")

    if "positive" in label.lower():
        print("  Implication:      Dealers dampen volatility — range-bound conditions favored")
        print("  Dealer action:    Sell rallies, buy dips (reduces intraday range)")
        print("  Strategy bias:    Sell premium, iron condors, credit spreads")
    elif "negative" in label.lower():
        print("  Implication:      Dealers amplify volatility — trending moves more likely")
        print("  Dealer action:    Buy rallies, sell dips (extends intraday range)")
        print("  Strategy bias:    Buy directional options, debit spreads, straddles")

    # The gamma flip is the single most important level from GEX analysis.
    # It represents the spot price where total GEX changes sign.
    gamma_flip = regime.get("gamma_flip")
    if gamma_flip is not None:
        print(f"\nGamma Flip:         {gamma_flip}")

        if spot:
            distance = spot - gamma_flip
            distance_pct = distance / spot * 100
            side = "ABOVE" if distance > 0 else "BELOW"
            print(f"Spot Price:         {spot}")
            print(f"Spot vs. Flip:      {side} flip by ${abs(distance):.2f} ({abs(distance_pct):.2f}%)")

            if abs(distance_pct) < 0.25:
                print("  Warning: Spot is very close to the gamma flip.")
                print("  Regime may flip intraday — watch for vol regime change.")

    # The fraction of total GEX from 0DTE options tells you how much
    # of today's dealer hedging pressure comes from same-day expiries.
    # When 0DTE dominates (>50%), intraday GEX levels are highly dynamic
    # because large OI rolls off at the close.
    zero_dte_gex_pct = regime.get("zero_dte_gex_pct", regime.get("zero_dte_share"))
    if zero_dte_gex_pct is not None:
        print(f"\n0DTE Share of GEX:  {zero_dte_gex_pct:.1%}")
        if zero_dte_gex_pct > 0.5:
            print("  Note: 0DTE options dominate GEX today.")
            print("  Gamma dynamics change rapidly — reassess regime hourly.")

    # Net GEX value from the regime section if provided
    net_gex = regime.get("net_gex")
    if net_gex is not None:
        sign = "+" if net_gex >= 0 else ""
        print(f"\nNet GEX (0DTE):     {sign}${net_gex:,.0f}")

    # Intraday trend based on recent GEX changes
    trend = regime.get("trend", regime.get("gex_trend"))
    if trend:
        print(f"GEX Trend:          {trend}")
        print("  (Whether dealer hedging pressure is increasing or decreasing)")

    print()
    print("=== Key Levels ===")
    call_wall = regime.get("call_wall")
    put_wall = regime.get("put_wall")
    if call_wall:
        print(f"Call Wall:          {call_wall}  (largest call OI concentration)")
    if put_wall:
        print(f"Put Wall:           {put_wall}  (largest put OI concentration)")
    if gamma_flip:
        print(f"Gamma Flip:         {gamma_flip}  (positive/negative gamma boundary)")

    print()
    print("Reference: https://flashalpha.com/articles/0dte-gamma-exposure-pin-risk-intraday-options-analytics")


if __name__ == "__main__":
    track_gamma_regime("SPY")
