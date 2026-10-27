-- NBA_DATA_PIPELINE Schema (DuckDB)
-- Utilizes a light star-schema

CREATE TABLE IF NOT EXISTS players (
    player_id       BIGINT PRIMARY KEY,
    player_name     VARCHAR,
    team_id         BIGINT,
    position        VARCHAR,
    updated_at      TIMESTAMP DEFAULT current_timestamp
);

CREATE TABLE IF NOT EXISTS teams (
    team_id         BIGINT PRIMARY KEY,
    team_abbreviation VARCHAR,
    team_name       VARCHAR          
);

-- Main fact table; one row per player per game
CREATE TABLE IF NOT EXISTS raw_player_game_logs (
    player_id       BIGINT,
    player_name     VARCHAR,
    team_id         BIGINT,
    team_abbreviation VARCHAR,
    game_id         VARCHAR,
    game_date       DATE,
    matchup         VARCHAR,
    is_home         BOOLEAN,
    opponent_team_abbreviation VARCHAR,
    min             DOUBLE,
    pts             DOUBLE,
    reb             DOUBLE,
    ast             DOUBLE,
    fga             DOUBLE,
    fgm             DOUBLE,
    season          VARCHAR,
    ingested_at     TIMESTAMP DEFAULT current_timestamp,
    PRIMARY KEY (player_id, game_id)
);

-- Opponent strength feature based on defensive context
CREATE TABLE IF NOT EXISTS raw_team_game_logs (
    team_id         BIGINT,
    game_id         VARCHAR,
    game_date       DATE,
    opponent_team_id BIGINT,
    def_rating      DOUBLE,
    pace            DOUBLE,
    season          VARCHAR,
    ingested_at TIMESTAMP DEFAULT current_timestamp,
    PRIMARY KEY (team_id, game_id)
);

-- Market lines from odds API; one row per bookmaker/player/date
CREATE TABLE IF NOT EXISTS raw_player_prop_odds (
    event_id        VARCHAR,
    commence_time   TIMESTAMP,
    home_team       VARCHAR,
    away_team       VARCHAR,
    bookmaker       VARCHAR,
    player_name     VARCHAR,
    market          VARCHAR,
    line            DOUBLE,
    over_price      DOUBLE,
    under_price     DOUBLE,
    fetched_at      TIMESTAMP DEFAULT current_timestamp,
    PRIMARY KEY (event_id, bookmaker, player_name, market, fetched_at)
);

-- Cleaned player game rows
CREATE TABLE IF NOT EXISTS staging_player_games (
    player_id       BIGINT,
    player_name     VARCHAR,
    team_id         BIGINT,
    game_id         VARCHAR,
    game_date       DATE,
    is_home         BOOLEAN,
    opponent_team_abbreviation VARCHAR,
    min             DOUBLE,
    pts             DOUBLE,
    reb             DOUBLE,
    ast             DOUBLE,
    season          VARCHAR,
    PRIMARY KEY (player_id, game_id)
);

-- Versioned feature table; **VERSIONING IS VITAL FOR ML training
CREATE TABLE IF NOT EXISTS features_player_game (
    player_id       BIGINT,
    game_id         VARCHAR,
    game_date       DATE,
    feature_version VARCHAR,
    pts_roll5       DOUBLE,
    pts_roll10      DOUBLE,
    min_roll5       DOUBLE,
    min_roll10      DOUBLE,
    rest_days       INTEGER,
    is_home         BOOLEAN,
    opp_def_rating_roll10 DOUBLE,
    pts_next        DOUBLE,
    is_high_scorer_next BOOLEAN,
    computed_at     TIMESTAMP DEFAULT current_timestamp,
    PRIMARY KEY (player_id, game_id, feature_version)
);








