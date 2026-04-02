"""
Build Database Schema
=================================
Creates the SQLite database and all core tables.

The database file will be created at: data/pga_predictor.db
"""

import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "pga_predictor.db")


def get_connection():
    """Returns a connection to the SQLite database."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    # Enable foreign key enforcement
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def create_schema():
    conn = get_connection()
    cursor = conn.cursor()

    # ── players ────────────────────────────────────────────────────
    # One row per player. Stable player_id used across all other tables.
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS players (
            player_id   INTEGER PRIMARY KEY AUTOINCREMENT,
            player_name TEXT    NOT NULL,           -- canonical spelling e.g. 'Rory McIlroy'
            espn_id     TEXT    UNIQUE,             -- ESPN athlete ID for API calls
            owgr_name   TEXT,                       -- name as it appears in OWGR docs (may differ)
            country     TEXT,
            dob         DATE,
            created_at  DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # ── tournaments ────────────────────────────────────────────────
    # One row per tournament per year (e.g. The Masters 2023, The Masters 2024).
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tournaments (
            tournament_id       INTEGER PRIMARY KEY AUTOINCREMENT,
            name                TEXT    NOT NULL,   -- e.g. 'The Masters'
            course_name         TEXT,               -- e.g. 'Augusta National'
            year                INTEGER NOT NULL,
            start_date          DATE,               -- Round 1 date
            end_date            DATE,
            course_length_yards INTEGER,
            course_par          INTEGER,
            grass_type          TEXT,               -- e.g. 'Bermuda', 'Bentgrass', 'Poa Annua'
            created_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
            UNIQUE (name, year)                     -- prevents duplicate entries
        )
    """)

    # ── results ────────────────────────────────────────────────────
    # One row per player per tournament.
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS results (
            result_id       INTEGER PRIMARY KEY AUTOINCREMENT,
            tournament_id   INTEGER NOT NULL REFERENCES tournaments(tournament_id),
            player_id       INTEGER NOT NULL REFERENCES players(player_id),
            finish_position INTEGER,                -- numeric: CUT=99, WD=98, DQ=97; leave NULL if player did not participate
            total_score     INTEGER,                -- score relative to par
            r1_score        INTEGER,
            r2_score        INTEGER,
            r3_score        INTEGER,
            r4_score        INTEGER,
            created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
            UNIQUE (tournament_id, player_id)       -- one result per player per tournament
        )
    """)

    # ── player_stats ───────────────────────────────────────────────
    # One row per player per stats window (e.g. '2023_pre_tournament').
    # A 'window' is a defined date range of tournaments used to compute
    # rolling averages — not a single tournament's stats.
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS player_stats (
            stat_id             INTEGER PRIMARY KEY AUTOINCREMENT,
            player_id           INTEGER NOT NULL REFERENCES players(player_id),
            window_label        TEXT,               -- optional label for the rolling window (e.g., '2023_pre_masters')
            window_start        DATE,               -- start date of the stats window;
            window_end          DATE,               -- end date of the stats window; inclusive
            
            -- Strokes Gained
            sg_total            REAL,
            sg_ott              REAL,               
            sg_app              REAL,               
            sg_arg              REAL,               
            sg_putt             REAL,               

            -- Ball striking
            driving_distance    REAL,
            driving_accuracy_pct REAL,
            gir_pct             REAL,               
            proximity_100_125   REAL,               
            proximity_125_150   REAL,
            proximity_150_175   REAL,

            -- Scoring
            scoring_avg         REAL,
            birdie_avg          REAL,
            par5_scoring_avg    REAL,

            -- Context
            events_played       INTEGER,            

            created_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
            UNIQUE (player_id, window_start, window_end)
        )
    """)

    # ── world_rankings ─────────────────────────────────────────────
    # Snapshot of OWGR rankings. One row per player per week snapshot.
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS world_rankings (
            ranking_id      INTEGER PRIMARY KEY AUTOINCREMENT,
            player_id       INTEGER NOT NULL REFERENCES players(player_id),
            ranking_date    DATE    NOT NULL,       -- date of the snapshot; used to align rankings with tournament start dates
            owgr_rank       INTEGER NOT NULL,
            created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
            UNIQUE (player_id, ranking_date)
        )
    """)

    conn.commit()
    conn.close()
    print(f"Database created at: {os.path.abspath(DB_PATH)}")
    print("Tables created: players, tournaments, results, player_stats, world_rankings")


if __name__ == "__main__":
    create_schema()