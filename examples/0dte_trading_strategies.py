"""
0DTE Trading Strategies — Python example using the FlashAlpha API.

Demonstrates 5 common 0DTE (zero days to expiration) trading strategies
with real-time API data informing each setup: pin play, gamma scalp,
vol crush, momentum fade, and straddle. Uses both fa.zero_dte() for
intraday analytics and fa.gex() for gamma exposure context.

These are analytical examples only — not trading recommendations.

Install: pip install flashalpha
Docs:    https://flashalpha.com/articles/guide-to-0dte-trading-strategies-real-time-data
"""

import os
from flashalpha import FlashAlpha

API_KEY = os.environ.get("FLASHALPHA_API_KEY", "YOUR_API_KEY")
fa = FlashAlpha(API_KEY)


def strategy_pin_play(data: dict, symbol: str) -> None:
    """
    Strategy 1: The Pin Play

    When a strike has heavy 0DTE OI and the pin score is high, selling a
    straddle or iron butterfly at the magnet strike can be profitable.
    Dealer hedging creates gravitational pull toward the strike, which
    favors premium sellers positioned at that level.

    Best conditions: pin_score > 65, price within 0.3% of magnet strike,
    less than 3 hours to close.
    """
    print("\n--- Strategy 1: Pin Play ---")
    pin = data.get("pin_risk", {})
    pin_score = pin.get("pin_score", 0) or 0
    magnet = pin.get("magnet_strike")
    spot = data.get("spot", data.get("underlying_price"))

    if not magnet or not spot:
        print("  Insufficient data for pin play setup.")
        return

    dist_pct = abs(spot - magnet) / spot * 100

    print(f"  Pin Score:    {pin_score}/100")
    print(f"  Magnet:       {magnet}")
    print(f"  Distance:     {dist_pct:.2f}% from spot")

    if pin_score >= 65 and dist_pct <= 0.35:
        print("  Signal:       ACTIVE — pin play conditions met")
        print(f"  Setup:        Sell straddle at {magnet} or iron butterfly centered at {magnet}")
        print("  Entry:        Sell ATM call + ATM put at magnet strike")
        print("  Exit:         Close at 50-70% profit or 2 hours before close")
        print("  Stop:         Price breaks magnet by more than straddle price")
    elif pin_score >= 50:
        print("  Signal:       WEAK — some pinning tendency but not ideal")
        print("  Action:       Wait for price to move closer to magnet strike")
    else:
        print("  Signal:       INACTIVE — insufficient pin risk for this strategy")


def strategy_gamma_scalp(data: dict, gex_data: dict) -> None:
    """
    Strategy 2: Gamma Scalp

    In negative gamma regimes, dealers amplify moves. Buying a 0DTE ATM
    straddle or strangle and delta-hedging it (gamma scalping) can extract
    value from realized volatility exceeding implied volatility. This
    requires active management every 15-30 minutes.

    Best conditions: negative gamma regime, VIX elevated, spot near gamma flip.
    """
    print("\n--- Strategy 2: Gamma Scalp ---")
    regime = data.get("regime", {})
    label = regime.get("label", "")
    gamma_flip = regime.get("gamma_flip") or gex_data.get("gamma_flip")
    spot = data.get("spot", data.get("underlying_price"))
    em = data.get("expected_move", {})
    atm_iv = em.get("atm_iv")

    print(f"  Regime:       {label}")
    if gamma_flip:
        print(f"  Gamma Flip:   {gamma_flip}")
    if atm_iv:
        print(f"  ATM IV:       {atm_iv:.1%}")

    if "negative" in label.lower():
        print("  Signal:       ACTIVE — negative gamma regime favors gamma scalping")
        print("  Setup:        Buy ATM straddle, delta-hedge every 15-30 min")
        print("  P&L driver:   Realized vol > implied vol (collect gamma)")
        print("  Risk:         Theta decay in final 2h can overwhelm gamma gains")
        if gamma_flip and spot:
            dist_pct = abs(spot - gamma_flip) / spot * 100
            if dist_pct < 0.5:
                print(f"  Note:         Spot is {dist_pct:.2f}% from gamma flip — regime may switch")
    else:
        print("  Signal:       INACTIVE — positive gamma dampens realized vol")
        print("  Action:       Wait for regime to shift to negative gamma")


def strategy_vol_crush(data: dict) -> None:
    """
    Strategy 3: Vol Crush

    After a morning spike in implied volatility, fading the IV by selling
    premium can be profitable if the vol context shows 0DTE IV elevated
    vs. 7DTE. The expected move provides the width for an iron condor.

    Best conditions: 0DTE/7DTE IV ratio > 1.1, price inside 1SD bounds,
    positive gamma regime.
    """
    print("\n--- Strategy 3: Vol Crush ---")
    vol = data.get("vol_context", data.get("volatility_context", {}))
    em = data.get("expected_move", {})
    regime = data.get("regime", {})

    iv_ratio = vol.get("zero_dte_7dte_ratio", vol.get("iv_ratio"))
    full_1sd = em.get("full_day_1sd")
    spot = data.get("spot", data.get("underlying_price"))
    regime_label = regime.get("label", "")

    if iv_ratio is not None:
        print(f"  0DTE/7DTE IV Ratio: {iv_ratio:.2f}")
    if full_1sd and spot:
        print(f"  1SD Range:    [{spot - full_1sd:.2f} — {spot + full_1sd:.2f}]")

    active = (
        (iv_ratio is not None and iv_ratio > 1.1)
        and ("positive" in regime_label.lower())
    )

    if active:
        print("  Signal:       ACTIVE — elevated 0DTE IV + positive gamma = vol crush candidate")
        if full_1sd and spot:
            call_strike = round(spot + full_1sd * 0.8)
            put_strike = round(spot - full_1sd * 0.8)
            print(f"  Setup:        Iron condor — sell {put_strike}P/{call_strike}C inside 1SD")
        print("  Exit:         Close at 50% profit or 90 min before close")
        print("  Stop:         Price breaks 1SD boundary")
    else:
        print("  Signal:       INACTIVE — IV ratio not elevated or wrong regime")


