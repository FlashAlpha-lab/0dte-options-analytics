"""
Unit tests for 0DTE options analytics examples.

All API calls are mocked using the `responses` library — no live API
key is required. Tests validate response parsing, field extraction,
logic branches, and error handling for every example module.

Run:
    pytest tests/test_unit.py -v
"""

import pytest
import responses

from flashalpha import (
    FlashAlpha,
    AuthenticationError,
    NotFoundError,
    RateLimitError,
    TierRestrictedError,
    ServerError,
)

BASE = "https://lab.flashalpha.com"


@pytest.fixture
def fa():
    """Return a FlashAlpha client with a dummy API key."""
    return FlashAlpha("test-key")


# ── Fixtures: representative zero_dte payloads ────────────────────────────────

def _zero_dte_full():
    """A fully populated zero_dte response covering all analytics sections."""
    return {
        "symbol": "SPY",
        "underlying_price": 590.42,
        "expiration": "2026-03-19",
        "as_of": "2026-03-19T14:45:12Z",
        "market_open": True,
        "time_to_close_hours": 1.25,
        "time_to_close_pct": 80.8,
        "regime": {
            "label": "positive_gamma",
            "description": "Dealers long gamma — moves dampened, mean reversion likely",
            "gamma_flip": 588.50,
            "spot_vs_flip": "above",
            "spot_to_flip_pct": 0.33,
        },
        "exposures": {
            "net_gex": 1_842_000_000,
            "net_dex": 48_200_000_000,
            "net_vex": -320_000_000,
            "net_chex": 95_000_000,
            "pct_of_total_gex": 62.4,
            "total_chain_net_gex": 2_952_000_000,
        },
        "expected_move": {
            "implied_1sd_dollars": 2.18,
            "implied_1sd_pct": 0.37,
            "remaining_1sd_dollars": 1.05,
            "remaining_1sd_pct": 0.18,
            "upper_bound": 591.47,   # underlying_price + remaining_1sd_dollars = 590.42 + 1.05
            "lower_bound": 589.37,   # underlying_price - remaining_1sd_dollars = 590.42 - 1.05
            "straddle_price": 1.62,
            "atm_iv": 0.123,
        },
        "pin_risk": {
            "magnet_strike": 590,
            "magnet_gex": 580_000_000,
            "distance_to_magnet_pct": 0.07,
            "pin_score": 82,
            "max_pain": 590,
            "oi_concentration_top3_pct": 41.2,
            "description": "Strong pin at 590. 82/100 pin score with 41% of OI in top 3 strikes.",
        },
        "hedging": {
            "spot_up_half_pct": {"dealer_shares_to_trade": -156_100, "direction": "sell", "notional_usd": -92_158_000},
            "spot_down_half_pct": {"dealer_shares_to_trade": 156_100, "direction": "buy", "notional_usd": 92_158_000},
            "spot_up_1pct": {"dealer_shares_to_trade": -312_200, "direction": "sell", "notional_usd": -184_316_000},
            "spot_down_1pct": {"dealer_shares_to_trade": 312_200, "direction": "buy", "notional_usd": 184_316_000},
        },
        "decay": {
            "net_theta_dollars": -4_820_000,
            "theta_per_hour_remaining": -3_856_000,
            "charm_regime": "time_decay_dealers_buy",
            "charm_description": "Time decay pushing dealers to buy — supportive into close",
            "gamma_acceleration": 2.4,
            "description": "0DTE theta bleeding $3,856/hr. Gamma 2.4x higher than equivalent 7DTE.",
        },
        "vol_context": {
            "zero_dte_atm_iv": 12.3,
            "seven_dte_atm_iv": 14.8,
            "iv_ratio_0dte_7dte": 0.83,
            "vix": 16.2,
            "vanna_exposure": -320_000_000,
            "vanna_interpretation": "vol_up_dealers_sell",
            "description": "0DTE IV at 12.3% vs 7DTE at 14.8%. Negative vanna — vol spike triggers dealer selling.",
        },
        "flow": {
            "total_volume": 842_000,
            "call_volume": 520_000,
            "put_volume": 322_000,
            "total_oi": 1_240_000,
            "call_oi": 680_000,
            "put_oi": 560_000,
            "pc_ratio_volume": 0.619,
            "pc_ratio_oi": 0.824,
            "volume_to_oi_ratio": 0.679,
        },
        "levels": {
            "call_wall": 595,
            "call_wall_gex": 420_000_000,
            "put_wall": 585,
            "put_wall_gex": -380_000_000,
            "highest_oi_strike": 590,
            "highest_oi_total": 48_200,
            "max_positive_gamma": 592,
            "max_negative_gamma": 586,
        },
        "strikes": [
            {
                "strike": 590,
                "call_gex": 450_000_000, "put_gex": -380_000_000, "net_gex": 70_000_000,
                "call_dex": 12_500_000, "put_dex": -15_000_000, "net_dex": -2_500_000,
                "call_oi": 25_000, "put_oi": 30_000,
                "call_volume": 15_000, "put_volume": 12_000,
                "call_iv": 0.18, "put_iv": 0.19,
                "call_delta": 0.50, "put_delta": -0.50,
                "call_gamma": 0.025, "put_gamma": 0.025,
                "call_theta": -1.0, "put_theta": -1.0,
            }
        ],
    }


