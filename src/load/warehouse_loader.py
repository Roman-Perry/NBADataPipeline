"""
- Load layer wrapper functions
- Specifically one function per target/feature table
"""

import logging

import pandas as pd

from src.db.connection import upsert_dataframe

logger = logging.getLogger(__name__)

def load_raw_player_game_logs(df: pd.DataFrame) -> int:
    n = upsert_dataframe("raw_player_game_logs", df, primary_key_cols=["player_id", "game_id"])
    logger.info("Loaded %d rows into raw_player_game_logs", n)
    return n

def load_raw_player_prop_odds(df: pd.DataFrame) -> int:
    if df.empty:
        logger.info("No odds rows to load")
        return 0
    n = upsert_dataframe(
        "raw_player_prop_odds", df,
        primary_key_cols=["event_id", "bookmaker", "player_name", "market", "fetched_at"],
    )
    logger.info("Loaded %d rows into raw_player_prop_odds", n)
    return n

def load_staging_player_games(df: pd.DataFrame) -> int:
    n = upsert_dataframe("staging_player_games", df, primary_key_cols=["player_id", "game_id"])
    logger.info("Loaded %d rows into staging_player_games", n)
    return n

def load_features(df: pd.DataFrame) -> int:
    n = upsert_dataframe(
        "features_player_game", df, 
        primary_key_cols=["player_id", "game_id", "feature_version"],
    )
    logger.info("Loaded %d rows into featurs_player_game", n)
    return n