def strategy_momentum_fade(data: dict) -> None:
    """
    Strategy 4: Momentum Fade

    When price has moved beyond the remaining 1SD expected move, the
    statistical edge shifts toward mean reversion. Buying OTM options
    in the opposite direction or selling OTM options in the momentum
    direction can capture this reversion tendency.

    Best conditions: spot displaced more than remaining_1sd from open,
    positive gamma regime (dealers will push price back).
    """
    print("\n--- Strategy 4: Momentum Fade ---")
    em = data.get("expected_move", {})
    regime = data.get("regime", {})

    rem_1sd = em.get("remaining_1sd")
    spot = data.get("spot", data.get("underlying_price"))
    open_price = em.get("open_price", data.get("open_price"))
    regime_label = regime.get("label", "")

    if rem_1sd:
        print(f"  Remaining 1SD: ±${rem_1sd:.2f}")
    if open_price and spot:
        displacement = spot - open_price
        print(f"  Open Price:    {open_price}")
        print(f"  Displacement:  {displacement:+.2f} from open")

        if rem_1sd and abs(displacement) > rem_1sd:
            direction = "upside" if displacement > 0 else "downside"
            fade_direction = "puts" if displacement > 0 else "calls"
            print(f"  Signal:       ACTIVE — price exceeded remaining 1SD to the {direction}")
            print(f"  Setup:        Buy OTM {fade_direction} or sell OTM options in momentum direction")
            print("  Rationale:    Move has exceeded statistical expectation — fade the extension")
            if "positive" in regime_label.lower():
                print("  Confirmation: Positive gamma regime reinforces mean reversion tendency")
        else:
            print("  Signal:       INACTIVE — displacement within remaining 1SD")
    else:
        print("  Insufficient data (need open price and remaining 1SD)")


def strategy_atm_straddle(data: dict) -> None:
    """
    Strategy 5: ATM Straddle

    Buying the ATM straddle at the open captures directional moves in
    either direction. The break-even points are spot +/- straddle price.
    Best deployed when negative gamma regime means dealers will amplify
    whatever directional move develops.

    Best conditions: negative gamma regime, straddle price reasonable
    vs. historical intraday range, early in session (>4 hours remaining).
    """
    print("\n--- Strategy 5: ATM Straddle ---")
    em = data.get("expected_move", {})
    regime = data.get("regime", {})

    straddle = em.get("straddle_price")
    spot = data.get("spot", data.get("underlying_price"))
    hours_rem = em.get("hours_remaining") or data.get("decay", {}).get("hours_remaining")
    regime_label = regime.get("label", "")

    if straddle:
        print(f"  Straddle Price: ${straddle:.2f}")
    if spot and straddle:
        upper_be = spot + straddle
        lower_be = spot - straddle
        print(f"  Break-evens:    [{lower_be:.2f} — {upper_be:.2f}]")
        pct_be = straddle / spot * 100
        print(f"  Move needed:    {pct_be:.2f}% from current spot")
    if hours_rem:
        print(f"  Hours left:     {hours_rem:.1f}h")

    active = (
        "negative" in regime_label.lower()
        and (hours_rem is None or hours_rem > 3.0)
    )

    if active:
        print("  Signal:       ACTIVE — negative gamma + sufficient time remaining")
        print("  Setup:        Buy 1 ATM call + 1 ATM put, same strike, same expiry")
        print("  Exit:         Take profit when one leg doubles, or at 80% profit total")
        print("  Stop:         Close if time decay consumes 50% of premium with no move")
    elif hours_rem and hours_rem < 2.0:
        print("  Signal:       INACTIVE — too little time left (theta risk too high)")
    else:
        print("  Signal:       WEAK — positive gamma reduces odds of straddle profit")

    print()


def run_all_strategies(symbol: str = "SPY") -> None:
    """Fetch 0DTE and GEX data, then evaluate all five strategies."""
    print(f"=== 0DTE Trading Strategy Dashboard: {symbol} ===")
    print("Fetching live data...")

    # Single zero_dte call for all intraday analytics
    data = fa.zero_dte(symbol)

    if data.get("no_zero_dte"):
        print(f"\nNo 0DTE expiration today for {symbol}.")
        print("SPY 0DTE days: Monday, Wednesday, Friday")
        return

    # GEX provides the broader gamma flip used in some strategies
    gex_data = fa.gex(symbol)

    spot = data.get("spot", data.get("underlying_price"))
    regime = data.get("regime", {})
    print(f"\nSpot:    {spot}")
    print(f"Regime:  {regime.get('label', 'unknown')}")

    strategy_pin_play(data, symbol)
    strategy_gamma_scalp(data, gex_data)
    strategy_vol_crush(data)
    strategy_momentum_fade(data)
    strategy_atm_straddle(data)

    print("Reference: https://flashalpha.com/articles/guide-to-0dte-trading-strategies-real-time-data")


if __name__ == "__main__":
    run_all_strategies("SPY")
