import pandas as pd

from pipeline.scoring.hype_score import calculate_score_bundle, weighted_score


CONFIG = {
    "component_min_coverage": {
        "attention": 0.5,
        "trading": 0.5,
        "retail_proxy": 0.5,
        "impact": 0.5,
        "hype": 0.25,
    },
    "weights": {
        "attention": {"wikipedia_attention_shock": 0.55, "social_attention": 0.45},
        "trading": {"unusual_volume": 0.60, "absolute_daily_move": 0.25, "volatility_shock": 0.15},
        "retail_proxy": {"short_term_activity": 0.50, "short_sale_volume_change": 0.30, "additional_retail_proxies": 0.20},
        "impact": {"price_move_per_dollar_volume": 0.45, "liquidity_sensitivity": 0.30, "attention_shock_size": 0.25},
        "hype": {"attention_score": 0.40, "trading_score": 0.35, "retail_proxy_score": 0.15, "impact_score": 0.10},
    },
}


def test_weighted_score_renormalizes_available_components() -> None:
    result = weighted_score(
        {"a": 80, "b": None}, {"a": 0.6, "b": 0.4}, minimum_coverage=0.5
    )
    assert result.value == 80
    assert result.coverage == 0.6


def test_weighted_score_rejects_insufficient_coverage() -> None:
    result = weighted_score(
        {"a": None, "b": 90}, {"a": 0.8, "b": 0.2}, minimum_coverage=0.5
    )
    assert result.value is None


def test_score_bundle_handles_missing_social_without_zero_fill() -> None:
    row = pd.Series(
        {
            "wikipedia_attention_score": 90,
            "social_attention_score": None,
            "unusual_volume_score": 80,
            "absolute_move_score": 70,
            "volatility_shock_score": 60,
            "short_term_activity_score": 75,
            "short_sale_change_score": 50,
            "additional_retail_proxy_score": None,
            "price_impact_score": 55,
            "liquidity_sensitivity_score": 45,
            "attention_shock_size_score": 90,
        }
    )
    scores = calculate_score_bundle(row, CONFIG)
    assert scores["attention_score"] == 90
    assert 0 <= scores["hype_score"] <= 100
