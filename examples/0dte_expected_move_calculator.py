"""
0DTE Expected Move Calculator — Python example using the FlashAlpha API.

Calculates the implied intraday expected move for 0DTE (zero days to
expiration) options on SPY. Shows both the full-day 1-standard-deviation
range and the remaining expected move adjusted for time elapsed in the
session. Uses ATM IV and straddle price from the FlashAlpha zero_dte
endpoint.

Install: pip install flashalpha
Docs:    https://flashalpha.com/articles/zero-dte-api-complete-guide-0dte-analytics-endpoint
"""

import os
from flashalpha import FlashAlpha

API_KEY = os.environ.get("FLASHALPHA_API_KEY", "YOUR_API_KEY")
fa = FlashAlpha(API_KEY)


def calculate_expected_move(symbol: str = "SPY") -> None:
    """
    Fetch 0DTE analytics and print an expected move report.

    The expected move tells a trader how far the market is pricing in
    a move by end of day. The 1SD expected move derived from the ATM
    straddle price represents the range where the market assigns roughly
    68% probability of the close landing.

    As time passes, the remaining expected move shrinks with the square
    root of remaining time — this is the square-root-of-time rule from
    options theory. For example, if 4 hours remain out of a 6.5-hour
    session, the remaining expected move is approximately:
        remaining = full_day_move * sqrt(4 / 6.5) ≈ 78% of full-day move

    The API computes this in real time so you always have a calibrated
    range for the current moment in the session.
    """
    data = fa.zero_dte(symbol)

    if data.get("no_zero_dte"):
        print(f"No 0DTE expiration today for {symbol}.")
        return

    em = data.get("expected_move", {})
    spot = data.get("spot", data.get("underlying_price"))

    print(f"=== 0DTE Expected Move Calculator: {symbol} ===")
    print()

    # The ATM IV is the implied volatility of the at-the-money options
    # expiring today. It reflects the market's current consensus on
    # intraday volatility.
    atm_iv = em.get("atm_iv")
    if atm_iv is not None:
        print(f"ATM IV (0DTE):      {atm_iv:.1%}")

    # Straddle price = call + put at the ATM strike. This is the raw
    # cost a buyer pays to profit from any directional move. It also
    # directly implies the 1SD expected move for the full day.
    straddle_price = em.get("straddle_price")
    if straddle_price is not None:
        print(f"ATM Straddle Price: ${straddle_price:.2f}")

    # The full-day 1SD expected move: the range within which the market
    # assigns ~68% probability for the closing price.
    full_day_1sd = em.get("full_day_1sd")
    if full_day_1sd is not None and spot:
        upper_full = spot + full_day_1sd
        lower_full = spot - full_day_1sd
        print(f"\nFull-Day 1SD Move:  ±${full_day_1sd:.2f}")
        print(f"  Upper bound:      {upper_full:.2f}")
        print(f"  Lower bound:      {lower_full:.2f}")
        print(f"  As % of spot:     ±{full_day_1sd / spot * 100:.2f}%")

    # The remaining 1SD move is the most actionable number during the
    # session. It is smaller than the full-day move because some time
    # value has already been consumed. Use this to calibrate whether
    # price has already moved its expected range.
    remaining_1sd = em.get("remaining_1sd")
    if remaining_1sd is not None and spot:
        upper_rem = spot + remaining_1sd
        lower_rem = spot - remaining_1sd
        print(f"\nRemaining 1SD Move: ±${remaining_1sd:.2f}")
        print(f"  Upper bound:      {upper_rem:.2f}")
        print(f"  Lower bound:      {lower_rem:.2f}")
        print(f"  As % of spot:     ±{remaining_1sd / spot * 100:.2f}%")

        # Show how much of the day's expected move has been consumed
        if full_day_1sd and full_day_1sd > 0:
            pct_remaining = remaining_1sd / full_day_1sd * 100
            print(f"  Remaining:        {pct_remaining:.0f}% of full-day expected move")

    # Time context — how far through the session are we?
    time_elapsed_pct = em.get("time_elapsed_pct")
    hours_remaining = em.get("hours_remaining")
    if time_elapsed_pct is not None:
        print(f"\nTime Elapsed:       {time_elapsed_pct:.0f}% of session")
    if hours_remaining is not None:
        print(f"Hours Remaining:    {hours_remaining:.1f}h")

    print()
    print("=== Interpretation ===")
    print("If price has already moved beyond remaining_1sd from open ->")
    print("  the expected move has been exceeded; mean reversion setups increase")
    print("If price is well within remaining_1sd ->")
    print("  range-bound strategies like iron condors and credit spreads are favored")
    print()
    print("Reference: https://flashalpha.com/articles/0dte-spy-complete-intraday-playbook-same-day-options")


if __name__ == "__main__":
    calculate_expected_move("SPY")