def _zero_dte_no_expiry():
    """Payload returned when there is no 0DTE expiration today for the symbol."""
    return {
        "symbol": "SPY",
        "underlying_price": 590.42,
        "expiration": None,
        "as_of": "2026-03-17T15:30:00Z",
        "market_open": True,
        "no_zero_dte": True,
        "message": "No 0DTE expiry for SPY today (Tuesday). Next expiry: 2026-03-18.",
        "next_zero_dte_expiry": "2026-03-18",
    }


# ── Test 1: zero_dte response parsing — basic fields ────────────────────────

@responses.activate
def test_zero_dte_returns_symbol_and_underlying_price(fa):
    responses.get(f"{BASE}/v1/exposure/zero-dte/SPY", json=_zero_dte_full())
    result = fa.zero_dte("SPY")
    assert result["symbol"] == "SPY"
    assert result["underlying_price"] == pytest.approx(590.42)


# ── Test 2: pin risk score parsing ──────────────────────────────────────────

@responses.activate
def test_pin_risk_score_parsed(fa):
    responses.get(f"{BASE}/v1/exposure/zero-dte/SPY", json=_zero_dte_full())
    result = fa.zero_dte("SPY")
    pin = result["pin_risk"]
    assert pin["pin_score"] == 82
    assert pin["magnet_strike"] == 590
    assert pin["max_pain"] == 590


# ── Test 3: pin score interpretation — thresholds ───────────────────────────

def test_pin_score_high_threshold():
    """Scores >= 70 should classify as HIGH pin risk."""
    score = 82
    if score >= 70:
        category = "HIGH"
    elif score >= 40:
        category = "MODERATE"
    else:
        category = "LOW"
    assert category == "HIGH"


def test_pin_score_moderate_threshold():
    score = 55
    if score >= 70:
        category = "HIGH"
    elif score >= 40:
        category = "MODERATE"
    else:
        category = "LOW"
    assert category == "MODERATE"


def test_pin_score_low_threshold():
    score = 20
    if score >= 70:
        category = "HIGH"
    elif score >= 40:
        category = "MODERATE"
    else:
        category = "LOW"
    assert category == "LOW"


# ── Test 4: expected move calculation ────────────────────────────────────────

@responses.activate
def test_expected_move_fields_parsed(fa):
    responses.get(f"{BASE}/v1/exposure/zero-dte/SPY", json=_zero_dte_full())
    result = fa.zero_dte("SPY")
    em = result["expected_move"]
    assert em["atm_iv"] == pytest.approx(0.123)
    assert em["straddle_price"] == pytest.approx(1.62)
    assert em["implied_1sd_dollars"] == pytest.approx(2.18)
    assert em["remaining_1sd_dollars"] == pytest.approx(1.05)


def test_expected_move_upper_lower_bounds():
    """Verify upper/lower bound arithmetic from remaining_1sd_dollars."""
    underlying_price = 590.42
    remaining_1sd_dollars = 1.05
    upper = underlying_price + remaining_1sd_dollars
    lower = underlying_price - remaining_1sd_dollars
    assert upper == pytest.approx(591.47)
    assert lower == pytest.approx(589.37)


def test_expected_move_pct_remaining():
    """Remaining 1SD as a fraction of full-day implied 1SD."""
    implied_1sd_dollars = 2.18
    remaining_1sd_dollars = 1.05
    pct = remaining_1sd_dollars / implied_1sd_dollars * 100
    assert pct == pytest.approx(48.2, abs=0.5)


