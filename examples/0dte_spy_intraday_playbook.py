"""
0DTE SPY Intraday Playbook — Complete real-time analytics using the FlashAlpha API.

A comprehensive intraday report combining all 0DTE analytics sections:
gamma regime, expected move, pin risk, dealer hedging flows, theta decay,
and volatility context. Run this at market open or any point during the
session to get a full picture of the options structure driving SPY price
action today.

This is the "one file" playbook for traders using 0DTE (zero days to
expiration) same-day options strategies on SPY.

Install: pip install flashalpha
Docs:    https://flashalpha.com/articles/0dte-spy-complete-intraday-playbook-same-day-options
"""

import os
from datetime import datetime
from flashalpha import FlashAlpha

API_KEY = os.environ.get("FLASHALPHA_API_KEY", "YOUR_API_KEY")
fa = FlashAlpha(API_KEY)


def print_separator(title: str = "", width: int = 60) -> None:
    if title:
        pad = (width - len(title) - 2) // 2
        print(f"\n{'=' * pad} {title} {'=' * pad}")
    else:
        print("=" * width)


def run_intraday_playbook(symbol: str = "SPY") -> None:
    """
    Fetch all 0DTE analytics and print a complete intraday report.

    Makes a single API call to fa.zero_dte() which returns all sections
    in one response: regime, expected_move, pin_risk, hedging, decay,
    vol_context. This is the most efficient way to get a full picture.
    """
    data = fa.zero_dte(symbol)

    print_separator()
    print(f"  0DTE INTRADAY PLAYBOOK: {symbol}")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print_separator()

    if data.get("no_zero_dte"):
        print(f"\nNo 0DTE expiration today for {symbol}.")
        print("SPY 0DTE expirations: Monday, Wednesday, Friday")
        print("SPX 0DTE expirations: Every weekday")
        return

    spot = data.get("spot", data.get("underlying_price"))
    if spot:
        print(f"\nSpot Price: {spot}")

    # ── SECTION 1: GAMMA REGIME ──────────────────────────────────────
    print_separator("GAMMA REGIME")

    regime = data.get("regime", {})
    label = regime.get("label", regime.get("regime_label", "unknown"))
    gamma_flip = regime.get("gamma_flip")
    zero_dte_pct = regime.get("zero_dte_gex_pct", regime.get("zero_dte_share"))

    print(f"Regime:         {label}")
    if gamma_flip:
        print(f"Gamma Flip:     {gamma_flip}")
        if spot:
            rel = "ABOVE" if spot > gamma_flip else "BELOW"
            dist_pct = abs(spot - gamma_flip) / spot * 100
            print(f"Position:       {rel} flip by {dist_pct:.2f}%")
    if zero_dte_pct is not None:
        print(f"0DTE GEX Share: {zero_dte_pct:.1%}")

    # Regime summary
    if "positive" in label.lower():
        print("Bias:           RANGE-BOUND — favor premium selling strategies")
    elif "negative" in label.lower():
        print("Bias:           DIRECTIONAL — favor debit/directional strategies")

    # ── SECTION 2: EXPECTED MOVE ─────────────────────────────────────
    print_separator("EXPECTED MOVE")

    em = data.get("expected_move", {})
    atm_iv = em.get("atm_iv")
    straddle = em.get("straddle_price")
    full_1sd = em.get("full_day_1sd")
    rem_1sd = em.get("remaining_1sd")
    hours_rem = em.get("hours_remaining") or data.get("decay", {}).get("hours_remaining")

    if atm_iv:
        print(f"ATM IV:         {atm_iv:.1%}")
    if straddle:
        print(f"Straddle Price: ${straddle:.2f}")
    if full_1sd and spot:
        print(f"Full-Day 1SD:   ±${full_1sd:.2f}  [{spot - full_1sd:.2f} — {spot + full_1sd:.2f}]")
    if rem_1sd and spot:
        print(f"Remaining 1SD:  ±${rem_1sd:.2f}  [{spot - rem_1sd:.2f} — {spot + rem_1sd:.2f}]")
    if hours_rem:
        print(f"Hours Left:     {hours_rem:.1f}h")
    if full_1sd and rem_1sd and full_1sd > 0:
        used_pct = (1 - rem_1sd / full_1sd) * 100
        print(f"Move Used:      {used_pct:.0f}% of day's expected move consumed")

    # ── SECTION 3: PIN RISK ──────────────────────────────────────────
    print_separator("PIN RISK")

    pin = data.get("pin_risk", {})
    pin_score = pin.get("pin_score")
    magnet = pin.get("magnet_strike")
    max_pain = pin.get("max_pain")
    oi_conc = pin.get("oi_concentration")

    if pin_score is not None:
        bar_len = int(pin_score / 5)
        bar = "#" * bar_len + "." * (20 - bar_len)
        print(f"Pin Score:      {pin_score}/100  [{bar}]")
        if pin_score >= 70:
            print("                HIGH — expect gravitational pull toward magnet strike")
        elif pin_score >= 40:
            print("                MODERATE — some pinning tendency")
        else:
            print("                LOW — price free to move through strikes")
    if magnet:
        print(f"Magnet Strike:  {magnet}")
        if spot:
            dist_pct = abs(spot - magnet) / spot * 100
            print(f"Distance:       {dist_pct:.2f}% from spot")
    if max_pain:
        print(f"Max Pain:       {max_pain}")
    if oi_conc is not None:
        print(f"OI Conc:        {oi_conc:.1%} at top strikes")

    # ── SECTION 4: DEALER HEDGING ────────────────────────────────────
    print_separator("DEALER HEDGING FLOWS")

    hedging = data.get("hedging", data.get("dealer_hedging", {}))

    flow_keys = [
        ("up_1pct",    "+1.0% scenario"),
        ("up_0_5pct",  "+0.5% scenario"),
        ("down_0_5pct","-0.5% scenario"),
        ("down_1pct",  "-1.0% scenario"),
    ]

    for key, label_str in flow_keys:
        flow = hedging.get(key, {})
        if isinstance(flow, dict):
            shares = flow.get("shares")
            direction = flow.get("direction")
            if shares is not None:
                dir_str = direction or ("BUY" if shares > 0 else "SELL")
                print(f"{label_str:<20} {dir_str} {abs(shares):>10,.0f} shares")
        elif isinstance(hedging, dict):
            shares = hedging.get(f"shares_{key}")
            if shares is not None:
                dir_str = "BUY" if shares > 0 else "SELL"
                print(f"{label_str:<20} {dir_str} {abs(shares):>10,.0f} shares")

    # ── SECTION 5: THETA DECAY ───────────────────────────────────────
    print_separator("THETA DECAY")

    decay = data.get("decay", data.get("theta_decay", {}))
    net_theta = decay.get("net_theta")
    theta_hr = decay.get("theta_per_hour")
    charm_regime = decay.get("charm_regime")
    gamma_accel = decay.get("gamma_acceleration")

    if net_theta is not None:
        print(f"Net Theta:      ${net_theta:,.0f}/day")
    if theta_hr is not None:
        print(f"Theta/Hour:     ${abs(theta_hr):,.0f}/hour")
    if charm_regime:
        print(f"Charm Regime:   {charm_regime}")
    if gamma_accel is not None:
        print(f"Gamma Accel:    {gamma_accel:.2f}x")

    # ── SECTION 6: VOL CONTEXT ───────────────────────────────────────
    print_separator("VOL CONTEXT")

    vol = data.get("vol_context", data.get("volatility_context", {}))
    iv_ratio = vol.get("zero_dte_7dte_ratio", vol.get("iv_ratio"))
    vix = vol.get("vix")
    vanna = vol.get("vanna_exposure", vol.get("vanna_interpretation"))

    if iv_ratio is not None:
        print(f"0DTE/7DTE IV Ratio: {iv_ratio:.2f}")
        if iv_ratio > 1.1:
            print("  0DTE IV elevated vs. 7DTE — near-term event or demand spike")
        elif iv_ratio < 0.9:
            print("  0DTE IV subdued vs. 7DTE — calm intraday conditions expected")
    if vix is not None:
        print(f"VIX:                {vix:.2f}")
    if vanna:
        print(f"Vanna Exposure:     {vanna}")

    # ── PLAYBOOK SUMMARY ─────────────────────────────────────────────
    print_separator("PLAYBOOK SUMMARY")

    regime_label = regime.get("label", "")
    pin_s = pin.get("pin_score", 0) or 0

    if "positive" in regime_label.lower() and pin_s >= 60:
        print("SETUP:  Positive gamma + high pin risk")
        print("TRADE:  Sell ATM straddle at magnet strike — collect theta from pinned price")
        print("RISK:   Stop if price breaks magnet by more than remaining_1sd")
    elif "positive" in regime_label.lower() and pin_s < 40:
        print("SETUP:  Positive gamma + low pin risk")
        print("TRADE:  Iron condor within the full-day 1SD range")
        print("RISK:   Adjust if price approaches gamma flip")
    elif "negative" in regime_label.lower():
        print("SETUP:  Negative gamma — dealers amplify moves")
        print("TRADE:  Directional debit spread in trend direction, or buy straddle")
        print("RISK:   Trend may exhaust quickly — trail stops or take profit at 1SD")
    else:
        print("SETUP:  Mixed signals — wait for clearer regime confirmation")
        print("TRADE:  Reduce size, use wider strikes")

    print()
    print("Reference: https://flashalpha.com/articles/0dte-spy-complete-intraday-playbook-same-day-options")


if __name__ == "__main__":
    run_intraday_playbook("SPY")
