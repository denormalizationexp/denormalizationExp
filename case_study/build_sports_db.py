#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_sports_db.py
==================
Build and populate the *normalized* sports-stats database in PostgreSQL.

Schema (underline = part of PK, edge with a filled dot = identifying / key edge)
-------------------------------------------------------------------------------
    Player(name PK, dob, height, weight)
    Team(name PK, coach, location)

    Game(date, h_name, a_name, h_score, a_score)
        PK            = (date, h_name)
        h_name -> Team(name)                   # identifying FK (home team)
        a_name -> Team(name)                   # plain (non-key) FK (away team)

    Stats(p_name, date, h_name, points)
        PK            = (date, h_name, p_name)
        p_name           -> Player(name)
        (date, h_name)   -> Game(date, h_name)         # composite FK
        # NOTE: Stats has NO direct FK to Team; it reaches Team only via Game.

Scale factor = NUMBER OF SEASONS
--------------------------------
`--sf` is the number of seasons of data to generate (float allowed):

    #teams   = --teams            (FIXED across seasons, default 30)
    #games   = round(1230 * sf)   (1230 games per season)
    #stats   = #games * --per-game

    #players: a rolling roster. Each season has `--players-per-season`
    active players (default 450). Between seasons a fraction `--turnover`
    (default 0.25) of the roster retires and is replaced by brand-new
    players, so the distinct-player total grows slowly and realistically:
        distinct players ~= players_per_season
                            + (seasons - 1) * round(players_per_season * turnover)
    e.g. sf=10 -> ~30 teams, ~1462 players, 12300 games, 369000 stats.

Seasons are laid out on a single, globally increasing calendar starting
2000-10-01, so every (date, h_name) is unique across the whole dataset.

Example
-------
    pip install psycopg2-binary
    python build_sports_db.py --sf 10 --dbname sportsdb \
        --host localhost --port 5432 \
        --user YOUR_USERNAME --password YOUR_PASSWORD \
        --create-db
"""

import argparse
import csv
import io
import random
import sys
from datetime import date, timedelta

try:
    import psycopg2
    from psycopg2 import errors as pg_errors
except ImportError:
    sys.exit("psycopg2 is required:  pip install psycopg2-binary")


# --------------------------------------------------------------------------- #
# Per-season baselines                                                        #
# --------------------------------------------------------------------------- #
TEAMS = 30                  # teams in the league (fixed across seasons)
GAMES_PER_SEASON = 1230     # ~ one NBA regular season
PLAYERS_PER_SEASON = 450    # active roster size per season
TURNOVER = 0.25             # fraction of roster replaced each new season
STATS_PER_GAME = 30         # distinct players (stat lines) per game


# --------------------------------------------------------------------------- #
# DDL                                                                         #
# --------------------------------------------------------------------------- #
DDL = """
DROP TABLE IF EXISTS stats  CASCADE;
DROP TABLE IF EXISTS game   CASCADE;
DROP TABLE IF EXISTS player CASCADE;
DROP TABLE IF EXISTS team   CASCADE;

CREATE TABLE team (
    name     VARCHAR(64)  PRIMARY KEY,
    coach    VARCHAR(128),
    location VARCHAR(128)
);

CREATE TABLE player (
    name   VARCHAR(64) PRIMARY KEY,
    dob    DATE,
    height INTEGER,                 -- cm
    weight INTEGER                  -- kg
);

CREATE TABLE game (
    "date"  DATE        NOT NULL,
    h_name  VARCHAR(64) NOT NULL,
    a_name  VARCHAR(64) NOT NULL,
    h_score INTEGER,
    a_score INTEGER,
    PRIMARY KEY ("date", h_name),
    FOREIGN KEY (h_name) REFERENCES team(name),
    FOREIGN KEY (a_name) REFERENCES team(name)
);

