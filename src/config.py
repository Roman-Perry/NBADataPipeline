"""
- Central configuration for the ETL/ELT pipeline
- All values should be read from environment variables
- Set variables in a '.env' file loaded via python-dotenv
"""

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# Paths
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = Path(os.getenv("NBA_DATA_DIR", PROJECT_ROOT / "data"))
RAW_DIR = DATA_DIR / "raw"
STAGING_DIR = DATA_DIR / "staging"

for d in (RAW_DIR, STAGING_DIR):
    d.mkdir(parents=True, exist_ok=True)

# Warehouse: DuckDB
WAREHOUSE_PATH = str(DATA_DIR / "warehouse.duckdb")

# Season and schedule
SEASON = os.getenv("NBA_SEASON", "2024-25")
SEASON_TYPE = os.getenv("NBA_SEASON_TYPE", "Regular Season")

# External APIs
ODDS_API_KEY = os.getenv("ODDS_API_KEY", "")
ODDS_API_BASE_URL = "https://api.the-odds-api.com/v4"
ODDS_SPORT_KEY = "basketball_nba"
ODDS_MARKET = "player_points"
ODDS_REGION = os.getenv("ODDS_API_REGION", "us")

# Rate limiting and retries
NBA_API_MIN_REQUEST_INTERVAL_SEC = float(os.getenv("NBA_API_MIN_INTERVAL", "0.8"))
NBA_API_MAX_RETRIES = int(os.getenv("NBA_API_MAX_RETRIES", "5"))

# Feature engineering
ROLLING_WINDOWS = (5, 10)
HIGH_SCORER_QUANTILE = 0.75







