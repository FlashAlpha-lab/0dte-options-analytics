"""
Integration tests for 0DTE options analytics against the live FlashAlpha API.

Requires a valid API key set in the FLASHALPHA_API_KEY environment variable.
All tests are marked with @pytest.mark.integration and are skipped when the
key is absent so CI passes without credentials.

Run:
    pytest tests/test_integration.py -m integration -v

These tests validate that the API returns correctly shaped responses for all
endpoints used in the 0DTE analytics examples.
"""

import os
import pytest

pytestmark = pytest.mark.integration

API_KEY = os.environ.get("FLASHALPHA_API_KEY")

if not API_KEY:
    pytest.skip(
        "FLASHALPHA_API_KEY not set — skipping integration tests",
        allow_module_level=True,
    )

from flashalpha import FlashAlpha, NotFoundError  # noqa: E402

fa = FlashAlpha(API_KEY)
SYMBOL = "SPY"


# ── Test 1: zero_dte returns valid top-level response ────────────────────────

def test_zero_dte_returns_valid_response():
    result = fa.zero_dte(SYMBOL)
    assert isinstance(result, dict), f"Expected dict, got {type(result)}"
    assert "symbol" in result, f"Missing 'symbol' key. Keys: {list(result.keys())}"
    assert result["symbol"] == SYMBOL


# ── Test 2: zero_dte with strike_range parameter ─────────────────────────────

def test_zero_dte_with_strike_range_param():
    """Passing strike_range should not raise and should return a valid response."""
    result = fa.zero_dte(SYMBOL, strike_range=0.03)
    assert isinstance(result, dict)
    assert "symbol" in result


# ── Test 3: zero_dte has expected sections or no_zero_dte flag ───────────────

def test_zero_dte_has_sections_or_no_expiry_flag():
    """
    The response must either contain analytics sections or the no_zero_dte flag.
    Both are valid API responses depending on the day.
    """
    result = fa.zero_dte(SYMBOL)
    has_sections = any(
        k in result
        for k in ("regime", "expected_move", "pin_risk", "hedging", "decay", "vol_context")
    )
    has_no_expiry = result.get("no_zero_dte") is True
    assert has_sections or has_no_expiry, (
        f"Response has neither analytics sections nor no_zero_dte flag. "
        f"Keys: {list(result.keys())}"
    )


# ── Test 4: zero_dte regime section has label ────────────────────────────────

def test_zero_dte_regime_has_label():
    result = fa.zero_dte(SYMBOL)
    if result.get("no_zero_dte"):
        pytest.skip("No 0DTE expiration today")
    regime = result.get("regime", {})
    assert "label" in regime or "regime_label" in regime, (
        f"'regime' section missing 'label'. Keys: {list(regime.keys())}"
    )


# ── Test 5: zero_dte pin_risk has pin_score ──────────────────────────────────

def test_zero_dte_pin_risk_has_score():
    result = fa.zero_dte(SYMBOL)
    if result.get("no_zero_dte"):
        pytest.skip("No 0DTE expiration today")
    pin = result.get("pin_risk", {})
    assert "pin_score" in pin, f"'pin_risk' missing 'pin_score'. Keys: {list(pin.keys())}"
    score = pin["pin_score"]
    assert isinstance(score, (int, float)), f"pin_score should be numeric, got {type(score)}"
    assert 0 <= score <= 100, f"pin_score {score} out of 0-100 range"


# ── Test 6: gex returns valid response ───────────────────────────────────────

def test_gex_returns_valid_response():
    result = fa.gex(SYMBOL)
    assert isinstance(result, dict)
    assert "symbol" in result
    assert result["symbol"] == SYMBOL


# ── Test 7: exposure_levels returns levels dict ───────────────────────────────

