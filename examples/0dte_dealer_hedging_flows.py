"""
0DTE Dealer Hedging Flows — Python example using the FlashAlpha API.

Estimates the share volume dealers must buy or sell at various price
displacements for 0DTE (zero days to expiration) options on SPY. Dealer
hedging flows create predictable support and resistance levels intraday.
Understanding the direction and magnitude of these flows gives traders
a structural edge when identifying likely inflection points.

Install: pip install flashalpha
Docs:    https://flashalpha.com/articles/guide-to-0dte-trading-strategies-real-time-data
"""

import os
from flashalpha import FlashAlpha

API_KEY = os.environ.get("FLASHALPHA_API_KEY", "YOUR_API_KEY")
fa = FlashAlpha(API_KEY)


def show_dealer_hedging_flows(symbol: str = "SPY") -> None:
    """
    Fetch 0DTE analytics and print estimated dealer hedging flows.

    Market makers who sell options must continuously delta-hedge by
    trading the underlying. As spot price moves, their delta changes
    and they must buy or sell shares to stay neutral. These flows are
    mechanical and predictable given the GEX structure.

    Positive flow numbers mean dealers must BUY the underlying (creates
    support). Negative flow numbers mean dealers must SELL the underlying
    (creates resistance). The larger the absolute value, the more
    structural force at that price level.
    """
    data = fa.zero_dte(symbol)

    if data.get("no_zero_dte"):
        print(f"No 0DTE expiration today for {symbol}.")
        return

    hedging = data.get("hedging", data.get("dealer_hedging", {}))
    spot = data.get("spot", data.get("underlying_price"))

    print(f"=== 0DTE Dealer Hedging Flow Estimates: {symbol} ===")
    if spot:
        print(f"Current Spot:       {spot}")
    print()

    # The API returns estimated hedging flows at standard displacement
    # levels (±0.5% and ±1% from current spot). These represent how
    # many shares dealers would need to transact if price moved to
    # each level right now.
    levels = [
        ("up_1pct",   "+1.0%", "price rallies 1%"),
        ("up_0_5pct", "+0.5%", "price rallies 0.5%"),
        ("down_0_5pct", "-0.5%", "price drops 0.5%"),
        ("down_1pct",   "-1.0%", "price drops 1%"),
    ]

    print(f"{'Scenario':<20} {'Dealer Flow':>15} {'Direction':>12} {'Notional':>15}")
    print("-" * 65)

    for key, label, description in levels:
        flow_data = hedging.get(key, {})
        if not flow_data and isinstance(hedging, dict):
            # Some API versions return flat keys
            shares = hedging.get(f"shares_{key}")
            direction = hedging.get(f"direction_{key}")
            notional = hedging.get(f"notional_{key}")
        else:
            shares = flow_data.get("shares") if isinstance(flow_data, dict) else None
            direction = flow_data.get("direction") if isinstance(flow_data, dict) else None
            notional = flow_data.get("notional") if isinstance(flow_data, dict) else None

        if shares is not None:
            shares_str = f"{shares:>+,.0f} shares"
            dir_str = direction or ("BUY" if shares > 0 else "SELL")
            notional_str = f"${abs(notional):,.0f}" if notional else "—"
            print(f"  {label} ({description:<15}) {shares_str:>15} {dir_str:>12} {notional_str:>15}")
        else:
            print(f"  {label:<20} {'No data':>15}")

    print()

    # Summary hedging pressure — which direction faces more structural flow?
    total_buy_pressure = hedging.get("total_buy_pressure")
    total_sell_pressure = hedging.get("total_sell_pressure")
    net_hedging_bias = hedging.get("net_bias", hedging.get("net_hedging_bias"))

    if total_buy_pressure is not None:
        print(f"Total Buy Pressure:  ${total_buy_pressure:,.0f} notional")
    if total_sell_pressure is not None:
        print(f"Total Sell Pressure: ${total_sell_pressure:,.0f} notional")
    if net_hedging_bias:
        print(f"Net Hedging Bias:    {net_hedging_bias}")

    print()
    print("=== Trading Implications ===")
    print("Scenarios with large positive flows (dealer BUY):")
    print("  These are structural support levels — dealers will mechanically buy")
    print("  on dips to this level, creating a cushion for downside moves.")
    print()
    print("Scenarios with large negative flows (dealer SELL):")
    print("  These are structural resistance levels — dealers will mechanically sell")
    print("  into rallies to this level, creating a ceiling for upside moves.")
    print()
    print("When dealer flows are large in both directions, the range is well-defined.")
    print("When flows are asymmetric, price may break out in the low-resistance direction.")
    print()
    print("Reference: https://flashalpha.com/articles/guide-to-0dte-trading-strategies-real-time-data")


if __name__ == "__main__":
    show_dealer_hedging_flows("SPY")
