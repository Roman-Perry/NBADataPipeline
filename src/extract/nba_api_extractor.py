"""
- nba_api data extraction
- Self throttling between calls 
- Tenacity for retries with exponential backoff
"""

import logging
import time

import pandas as pd
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from src import config

logger = logging.getLogger(__name__)

_last_call_ts = 0.0


def _throttle() -> None:
    global _last_call_ts
    elapsed = time.monotonic() - _last_call_ts
    wait = config.NBA_API_MIN_REQUEST_INTERVAL_SEC - elapsed
    if wait > 0:
        time.sleep(wait)
    _last_call_ts = time.monotonic()

def _retryable():
    return retry(
        stop=stop_after_attempt(config.NBA_API_MAX_RETRIES),
        wait=wait_exponential(multiplier=1, min=2, max=30),
        retry=retry_if_exception_type(Exception),
        reraise=True,
    )

@_retryable
def _fetch_league_game_log(season: str, season_type: str, player_or_team: str) -> pd.DataFrame:

    from nba_api.stats.endpoints import leaguegamelog

    _throttle()
    logger.info(
        "Fetching LeagueGameLog season=%s type=%s player_or_team=%s",
        season, season_type, player_or_team,
    )
    resp = leaguegamelog.LeagueGameLog(
        season=season,
        season_type_all_star=season_type,
        player_or_team_abbreviation=player_or_team,
        timeout=60,
    )
    return resp.get_data_frames()[0] # Isolates the primary data table provided from nba_api resp

def extract_player_game_logs(season: str | None = None, season_type: str | None = None) -> pd.DataFrame:

    season = season or config.SEASON
    season_type = season_type or config.SEASON_TYPE

    raw = _fetch_league_game_log(season, season_type, player_or_team="P")

    raw["IS_HOME"] = ~raw["MATCHUP"].str.contains("@")
    raw["OPPONENT_TEAM_ABBREVIATION"] = (
        raw["MATCHUP"].str.split().str[-1]
    )
    raw["SEASON"] = season

    keep = raw.rename(
        columns={
            "PLAYER_ID": "player_id",
            "PLAYER_NAME": "player_name",
            "TEAM_ID": "team_id",
            "TEAM_ABBREVIATION": "team_abbreviation",
            "GAME_ID": "game_id",
            "GAME_DATE": "game_date",
            "MATCHUP": "matchup",
            "IS_HOME": "is_home",
            "OPPONENT_TEAM_ABBREVIATION": "opponent_team_abbreviation",
            "MIN": "min",
            "PTS": "pts",
            "REB": "reb",
            "AST": "ast",
            "FGA": "fga",
            "FGM": "fgm",
            "SEASON": "season",
        }
    )
    cols = [ 
        "player_id", "player_name", "team_id", "team_abbreviation", "game_id",
        "game_date", "matchup", "is_home", "opponent_team_abbreviation", 
        "min", "pts", "reb", "ast", "fga", "fgm", "season",
    ]
    keep = keep[cols]
    keep["game_date"] = pd.to_datetime(keep["game_date"]).dt.date
    logger.info("Extracted %d player-game rows", len(keep))
    return keep

def extract_team_game_logs(season: str | None = None, season_type: str | None = None) -> pd.DataFrame:

    season = season or config.SEASON
    season_type = season_type or config.SEASON_TYPE

    raw = _fetch_league_game_log(season, season_type, player_or_team="T")

    raw["OPPONENT_TEAM_ABBREVIATION"] = raw["MATCHUP"].str.split().str[-1]
    raw["SEASON"] = season

    keep = raw.rename(
        columns={
            "TEAM_ID": "team_id",
            "GAME_ID": "game_id",
            "GAME_DATE": "game_date",
            "OPPONENT_TEAM_ABBREVIATION": "opponent_team_abbreviation",
            "SEASON": "season",
        }
    )[["team_id", "game_id", "game_date", "opponent_team_abbreviation", "season"]]

    keep["game_date"] = pd.to_datetime(keep["game_date"]).dt.date
    logger.info("Extracted %d team-game rows", len(keep))
    return keep