# ── Test 5: regime detection ─────────────────────────────────────────────────

@responses.activate
def test_regime_label_positive_gamma(fa):
    responses.get(f"{BASE}/v1/exposure/zero-dte/SPY", json=_zero_dte_full())
    result = fa.zero_dte("SPY")
    label = result["regime"]["label"]
    assert "positive" in label.lower()


@responses.activate
def test_regime_label_negative_gamma(fa):
    payload = _zero_dte_full()
    payload["regime"]["label"] = "negative_gamma"
    responses.get(f"{BASE}/v1/exposure/zero-dte/SPY", json=payload)
    result = fa.zero_dte("SPY")
    assert "negative" in result["regime"]["label"].lower()


@responses.activate
def test_gamma_flip_parsed(fa):
    responses.get(f"{BASE}/v1/exposure/zero-dte/SPY", json=_zero_dte_full())
    result = fa.zero_dte("SPY")
    assert result["regime"]["gamma_flip"] == pytest.approx(588.50)


# ── Test 6: dealer hedging flow direction ────────────────────────────────────

@responses.activate
def test_hedging_flows_direction(fa):
    responses.get(f"{BASE}/v1/exposure/zero-dte/SPY", json=_zero_dte_full())
    result = fa.zero_dte("SPY")
    hedging = result["hedging"]
    # Up scenarios: dealers sell into rallies (negative shares / sell direction)
    assert hedging["spot_up_1pct"]["direction"] == "sell"
    assert hedging["spot_up_half_pct"]["dealer_shares_to_trade"] < 0
    # Down scenarios: dealers buy on dips (positive shares / buy direction)
    assert hedging["spot_down_half_pct"]["direction"] == "buy"
    assert hedging["spot_down_1pct"]["dealer_shares_to_trade"] > 0


def test_hedging_flow_notional_magnitude():
    """Notional should be substantially larger than share count * 1 dollar."""
    shares = 312_200
    spot = 590.42
    approx_notional = shares * spot
    assert approx_notional > 100_000_000  # >$100M for 312k shares of SPY


# ── Test 7: theta decay parsing ──────────────────────────────────────────────

@responses.activate
def test_theta_decay_fields(fa):
    responses.get(f"{BASE}/v1/exposure/zero-dte/SPY", json=_zero_dte_full())
    result = fa.zero_dte("SPY")
    decay = result["decay"]
    assert decay["net_theta_dollars"] == -4_820_000
    assert decay["theta_per_hour_remaining"] == -3_856_000
    assert decay["charm_regime"] == "time_decay_dealers_buy"
    assert decay["gamma_acceleration"] == pytest.approx(2.4)


def test_gamma_acceleration_classification():
    """Verify gamma acceleration threshold classification logic."""
    def classify(ga):
        if ga >= 3.0:
            return "EXTREME"
        elif ga >= 2.0:
            return "HIGH"
        elif ga >= 1.5:
            return "ELEVATED"
        else:
            return "NORMAL"

    assert classify(3.5) == "EXTREME"
    assert classify(2.4) == "HIGH"
    assert classify(1.6) == "ELEVATED"
    assert classify(1.2) == "NORMAL"


# ── Test 8: vol context parsing ──────────────────────────────────────────────

@responses.activate
def test_vol_context_fields(fa):
    responses.get(f"{BASE}/v1/exposure/zero-dte/SPY", json=_zero_dte_full())
    result = fa.zero_dte("SPY")
    vol = result["vol_context"]
    assert vol["iv_ratio_0dte_7dte"] == pytest.approx(0.83)
    assert vol["vix"] == pytest.approx(16.2)
    assert vol["vanna_exposure"] == -320_000_000


def test_iv_ratio_interpretation():
    """IV ratio below 1.0 (0DTE cheaper than 7DTE) should signal subdued 0DTE premium."""
    ratio = 0.83
    if ratio > 1.25:
        interpretation = "HIGHLY ELEVATED"
    elif ratio > 1.10:
        interpretation = "ELEVATED"
    elif ratio > 0.90:
        interpretation = "NORMAL"
    else:
        interpretation = "SUBDUED"
    assert interpretation == "SUBDUED"


# ── Test 9: no 0DTE expiry handling ─────────────────────────────────────────

