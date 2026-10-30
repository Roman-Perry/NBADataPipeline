"""
- Extraction of player prop market lines from Odds API
"""

import logging

import pandas as pd
import requests
from tenacity import retry, stop_after_attempt, wait_exponential

from src import config

logger = logging.getLogger(__name__)

class OddsAPIError(RuntimeError):
    pass


@retry(stop=stop_after_attempt(4), wait=wait_exponential(multiplier=1, min=2, max=20))
def _get(path: str, params: dict) -> list:
    if not config.ODDS_API_KEY:
        raise OddsAPIError(
            "ODDS_API_KEY is not set. Add it to your .env or Airflow "
            "connection/variable store before running this task."
        )
    params = {**params, "apiKey": config.ODDS_API_KEY}
    resp = requests.get(f"{config.ODDS_API_BASE_URL}{path}", params=params, timeout=30)
    if resp.status_code == 401:
        raise OddsAPIError("Odds API rejected the key (401) - check ODDS_API_KEY.")
    resp.raise_for_status()
    return resp.json()

def extract_player_points_props() -> pd.DataFrame:

    events = _get(f"/sports/{config.ODDS_SPORT_KEY}/events", params={})
    rows = []
    for event in events:
        event_id = event["id"]
        try:
            odds = _get(
                f"/sports/{config.ODDS_SPORT_KEY}/events/{event_id}/odds",
                params={
                    "regions": config.ODDS_REGION,
                    "markets": config.ODDS_MARKET,
                    "oddsFormat": "american",
                }
            )
        except OddsAPIError:
            logger.warning("Skipping event %s: odds fetch failed", event_id)
            continue

        for bookmaker in odds.get("bookmakers", []):
            for market in bookmaker.get("markets", []):
                if market["key"] != config.ODDS_MARKET:
                    continue

                by_player: dict[str, dict] = {}
                for outcome in market.get("outcomes", []):
                    player = outcome["description"]
                    slot = by_player.setdefault(player, {"line": outcome["point"]})
                    if outcome["name"] == "Over":
                        slot["over_price"] = outcome["price"]
                    else:
                        slot["under_price"] = outcome["price"]

                for player, prices in by_player.items():
                    rows.append(
                        {
                            "event_id": event_id,
                            "commence_time": event["commence_time"],
                            "home_team": event["home_team"],
                            "away_team": event["away_team"],
                            "bookmaker": bookmaker["key"],
                            "player_name": player,
                            "market": config.ODDS_MARKET,
                            "line": prices.get("line"),
                            "over_price": prices.get("over_price"),
                            "under_price": prices.get("under_price"),
                        }
                    )

    df = pd.DataFrame(rows)
    if not df.empty:
        df["commence_time"] = pd.to_datetime(df["commence_time"])
    logger.info("Extracted %d player prop odds rows across %d events", len(df), len(events))
    return df


