from __future__ import annotations

import math
from collections.abc import Iterable

import numpy as np
import pandas as pd


MAD_SCALE = 1.4826


def clipped(value: float | None, low: float = 0.0, high: float = 100.0) -> float | None:
    if value is None or pd.isna(value):
        return None
    return float(min(max(float(value), low), high))


def robust_z_score(
    value: float | int | None,
    history: Iterable[float | int | None],
    *,
    min_observations: int = 10,
    clip: float = 8.0,
) -> float | None:
    values = pd.Series(list(history), dtype="float64").dropna()
    if value is None or pd.isna(value) or len(values) < min_observations:
        return None
    median = float(values.median())
    mad = float((values - median).abs().median())
    if mad == 0:
        std = float(values.std(ddof=0))
        if std == 0 or math.isnan(std):
            return 0.0 if float(value) == median else (clip if float(value) > median else -clip)
        z = (float(value) - median) / std
    else:
        z = (float(value) - median) / (MAD_SCALE * mad)
    return float(np.clip(z, -clip, clip))


def add_rolling_robust_features(
    frame: pd.DataFrame,
    *,
    group_column: str,
    date_column: str,
    value_column: str,
    prefix: str,
    window: int = 30,
    min_observations: int = 10,
    clip: float = 8.0,
) -> pd.DataFrame:
    result = frame.sort_values([group_column, date_column]).copy()
    result[f"{prefix}_median"] = np.nan
    result[f"{prefix}_mad"] = np.nan
    result[f"{prefix}_robust_z"] = np.nan

    for _, index in result.groupby(group_column, sort=False).groups.items():
        series = pd.to_numeric(result.loc[index, value_column], errors="coerce")
        historical = series.shift(1)
        median = historical.rolling(window, min_periods=min_observations).median()
        mad = historical.rolling(window, min_periods=min_observations).apply(
            lambda values: float(np.median(np.abs(values - np.median(values)))), raw=True
        )
        fallback_std = historical.rolling(window, min_periods=min_observations).std(ddof=0)
        denominator = (mad * MAD_SCALE).where(mad > 0, fallback_std)
        z = (series - median) / denominator.replace(0, np.nan)
        flat_baseline = denominator.fillna(0).eq(0) & median.notna()
        equal_flat = flat_baseline & series.eq(median)
        positive_flat = flat_baseline & series.gt(median)
        negative_flat = flat_baseline & series.lt(median)
        z = z.mask(equal_flat, 0.0).mask(positive_flat, clip).mask(negative_flat, -clip).clip(-clip, clip)
        result.loc[index, f"{prefix}_median"] = median.values
        result.loc[index, f"{prefix}_mad"] = mad.values
        result.loc[index, f"{prefix}_robust_z"] = z.values
    return result


def percentile_rank(series: pd.Series, *, higher_is_stronger: bool = True) -> pd.Series:
    numeric = pd.to_numeric(series, errors="coerce")
    valid = numeric.dropna()
    output = pd.Series(np.nan, index=series.index, dtype="float64")
    if valid.empty:
        return output
    if len(valid) == 1:
        output.loc[valid.index] = 50.0
        return output
    ranks = valid.rank(method="average", pct=True) * 100.0
    if not higher_is_stronger:
        ranks = 100.0 - ranks + 100.0 / len(valid)
    output.loc[valid.index] = ranks.clip(0, 100)
    return output


def score_from_z(z_score: float | None) -> float | None:
    """Map a robust z-score to 0-100 without pretending it is a probability."""
    if z_score is None or pd.isna(z_score):
        return None
    # Smooth monotonic transformation: z=0 -> 50, z=2 -> ~88, z=-2 -> ~12.
    return float(100.0 / (1.0 + math.exp(-float(z_score))))
