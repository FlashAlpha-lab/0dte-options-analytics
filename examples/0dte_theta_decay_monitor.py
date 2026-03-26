"""
0DTE Theta Decay Monitor — Python example using the FlashAlpha API.

Monitors theta decay dynamics for 0DTE (zero days to expiration) options
on SPY. Tracks net theta, per-hour decay rate, charm regime, and gamma
acceleration. Theta decay is not linear — it accelerates dramatically
in the final 2-3 hours of a 0DTE session, which is one of the defining
characteristics that makes these instruments unique.

Install: pip install flashalpha
Docs:    https://flashalpha.com/articles/0dte-spy-complete-intraday-playbook-same-day-options
"""

import os
from flashalpha import FlashAlpha

API_KEY = os.environ.get("FLASHALPHA_API_KEY", "YOUR_API_KEY")
fa = FlashAlpha(API_KEY)


def monitor_theta_decay(symbol: str = "SPY") -> None:
    """
    Fetch 0DTE analytics and print a theta decay report.

    Theta is the rate at which an option loses value as time passes,
    holding all else constant. For 0DTE options, theta is extremely
    high because every hour consumed represents a large fraction of
    the remaining life. A standard 0DTE ATM option may lose 30-50%
    of its value in the final 90 minutes.

    Charm is the second-order greek measuring how delta changes as time
    passes. In 0DTE options, charm is significant because it causes
    dealer delta hedges to unwind rapidly near close, creating forced
    buying or selling flows unrelated to price movement.

    Gamma acceleration measures whether gamma is increasing (speeding up)
    as time decays. For near-the-money 0DTE options, gamma accelerates
    sharply in the final hours — small moves produce increasingly larger
    swings in option price.
    """
    data = fa.zero_dte(symbol)

    if data.get("no_zero_dte"):
        print(f"No 0DTE expiration today for {symbol}.")
        return

    decay = data.get("decay", data.get("theta_decay", {}))
    em = data.get("expected_move", {})

    print(f"=== 0DTE Theta Decay Monitor: {symbol} ===")
    print()

    # Net theta: total dollar value that 0DTE options lose per day
    # across all open contracts (from dealer perspective).
    # Negative net theta = dealers are short options and collecting decay.
    # Positive net theta = dealers are long options and paying decay.
    net_theta = decay.get("net_theta")
    if net_theta is not None:
        sign = "+" if net_theta >= 0 else ""
        print(f"Net Theta (0DTE):   {sign}${net_theta:,.0f}/day")
        if net_theta < 0:
            print("  Dealers are short options — they benefit from time passing.")
        else:
            print("  Dealers are long options — they lose value as time passes.")

    # Theta per hour gives a real-time view of how much value is burning
    # off per hour remaining in the session. This accelerates near close.
    theta_per_hour = decay.get("theta_per_hour")
    if theta_per_hour is not None:
        print(f"Theta per Hour:     ${abs(theta_per_hour):,.0f}/hour")

    # Hours remaining in the trading session
    hours_remaining = em.get("hours_remaining") or decay.get("hours_remaining")
    if hours_remaining is not None:
        print(f"Hours Remaining:    {hours_remaining:.1f}h")

        # Classify the phase of the day's theta decay cycle
        if hours_remaining < 1.0:
            phase = "FINAL HOUR — theta decay is at maximum rate"
        elif hours_remaining < 2.0:
            phase = "END GAME — decay accelerating rapidly"
        elif hours_remaining < 3.5:
            phase = "AFTERNOON — decay picking up speed"
        else:
            phase = "MORNING/MIDDAY — decay rate moderate"
        print(f"Decay Phase:        {phase}")

    # Charm regime describes how dealer delta hedges are evolving due
    # to time passage alone. "unwinding" means dealers are reducing
    # their hedge positions as the day progresses.
    charm_regime = decay.get("charm_regime")
    if charm_regime:
        print(f"\nCharm Regime:       {charm_regime}")
        print("  Charm creates forced dealer transactions near close,")
        print("  independent of price movement.")

    # Gamma acceleration measures whether 0DTE gamma is speeding up.
    # A value > 1.0 means gamma is higher now than the session average.
    # Values > 2.0 signal an elevated risk of sharp intraday moves.
    gamma_acceleration = decay.get("gamma_acceleration")
    if gamma_acceleration is not None:
        print(f"\nGamma Acceleration: {gamma_acceleration:.2f}x")
        if gamma_acceleration >= 3.0:
            print("  EXTREME — 0DTE gamma is highly elevated. Small moves = large P&L swings.")
        elif gamma_acceleration >= 2.0:
            print("  HIGH — gamma is well above average. Intraday moves can be sharp.")
        elif gamma_acceleration >= 1.5:
            print("  ELEVATED — gamma is above average. Monitor positions closely.")
        else:
            print("  NORMAL — gamma acceleration is moderate.")

    # Rate of decay change shows whether we're entering the acceleration zone
    decay_rate_change = decay.get("decay_rate_change")
    if decay_rate_change is not None:
        print(f"\nDecay Rate Change:  {decay_rate_change:+.1%}/hour")

    print()
    print("=== Trading Implications ===")
    print("Final 2 hours: theta decay accelerates — premium sellers benefit most")
    print("Final 1 hour:  gamma acceleration can create explosive moves near strikes")
    print("Near close:    charm unwind may cause abrupt directional pressure")
    print()
    print("Theta sellers: the last 90 minutes are when you earn most of your daily edge")
    print("Theta buyers:  be cautious holding 0DTE longs in the final 2 hours")
    print()
    print("Reference: https://flashalpha.com/articles/0dte-spy-complete-intraday-playbook-same-day-options")


if __name__ == "__main__":
    monitor_theta_decay("SPY")
