"""
- Feature engineering for the player-game feature table
"""

import logging

import numpy as np
import pandas as pd

from src import config

logger = logging.getLogger(__name__)

FEATURE_VERSION = "v1"

def _rolling_past_only(series: pd.Series, window: int) -> pd.Series:
    return series.shift(1).rolling(window=window, min_periods=1).mean()

def build_player_features(staging: pd.DataFrame, team_context: pd.DataFrame | None = None) -> pd.DataFrame:
    df = staging.sort_values(["player_id", "game_date"]).copy()

    feature_frames = []
    for player_id, g in df.groupby("player_id", sort=False):
        g = g.sort_values("game_date").reset_index(drop=True)

        for w in config.ROLLING_WINDOWS:
            g[f"pts_roll{w}"] = _rolling_past_only(g["pts"], w)
            g[f"min_roll{w}"] = _rolling_past_only(g["min"], w)

        g["rest_days"] = g["game_date"].apply(pd.Timestamp).diff().dt.days
        g["rest_days"] = g["rest_days"].fillna(g["rest_days"].median()).clip(upper=10)

        g["pts_next"] = g["pts"].shift(-1)

        feature_frames.append(g)

    out = pd.concat(feature_frames, ignore_index=True)

    if team_context is not None and not team_context.empty:
        out = out.merge(
            team_context[["game_id", "opp_def_rating_roll10"]],
            on="game_id",
            how="left",
        )
    else:
        out["opp_def_rating_roll10"] = np.nan


    out["high_scorer_threshold"] = out.groupby("player_id")["pts"].transform(
        lambda s: s.shift(1).expanding(min_periods=5).quantile(config.HIGH_SCORER_QUANTILE)
    )
    out["is_high_scorer_next"] = out["pts_next"] > out["high_scorer_threshold"]

    out["feature_version"] = FEATURE_VERSION

    out = out.dropna(subset=["pts_next"])

    cols = [
        "player_id", "game_id", "game_date", "feature_version",
        "pts_roll5", "pts_roll10", "min_roll5", "min_roll10",
        "rest_days", "is_home", "opp_def_rating_roll10",
        "pts_next", "is_high_scorer_next",
    ]
    logger.info("Built %d feature rows (version=%s)", len(out), FEATURE_VERSION)
    return out[cols].reset_index(drop=True)



