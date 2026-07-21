import math

import pandas as pd

from pipeline.scoring.normalization import (
    add_rolling_robust_features,
    percentile_rank,
    robust_z_score,
)


def test_robust_z_detects_positive_outlier() -> None:
    history = [10, 11, 10, 9, 10, 11, 10, 9, 10, 10, 11, 9]
    assert robust_z_score(30, history, min_observations=10) == 8.0


def test_robust_z_returns_none_with_insufficient_history() -> None:
    assert robust_z_score(20, [10, 11], min_observations=3) is None


def test_rolling_features_use_prior_observations_only() -> None:
    frame = pd.DataFrame(
        {
            "symbol": ["AAA"] * 12,
            "date": pd.date_range("2026-01-01", periods=12).date,
            "value": [10] * 11 + [100],
        }
    )
    result = add_rolling_robust_features(
        frame,
        group_column="symbol",
        date_column="date",
        value_column="value",
        prefix="test",
        window=10,
        min_observations=10,
    )
    assert result.iloc[-1]["test_median"] == 10
    assert result.iloc[-1]["test_robust_z"] == 8


def test_percentile_rank_keeps_missing_values_missing() -> None:
    values = pd.Series([1.0, math.nan, 3.0])
    ranked = percentile_rank(values)
    assert pd.isna(ranked.iloc[1])
    assert ranked.iloc[2] == 100
