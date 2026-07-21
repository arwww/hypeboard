from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from pipeline.scoring.normalization import clipped


@dataclass(frozen=True, slots=True)
class WeightedScore:
    value: float | None
    coverage: float
    available_components: tuple[str, ...]


def weighted_score(
    values: dict[str, float | None],
    weights: dict[str, float],
    *,
    minimum_coverage: float,
) -> WeightedScore:
    total_weight = sum(weights.values())
    available = {
        name: float(value)
        for name, value in values.items()
        if name in weights and value is not None and not pd.isna(value)
    }
    available_weight = sum(weights[name] for name in available)
    coverage = available_weight / total_weight if total_weight else 0.0
    if coverage + 1e-12 < minimum_coverage or not available:
        return WeightedScore(None, round(coverage, 4), tuple(available))
    value = sum(available[name] * weights[name] for name in available) / available_weight
    return WeightedScore(clipped(value), round(coverage, 4), tuple(available))


def calculate_score_bundle(row: pd.Series, config: dict) -> dict[str, object]:
    minimums = config["component_min_coverage"]
    weights = config["weights"]

    attention = weighted_score(
        {
            "wikipedia_attention_shock": row.get("wikipedia_attention_score"),
            "social_attention": row.get("social_attention_score"),
        },
        weights["attention"],
        minimum_coverage=minimums["attention"],
    )
    trading = weighted_score(
        {
            "unusual_volume": row.get("unusual_volume_score"),
            "absolute_daily_move": row.get("absolute_move_score"),
            "volatility_shock": row.get("volatility_shock_score"),
        },
        weights["trading"],
        minimum_coverage=minimums["trading"],
    )
    retail = weighted_score(
        {
            "short_term_activity": row.get("short_term_activity_score"),
            "short_sale_volume_change": row.get("short_sale_change_score"),
            "additional_retail_proxies": row.get("additional_retail_proxy_score"),
        },
        weights["retail_proxy"],
        minimum_coverage=minimums["retail_proxy"],
    )
    impact = weighted_score(
        {
            "price_move_per_dollar_volume": row.get("price_impact_score"),
            "liquidity_sensitivity": row.get("liquidity_sensitivity_score"),
            "attention_shock_size": row.get("attention_shock_size_score"),
        },
        weights["impact"],
        minimum_coverage=minimums["impact"],
    )
    hype = weighted_score(
        {
            "attention_score": attention.value,
            "trading_score": trading.value,
            "retail_proxy_score": retail.value,
            "impact_score": impact.value,
        },
        weights["hype"],
        minimum_coverage=minimums["hype"],
    )
    return {
        "attention_score": attention.value,
        "trading_score": trading.value,
        "retail_proxy_score": retail.value,
        "impact_score": impact.value,
        "hype_score": hype.value,
        "score_coverage": hype.coverage,
        "component_coverage": {
            "attention": attention.coverage,
            "trading": trading.coverage,
            "retail_proxy": retail.coverage,
            "impact": impact.coverage,
        },
    }
