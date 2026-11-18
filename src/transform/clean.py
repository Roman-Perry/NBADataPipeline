"""
- Clean + dedupe raw player game logs for staging
"""

import logging

import pandas as pd

logger = logging.getLogger(__name__)


def clean_player_game_logs(raw: pd.DataFrame) -> pd.DataFrame:
    df = raw.copy()

    before = len(df)
    df = df.dropna(subset=["player_id", "game_id", "game_date"])
    df = df[df["min"].fillna(0) > 0]
    df = df.drop_duplicates(subset=["player_id", "game_id"], keep="last")
    logger.info("Cleaning dropped %d of %d rows", before - len(df), before)

    numeric_cols = ["min", "pts", "reb", "ast"]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df.dropna(subset=numeric_cols)

    df["is_home"] = df["is_home"].astype(bool)
    df["game_date"] = pd.to_datetime(df["game_date"]).dt.date

    return df[
        [
            "player_id", "player_name", "team_id", "game_id", "game_date",
            "is_home", "opponent_team_abbreviation", "min", "pts", "reb",
            "ast", "season",
        ]
    ].sort_values(["player_id", "game_date"]).reset_index(drop=True)