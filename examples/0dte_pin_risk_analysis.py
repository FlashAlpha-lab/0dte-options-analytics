"""
0DTE Pin Risk Analysis — Python example using the FlashAlpha API.

Analyzes pin risk for 0DTE (zero days to expiration) options on SPY.
Pin risk occurs when a large concentration of open interest at a nearby
strike creates gravitational price action near expiration. This script
prints the pin score, magnet strike, distance from current price, max
pain level, and OI concentration to help traders identify likely pinning.

Install: pip install flashalpha
Docs:    https://flashalpha.com/articles/0dte-gamma-exposure-pin-risk-intraday-options-analytics
"""

import os
from flashalpha import FlashAlpha

# Retrieve your API key from the environment. Get one at flashalpha.com.
API_KEY = os.environ.get("FLASHALPHA_API_KEY", "YOUR_API_KEY")
fa = FlashAlpha(API_KEY)


def analyze_pin_risk(symbol: str = "SPY") -> None:
    """
    Fetch 0DTE analytics and print a pin risk report.

    Pin risk is the tendency of an underlying to close at or near a
    strike with heavy open interest concentration as expiration
    approaches. The magnet strike is the single strike with the most
    influence. Max pain is the strike where option sellers (dealers)
    lose the least money — it often coincides with the magnet strike.
    """
    data = fa.zero_dte(symbol)

    # If today is not a 0DTE expiration day for this symbol, the API
    # returns a no_zero_dte flag rather than live analytics.
    if data.get("no_zero_dte"):
        print(f"No 0DTE expiration today for {symbol}.")
        print("SPY has 0DTE options on Monday, Wednesday, and Friday.")
        print("SPX has 0DTE options every weekday.")
        return

    pin = data.get("pin_risk", {})
    spot = data.get("spot", data.get("underlying_price"))

    print(f"=== 0DTE Pin Risk Report: {symbol} ===")
    print()

    # Pin score: 0 = no pin risk, 100 = extreme pin risk.
    # Scores above 70 suggest meaningful gravitational pull toward
    # the magnet strike in the final 1-2 hours of the session.
    pin_score = pin.get("pin_score")
    print(f"Pin Score:          {pin_score}/100")

    if pin_score is not None:
        if pin_score >= 80:
            print("  Interpretation:   HIGH — strong gravitational pull toward magnet strike")
        elif pin_score >= 50:
            print("  Interpretation:   MODERATE — some pinning tendency, watch the strike")
        else:
            print("  Interpretation:   LOW — underlying likely to move through strikes freely")

    # The magnet strike is the single strike exerting the most
    # gravitational force based on open interest concentration.
    magnet = pin.get("magnet_strike")
    print(f"\nMagnet Strike:      {magnet}")

    if spot and magnet:
        distance_pct = abs(spot - magnet) / spot * 100
        direction = "above" if magnet > spot else "below"
        print(f"Distance from Spot: {distance_pct:.2f}% ({direction} current price of {spot})")
        print("  Note: Pin risk intensifies when price is within 0.25% of the magnet strike")

    # Max pain is the strike where aggregate option value at expiration
    # is minimized — i.e., where option buyers collectively lose the most.
    # It often serves as an anchor for end-of-day price action.
    max_pain = pin.get("max_pain")
    print(f"\nMax Pain Strike:    {max_pain}")

    if max_pain and magnet:
        pain_diff = abs(max_pain - magnet)
        if pain_diff < 1.0:
            print("  Note: Max pain and magnet strike are aligned — pin risk is reinforced")

    # OI concentration measures what fraction of total 0DTE OI is at
    # the top 1-3 strikes. Higher concentration = stronger pin.
    oi_concentration = pin.get("oi_concentration")
    if oi_concentration is not None:
        print(f"\nOI Concentration:   {oi_concentration:.1%}")
        print("  (Share of total 0DTE OI held at top 3 strikes)")

    # Additional pin risk fields the API may return
    dominant_strike_oi = pin.get("dominant_strike_oi")
    if dominant_strike_oi:
        print(f"\nDominant Strike OI: {dominant_strike_oi:,} contracts")

    print()
    print("=== Trading Implications ===")
    print("High pin risk -> consider selling straddles/strangles at the magnet strike")
    print("High pin risk -> fade breakout attempts in final 90 minutes")
    print("Low pin risk  -> trend/momentum strategies more likely to work")
    print()
    print("Reference: https://flashalpha.com/articles/0dte-gamma-exposure-pin-risk-intraday-options-analytics")


if __name__ == "__main__":
    analyze_pin_risk("SPY")