CREATE TABLE stats (
    p_name VARCHAR(64) NOT NULL,
    "date" DATE        NOT NULL,
    h_name VARCHAR(64) NOT NULL,
    points INTEGER,
    PRIMARY KEY ("date", h_name, p_name),
    FOREIGN KEY (p_name) REFERENCES player(name),
    FOREIGN KEY ("date", h_name) REFERENCES game("date", h_name)
);
"""


# --------------------------------------------------------------------------- #
# Generators (deterministic given the seed)                                   #
# --------------------------------------------------------------------------- #
def gen_teams(n):
    return [(f"Team_{i:04d}", f"Coach_{i:04d}", f"City_{i % 100:02d}")
            for i in range(n)]


def season_game_counts(sf, per_season):
    """Split sf seasons into per-season game counts (last season may be partial)."""
    full = int(sf)
    frac = sf - full
    counts = [per_season] * full
    if frac > 0:
        counts.append(round(per_season * frac))
    counts = [c for c in counts if c > 0]
    return counts or [max(1, round(per_season * sf))]


class PlayerPool:
    """Master player table + a rolling per-season roster with turnover."""

    def __init__(self):
        self.rows = []          # (name, dob, height, weight)
        self._next = 0
        self._base_dob = date(1985, 1, 1)

    def _add(self, k):
        new = []
        for _ in range(k):
            name = f"Player_{self._next:06d}"
            dob = self._base_dob + timedelta(days=random.randint(0, 365 * 20))
            self.rows.append((name, dob.isoformat(),
                              random.randint(170, 220), random.randint(70, 130)))
            new.append(name)
            self._next += 1
        return new

    def rosters(self, num_seasons, per_season, turnover):
        active = self._add(per_season)
        out = [list(active)]
        n_new = min(round(per_season * turnover), per_season)
        for _ in range(1, num_seasons):
            if n_new > 0:                       # retire oldest, sign newcomers
                active = active[n_new:] + self._add(n_new)
            out.append(list(active))
        return out


def gen_games_and_stats(counts, rosters, team_names, per_game):
    """
    One global increasing calendar -> (date, h_name) unique everywhere.
    Returns (game_rows, stats_rows).
    game_rows : (date, h_name, a_name, h_score, a_score)
    stats_rows: (p_name, date, h_name, points)
    """
    games, stats = [], []
    nteams = len(team_names)
    cur = date(2000, 10, 1)
    lo, hi = max(1, nteams // 3), max(1, nteams // 2)
    for s, gcount in enumerate(counts):
        roster = rosters[s]
        k_stat = min(per_game, len(roster))
        remaining = gcount
        while remaining > 0:
            k = min(remaining, random.randint(lo, hi), nteams)
            homes = random.sample(team_names, k)               # distinct homes
            d_iso = cur.isoformat()
            for h in homes:
                a = random.choice(team_names)
                while a == h:
                    a = random.choice(team_names)
                games.append((d_iso, h, a,
                              random.randint(80, 130), random.randint(80, 130)))
                for p in random.sample(roster, k_stat):
                    stats.append((p, d_iso, h, random.randint(0, 60)))
            remaining -= len(homes)
            cur += timedelta(days=1)
    return games, stats


# --------------------------------------------------------------------------- #
# Fast bulk load via COPY                                                     #
# --------------------------------------------------------------------------- #
def copy_rows(cur, table, columns, rows):
    buf = io.StringIO()
    csv.writer(buf).writerows(rows)
    buf.seek(0)
    cur.copy_expert(
        f'COPY {table} ({", ".join(columns)}) FROM STDIN WITH (FORMAT csv)', buf)


# --------------------------------------------------------------------------- #
# Optional: create the target database                                        #
# --------------------------------------------------------------------------- #
def create_database(args):
    conn = psycopg2.connect(dbname="postgres", host=args.host, port=args.port,
                            user=args.user, password=args.password)
    conn.autocommit = True
    try:
        with conn.cursor() as cur:
            try:
                cur.execute(f'CREATE DATABASE "{args.dbname}"')
                print(f"[db] created database {args.dbname!r}")
            except pg_errors.DuplicateDatabase:
                print(f"[db] database {args.dbname!r} already exists, reusing")
    finally:
        conn.close()


# --------------------------------------------------------------------------- #
# Main                                                                        #
# --------------------------------------------------------------------------- #
def main():
    ap = argparse.ArgumentParser(
        description="Build & populate the normalized sports-stats DB. "
                    "Scale factor = number of seasons.")
    ap.add_argument("--sf", type=float, default=100,
                    help="number of seasons of data (float allowed)")
    ap.add_argument("--teams", type=int, default=TEAMS,
                    help="number of teams (FIXED across seasons)")
    ap.add_argument("--games-per-season", type=int, default=GAMES_PER_SEASON)
    ap.add_argument("--players-per-season", type=int, default=PLAYERS_PER_SEASON)
    ap.add_argument("--turnover", type=float, default=TURNOVER,
                    help="fraction of roster replaced each new season (0..1)")
    ap.add_argument("--per-game", type=int, default=STATS_PER_GAME,
                    help="distinct players (stat lines) per game")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--dbname", default="sportsdb")
    ap.add_argument("--host", default="localhost")
    ap.add_argument("--port", default=5432, type=int)
    ap.add_argument("--user", default="", help="PostgreSQL username.")   # Enter your psql user
    ap.add_argument("--password", default="", help="PostgreSQL password.")  # Enter your psql password
    ap.add_argument("--create-db", action="store_true",
                    help="CREATE DATABASE first (connects to 'postgres')")
    args = ap.parse_args()

    random.seed(args.seed)

    n_teams = max(2, args.teams)
    counts = season_game_counts(args.sf, args.games_per_season)
    n_seasons = len(counts)

    teams = gen_teams(n_teams)
    team_names = [t[0] for t in teams]

    pool = PlayerPool()
    rosters = pool.rosters(n_seasons, max(2, args.players_per_season),
                           max(0.0, min(1.0, args.turnover)))
    players = pool.rows

    games, stats = gen_games_and_stats(counts, rosters, team_names, args.per_game)

    print(f"[plan] seasons={args.sf}  teams={n_teams}  players={len(players)}  "
          f"games={len(games)}  stats={len(stats)}")

    if args.create_db:
        create_database(args)

    conn = psycopg2.connect(dbname=args.dbname, host=args.host, port=args.port,
                            user=args.user, password=args.password)
    try:
        with conn.cursor() as cur:
            print("[ddl] creating tables ...")
            cur.execute(DDL)
            print(f"[load] team   ({len(teams):>9} rows)")
            copy_rows(cur, "team", ["name", "coach", "location"], teams)
            print(f"[load] player ({len(players):>9} rows)")
            copy_rows(cur, "player", ["name", "dob", "height", "weight"], players)
            print(f"[load] game   ({len(games):>9} rows)")
            copy_rows(cur, "game",
                      ['"date"', "h_name", "a_name", "h_score", "a_score"], games)
            print(f"[load] stats  ({len(stats):>9} rows)")
            copy_rows(cur, "stats",
                      ["p_name", '"date"', "h_name", "points"], stats)
        conn.commit()

        with conn.cursor() as cur:
            for t in ("team", "player", "game", "stats"):
                cur.execute(f"SELECT count(*) FROM {t}")
                print(f"[done] {t:<7} = {cur.fetchone()[0]:>9} rows")
        print("[ok] database built successfully.")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
