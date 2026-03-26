"""
0DTE Vol Context Analysis — Python example using the FlashAlpha API.

Analyzes volatility context for 0DTE (zero days to expiration) options
on SPY. Prints the 0DTE vs. 7DTE IV ratio, VIX level, vanna exposure,
and vol interpretation. Understanding vol context helps traders assess
whether intraday implied volatility is elevated or compressed relative
to the broader vol surface, which informs premium buying vs. selling bias.

Install: pip install flashalpha
Docs:    https://flashalpha.com/articles/zero-dte-options-api-real-time-0dte-analytics
"""

import os
from flashalpha import FlashAlpha

API_KEY = os.environ.get("FLASHALPHA_API_KEY", "YOUR_API_KEY")
fa = FlashAlpha(API_KEY)


def analyze_vol_context(symbol: str = "SPY") -> None:
    """
    Fetch 0DTE analytics and print the volatility context report.

    The vol context section of the zero_dte response provides data
    about how same-day implied volatility compares to the broader
    vol surface. Key questions this answers:

    1. Is 0DTE IV elevated vs. 7DTE IV? (IV ratio)
       Ratio > 1.0 means traders are paying a premium for same-day
       options vs. weekly options — often driven by event risk,
       FOMC, CPI, or elevated intraday demand for protection.

    2. Where is VIX? (macro vol context)
       Low VIX (<15) generally favors premium selling.
       High VIX (>25) generally favors premium buying / protection.

    3. What is the vanna exposure?
       Vanna measures how dealer delta changes as implied volatility
       changes. Large positive vanna means dealers must buy the
       underlying if IV falls (vol crush = tailwind for price).
       Large negative vanna means dealers must sell if IV rises.
    """
    data = fa.zero_dte(symbol)

    if data.get("no_zero_dte"):
        print(f"No 0DTE expiration today for {symbol}.")
        return

    vol = data.get("vol_context", data.get("volatility_context", {}))
    em = data.get("expected_move", {})
    spot = data.get("spot", data.get("underlying_price"))

    print(f"=== 0DTE Vol Context Analysis: {symbol} ===")
    if spot:
        print(f"Spot Price:         {spot}")
    print()

    # IV Ratio: 0DTE ATM IV divided by 7DTE ATM IV.
    # This tells you whether same-day options are "expensive" or "cheap"
    # relative to the options market's baseline weekly expectation.
    iv_ratio = vol.get("zero_dte_7dte_ratio", vol.get("iv_ratio"))
    atm_iv_0dte = vol.get("atm_iv_0dte") or em.get("atm_iv")
    atm_iv_7dte = vol.get("atm_iv_7dte")

    if atm_iv_0dte is not None:
        print(f"ATM IV (0DTE):      {atm_iv_0dte:.1%}")
    if atm_iv_7dte is not None:
        print(f"ATM IV (7DTE):      {atm_iv_7dte:.1%}")

    if iv_ratio is not None:
        print(f"\n0DTE/7DTE IV Ratio: {iv_ratio:.3f}")

        # Interpret the ratio
        if iv_ratio > 1.25:
            print("  Interpretation:   HIGHLY ELEVATED")
            print("  Meaning:          0DTE options are significantly expensive vs. 7DTE")
            print("  Context:          Likely driven by same-day event, Fed, or CPI risk")
            print("  Bias:             Premium SELLING in 0DTE has elevated structural edge")
        elif iv_ratio > 1.10:
            print("  Interpretation:   ELEVATED")
            print("  Meaning:          0DTE options are moderately expensive vs. 7DTE")
            print("  Bias:             Slight edge to premium selling strategies")
        elif iv_ratio > 0.90:
            print("  Interpretation:   NORMAL")
            print("  Meaning:          0DTE IV is in line with the broader vol surface")
            print("  Bias:             Neutral — regime and pin risk should drive strategy selection")
        else:
            print("  Interpretation:   SUBDUED")
            print("  Meaning:          0DTE options are cheap relative to 7DTE")
            print("  Bias:             Edge to premium BUYING — straddles may be underpriced")

    # VIX provides macro vol context. The SPX VIX reflects a 30-day
    # implied vol estimate, but it anchors trader expectations for
    # intraday vol regimes too. High VIX = market expects large moves.
    print()
    vix = vol.get("vix")
    if vix is not None:
        print(f"VIX:                {vix:.2f}")
        if vix < 13:
            print("  VIX Regime:       VERY LOW — complacent market, range-bound conditions likely")
        elif vix < 18:
            print("  VIX Regime:       LOW — calm conditions favor premium selling")
        elif vix < 25:
            print("  VIX Regime:       MODERATE — balanced regime")
        elif vix < 35:
            print("  VIX Regime:       ELEVATED — volatile conditions, wider expected moves")
        else:
            print("  VIX Regime:       HIGH — extreme vol, 0DTE premium buyers may outperform")

    # Vanna exposure measures how vanna-related dealer flows will affect
    # the underlying if implied volatility changes intraday. A vol crush
    # (IV falling after a spike) with positive vanna creates a tailwind
    # for price as dealers buy to rehedge.
    print()
    vanna_exp = vol.get("vanna_exposure")
    vanna_interp = vol.get("vanna_interpretation")

    if vanna_exp is not None:
        sign = "+" if vanna_exp >= 0 else ""
        print(f"Vanna Exposure:     {sign}${vanna_exp:,.0f}")
        if vanna_exp > 0:
            print("  Direction:        POSITIVE — IV drop -> dealers BUY underlying (vol crush = bid)")
        else:
            print("  Direction:        NEGATIVE — IV drop -> dealers SELL underlying (vol crush = offer)")

    if vanna_interp:
        print(f"  Interpretation:   {vanna_interp}")

    # Vol term structure slope describes whether the market expects
    # vol to be higher today vs. later in the week.
    term_slope = vol.get("term_structure_slope")
    if term_slope is not None:
        print(f"\nTerm Structure:     {term_slope}")

    # Overall vol regime classification
    vol_regime = vol.get("vol_regime", vol.get("regime"))
    if vol_regime:
        print(f"\nVol Regime:         {vol_regime}")

    print()
    print("=== Strategy Implications ===")
    print("High IV ratio (>1.1) + positive gamma -> sell premium (0DTE is overpriced)")
    print("Low IV ratio (<0.9)  + negative gamma -> buy premium (0DTE is underpriced)")
    print("High VIX + negative vanna -> vol crush tailwind for longs on any IV spike")
    print("Low VIX  + positive vanna -> be cautious selling premium if vol can spike")
    print()
    print("Reference: https://flashalpha.com/articles/zero-dte-options-api-real-time-0dte-analytics")


if __name__ == "__main__":
    analyze_vol_context("SPY")