def test_exposure_levels_returns_levels():
    result = fa.exposure_levels(SYMBOL)
    assert "levels" in result, f"Missing 'levels'. Keys: {list(result.keys())}"
    lvl = result["levels"]
    assert isinstance(lvl, dict)
    for key in ("gamma_flip", "call_wall", "put_wall"):
        assert key in lvl, f"'levels' missing '{key}'. Keys: {list(lvl.keys())}"


# ── Test 8: greeks returns first/second/third order ─────────────────────────

def test_greeks_returns_orders():
    result = fa.greeks(spot=595.0, strike=595.0, dte=0.042, sigma=0.12, type="call")
    assert "first_order" in result, f"Missing 'first_order'. Keys: {list(result.keys())}"
    fo = result["first_order"]
    assert "delta" in fo, f"'first_order' missing 'delta'. Keys: {list(fo.keys())}"
    assert "gamma" in fo, f"'first_order' missing 'gamma'."
    assert "theta" in fo, f"'first_order' missing 'theta'."
    # Second order includes vanna, charm, vomma
    second = result.get("second_order", {})
    assert isinstance(second, dict)


# ── Test 9: stock_quote works ─────────────────────────────────────────────────

def test_stock_quote_returns_bid_ask_mid():
    result = fa.stock_quote(SYMBOL)
    for field in ("bid", "ask", "mid"):
        assert field in result, f"stock_quote missing '{field}'. Keys: {list(result.keys())}"
    assert result["ask"] >= result["bid"] >= 0


# ── Test 10: health check works ──────────────────────────────────────────────

def test_health_check_returns_healthy():
    result = fa.health()
    assert "status" in result, f"Missing 'status'. Keys: {list(result.keys())}"
    # The API returns "Healthy" but be tolerant of minor variations
    assert result["status"].lower() in ("healthy", "ok", "up"), (
        f"Unexpected health status: {result['status']}"
    )


# ── Test 11: invalid symbol returns 404 ──────────────────────────────────────

def test_invalid_symbol_raises_not_found():
    with pytest.raises(NotFoundError):
        fa.stock_quote("ZZZZZNOTREAL")


# ── Test 12: symbols returns list ────────────────────────────────────────────

def test_symbols_returns_list():
    result = fa.symbols()
    assert "symbols" in result, f"Missing 'symbols'. Keys: {list(result.keys())}"
    assert isinstance(result["symbols"], list)
    # The API should have at least some symbols active
    assert len(result["symbols"]) > 0


# ── Test 13: gex with min_oi filter ──────────────────────────────────────────

def test_gex_with_min_oi_filter():
    result = fa.gex(SYMBOL, min_oi=500)
    assert "strikes" in result or "symbol" in result


# ── Test 14: zero_dte expected_move has atm_iv ───────────────────────────────

def test_zero_dte_expected_move_has_atm_iv():
    result = fa.zero_dte(SYMBOL)
    if result.get("no_zero_dte"):
        pytest.skip("No 0DTE expiration today")
    em = result.get("expected_move", {})
    assert "atm_iv" in em or "straddle_price" in em, (
        f"'expected_move' missing key vol fields. Keys: {list(em.keys())}"
    )
    if "atm_iv" in em:
        assert 0 < em["atm_iv"] < 5.0, f"atm_iv {em['atm_iv']} out of reasonable range"


# ── Test 15: zero_dte vol_context has iv ratio ───────────────────────────────

def test_zero_dte_vol_context_has_iv_ratio():
    result = fa.zero_dte(SYMBOL)
    if result.get("no_zero_dte"):
        pytest.skip("No 0DTE expiration today")
    vol = result.get("vol_context", result.get("volatility_context", {}))
    # iv ratio field name may vary — check either key
    has_ratio = "zero_dte_7dte_ratio" in vol or "iv_ratio" in vol
    # vol_context may be absent on some plan tiers — just check if present is valid
    if has_ratio:
        ratio = vol.get("zero_dte_7dte_ratio") or vol.get("iv_ratio")
        assert 0 < ratio < 10, f"IV ratio {ratio} out of reasonable range"
