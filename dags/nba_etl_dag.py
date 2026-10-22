"""
- Airflow orchestrated ETL/ELT
- TaskFlow API in modern 3.x style
"""

from __future__ import annotations
import datetime as dt

from airflow.sdk import dag, task
from airflow.sdk.exceptions import AirflowSkipException

default_args = {
    "owner": "NBADataPipeline",
    "retries": 3,
    "retry_delay": dt.timedelta(minutes=5),
    "retry_exponential_backoff": True,
    "max_retry_delay": dt.timedelta(minutes=30),
}

@dag(
    dag_id="nba_etl_elt_pipeline",
    description="Extract NBA game logs + prop odds, transform, load into warehouse and feature store",
    schedule="0 9 * * *",
    start_date=dt.datetime(2024, 10, 1),
    catchup=False,
    default_args=default_args,
    tags=["nba", "etl", "elt"],
)
def nba_etl_elt_pipeline():

    @task
    def extract_game_logs() -> str:
        # Player game logs from nba_api
        from src.extract.nba_api_extractor import extract_player_game_logs
        from src.load.warehouse_loader import load_raw_player_game_logs

        df = extract_player_game_logs()
        if df.empty:
            raise AirflowSkipException("No new player game log rows returned by nba_api")
        load_raw_player_game_logs(df)
        return f"raw_player_game_logs:{len(df)}"

    @task
    def extract_team_context() -> str:
        # Team game logs used for opponent-strength features
        from src.extract.nba_api_extractor import extract_team_game_logs
        from src.load.warehouse_loader import upsert_dataframe # keeping this here for potential future use

        df = extract_team_game_logs()
        return f"raw_team_game_logs:{len(df)}"

    @task
    def extract_odds() -> str:
        # Player point prop lines from odds API
        from src.extract.odds_api_extractor import extract_player_points_props
        from src.load.warehouse_loader import load_raw_player_prop_odds

        df = extract_player_points_props()
        n = load_raw_player_prop_odds(df)
        return f"raw_player_prop_odds:{n}"

    @task
    def clean_transform() -> str:
        # Clean raw game logs
        from src.db.connection import get_connection
        from src.transform.clean import clean_player_game_logs
        from src.load.warehouse_loader import load_staging_player_games

        with get_connection() as con:
            raw = con.execute("SELECT * FROM raw_player_game_logs").fetchdf()

        cleaned = clean_player_game_logs(raw)
        n = load_staging_player_games(cleaned)
        return f"staging_player_games:{n}"

    @task
    def build_and_load_features() -> str:
        # Computing rolling features and loading them
        from src.db.connection import get_connection
        from src.transfrom.build_features import build_player_features
        from src.load.warehouse_loader import load_features

        with get_connection() as con:
            staging = con.execute("SELECT * FROM staging_player_games").fetchdf()

        features = build_player_features(staging)
        n = load_features(features)
        return f"features_player_game:{n}"

    game_logs = extract_game_logs()
    team_context = extract_team_context()
    odds = extract_odds()

    cleaned = clean_transform()
    features = build_and_load_features()

    [game_logs, team_context] >> cleaned >> features
    odds # Purposefully independent 

nba_etl_elt_pipeline()


    

    










