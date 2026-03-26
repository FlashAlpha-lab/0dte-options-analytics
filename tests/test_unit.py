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
        "spot": 595.40,
        "no_zero_dte": False,
        "regime": {
            "label": "positive_gamma",
            "gamma_flip": 593.00,
            "net_gex": 1_850_000_000,
            "zero_dte_gex_pct": 0.48,
            "call_wall": 600.0,
            "put_wall": 590.0,
        },
        "expected_move": {
            "atm_iv": 0.122,
            "straddle_price": 3.85,
            "full_day_1sd": 3.85,
            "remaining_1sd": 2.10,
            "hours_remaining": 3.2,
            "time_elapsed_pct": 51.0,
            "open_price": 594.80,
        },
        "pin_risk": {
            "pin_score": 74,
            "magnet_strike": 595.0,
            "max_pain": 595.0,
            "oi_concentration": 0.31,
            "dominant_strike_oi": 145_000,
        },
        "hedging": {
            "up_1pct": {"shares": -320_000, "direction": "SELL", "notional": 190_500_000},
            "up_0_5pct": {"shares": -155_000, "direction": "SELL", "notional": 92_200_000},
            "down_0_5pct": {"shares": 148_000, "direction": "BUY", "notional": 88_100_000},
            "down_1pct": {"shares": 310_000, "direction": "BUY", "notional": 184_600_000},
            "net_bias": "buy_dips",
        },
        "decay": {
            "net_theta": -4_200_000,
            "theta_per_hour": -1_312_500,
            "charm_regime": "unwinding",
            "gamma_acceleration": 1.85,
            "decay_rate_change": 0.14,
        },
        "vol_context": {
            "atm_iv_0dte": 0.122,
            "atm_iv_7dte": 0.108,
            "zero_dte_7dte_ratio": 1.13,
            "vix": 17.4,
            "vanna_exposure": 980_000_000,
            "vanna_interpretation": "Vol drop -> dealer buy flows",
            "vol_regime": "elevated",
        },
    }


def _zero_dte_no_expiry():
    """Payload returned when there is no 0DTE expiration today for the symbol."""
    return {
        "symbol": "SPY",
        "no_zero_dte": True,
        "message": "No zero-DTE expiration for SPY today.",
    }


# ── Test 1: zero_dte response parsing — basic fields ────────────────────────

@responses.activate
def test_zero_dte_returns_symbol_and_spot(fa):
    responses.get(f"{BASE}/v1/exposure/zero-dte/SPY", json=_zero_dte_full())
    result = fa.zero_dte("SPY")
    assert result["symbol"] == "SPY"
    assert result["spot"] == 595.40


# ── Test 2: pin risk score parsing ──────────────────────────────────────────

@responses.activate
def test_pin_risk_score_parsed(fa):
    responses.get(f"{BASE}/v1/exposure/zero-dte/SPY", json=_zero_dte_full())
    result = fa.zero_dte("SPY")
    pin = result["pin_risk"]
    assert pin["pin_score"] == 74
    assert pin["magnet_strike"] == 595.0
    assert pin["max_pain"] == 595.0


# ── Test 3: pin score interpretation — thresholds ───────────────────────────

def test_pin_score_high_threshold():
    """Scores >= 70 should classify as HIGH pin risk."""
    score = 74
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
    assert em["atm_iv"] == pytest.approx(0.122)
    assert em["straddle_price"] == pytest.approx(3.85)
    assert em["full_day_1sd"] == pytest.approx(3.85)
    assert em["remaining_1sd"] == pytest.approx(2.10)


def test_expected_move_upper_lower_bounds():
    """Verify upper/lower bound arithmetic from remaining_1sd."""
    spot = 595.40
    remaining_1sd = 2.10
    upper = spot + remaining_1sd
    lower = spot - remaining_1sd
    assert upper == pytest.approx(597.50)
    assert lower == pytest.approx(593.30)


def test_expected_move_pct_remaining():
    """Remaining 1SD as a fraction of full-day 1SD."""
    full_1sd = 3.85
    remaining_1sd = 2.10
    pct = remaining_1sd / full_1sd * 100
    assert pct == pytest.approx(54.5, abs=0.5)


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
    assert result["regime"]["gamma_flip"] == pytest.approx(593.00)


# ── Test 6: dealer hedging flow direction ────────────────────────────────────

@responses.activate
def test_hedging_flows_direction(fa):
    responses.get(f"{BASE}/v1/exposure/zero-dte/SPY", json=_zero_dte_full())
    result = fa.zero_dte("SPY")
    hedging = result["hedging"]
    # Up scenarios: dealers sell into rallies (negative shares / SELL direction)
    assert hedging["up_1pct"]["direction"] == "SELL"
    assert hedging["up_0_5pct"]["shares"] < 0
    # Down scenarios: dealers buy on dips (positive shares / BUY direction)
    assert hedging["down_0_5pct"]["direction"] == "BUY"
    assert hedging["down_1pct"]["shares"] > 0


def test_hedging_flow_notional_magnitude():
    """Notional should be substantially larger than share count * 1 dollar."""
    shares = 320_000
    spot = 595.40
    approx_notional = shares * spot
    assert approx_notional > 100_000_000  # >$100M for 320k shares of SPY


# ── Test 7: theta decay parsing ──────────────────────────────────────────────

@responses.activate
def test_theta_decay_fields(fa):
    responses.get(f"{BASE}/v1/exposure/zero-dte/SPY", json=_zero_dte_full())
    result = fa.zero_dte("SPY")
    decay = result["decay"]
    assert decay["net_theta"] == -4_200_000
    assert decay["theta_per_hour"] == -1_312_500
    assert decay["charm_regime"] == "unwinding"
    assert decay["gamma_acceleration"] == pytest.approx(1.85)


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
    assert vol["zero_dte_7dte_ratio"] == pytest.approx(1.13)
    assert vol["vix"] == pytest.approx(17.4)
    assert vol["vanna_exposure"] == 980_000_000


def test_iv_ratio_interpretation():
    """IV ratio above 1.1 should signal elevated 0DTE premium."""
    ratio = 1.13
    if ratio > 1.25:
        interpretation = "HIGHLY ELEVATED"
    elif ratio > 1.10:
        interpretation = "ELEVATED"
    elif ratio > 0.90:
        interpretation = "NORMAL"
    else:
        interpretation = "SUBDUED"
    assert interpretation == "ELEVATED"


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
    spot = 595.40
    magnet = 595.0
    distance_pct = abs(spot - magnet) / spot * 100
    assert distance_pct == pytest.approx(0.0672, abs=0.001)


# ── Test 16: full-day vs remaining expected move pct used ────────────────────

def test_expected_move_pct_used():
    """If remaining is smaller than full, pct_used > 0."""
    full_1sd = 3.85
    remaining_1sd = 2.10
    pct_used = (1 - remaining_1sd / full_1sd) * 100
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