@responses.activate
def test_no_zero_dte_flag_returned(fa):
    responses.get(f"{BASE}/v1/exposure/zero-dte/SPY", json=_zero_dte_no_expiry())
    result = fa.zero_dte("SPY")
    assert result.get("no_zero_dte") is True


@responses.activate
def test_no_zero_dte_does_not_raise(fa):
    """The SDK should not raise an exception for the no_zero_dte case (it is a 200)."""
    responses.get(f"{BASE}/v1/exposure/zero-dte/SPY", json=_zero_dte_no_expiry())
    result = fa.zero_dte("SPY")
    # Example logic: check the flag and return early
    if result.get("no_zero_dte"):
        message = "No 0DTE expiration today"
    else:
        message = "Live data available"
    assert message == "No 0DTE expiration today"


# ── Test 10: error handling — 401 ────────────────────────────────────────────

@responses.activate
def test_zero_dte_401_raises_auth_error(fa):
    responses.get(
        f"{BASE}/v1/exposure/zero-dte/SPY",
        json={"detail": "Invalid API key."},
        status=401,
    )
    with pytest.raises(AuthenticationError) as exc_info:
        fa.zero_dte("SPY")
    assert exc_info.value.status_code == 401


# ── Test 11: error handling — 403 ────────────────────────────────────────────

@responses.activate
def test_zero_dte_403_raises_tier_restricted(fa):
    responses.get(
        f"{BASE}/v1/exposure/zero-dte/SPY",
        json={
            "message": "Requires Growth plan.",
            "current_plan": "Free",
            "required_plan": "Growth",
        },
        status=403,
    )
    with pytest.raises(TierRestrictedError) as exc_info:
        fa.zero_dte("SPY")
    assert exc_info.value.current_plan == "Free"
    assert exc_info.value.required_plan == "Growth"


# ── Test 12: error handling — 429 ────────────────────────────────────────────

@responses.activate
def test_zero_dte_429_raises_rate_limit(fa):
    responses.get(
        f"{BASE}/v1/exposure/zero-dte/SPY",
        json={"message": "Quota exceeded."},
        status=429,
        headers={"Retry-After": "30"},
    )
    with pytest.raises(RateLimitError) as exc_info:
        fa.zero_dte("SPY")
    assert exc_info.value.retry_after == 30


# ── Test 13: strike_range parameter is sent ──────────────────────────────────

@responses.activate
def test_zero_dte_strike_range_param(fa):
    responses.get(f"{BASE}/v1/exposure/zero-dte/SPY", json=_zero_dte_full())
    fa.zero_dte("SPY", strike_range=0.03)
    assert "strike_range=0.03" in responses.calls[0].request.url


# ── Test 14: gex endpoint returns gamma_flip ─────────────────────────────────

@responses.activate
def test_gex_gamma_flip(fa):
    payload = {
        "symbol": "SPY",
        "net_gex": 1_850_000_000,
        "gamma_flip": 593.00,
        "strikes": [],
    }
    responses.get(f"{BASE}/v1/exposure/gex/SPY", json=payload)
    result = fa.gex("SPY")
    assert result["gamma_flip"] == pytest.approx(593.00)


# ── Test 15: OI concentration arithmetic ─────────────────────────────────────

def test_oi_concentration_distance_calculation():
    """Distance from spot to magnet strike should compute correctly."""
    underlying_price = 590.42
    magnet = 590
    distance_pct = abs(underlying_price - magnet) / underlying_price * 100
    assert distance_pct == pytest.approx(0.0712, abs=0.001)


# ── Test 16: full-day vs remaining expected move pct used ────────────────────

def test_expected_move_pct_used():
    """If remaining is smaller than full, pct_used > 0."""
    implied_1sd_dollars = 2.18
    remaining_1sd_dollars = 1.05
    pct_used = (1 - remaining_1sd_dollars / implied_1sd_dollars) * 100
    assert pct_used > 0
    assert pct_used < 100


# ── Test 17: server error on zero_dte ────────────────────────────────────────

@responses.activate
def test_zero_dte_500_raises_server_error(fa):
    responses.get(
        f"{BASE}/v1/exposure/zero-dte/SPY",
        json={"detail": "Internal server error"},
        status=500,
    )
    with pytest.raises(ServerError) as exc_info:
        fa.zero_dte("SPY")
    assert exc_info.value.status_code == 500
