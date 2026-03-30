BEGIN;

CREATE TABLE IF NOT EXISTS raw_segments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_file TEXT NOT NULL,
    source_offset INTEGER,
    captured_at TEXT NOT NULL,
    segment_type TEXT,
    parser_version TEXT,
    raw_text TEXT,
    raw_json TEXT,
    parse_status TEXT NOT NULL,
    error_message TEXT
);

CREATE TABLE IF NOT EXISTS inventory_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    captured_at TEXT NOT NULL,
    gold INTEGER,
    gems INTEGER,
    wc_common INTEGER,
    wc_uncommon INTEGER,
    wc_rare INTEGER,
    wc_mythic INTEGER,
    raw_segment_id INTEGER,
    FOREIGN KEY(raw_segment_id) REFERENCES raw_segments(id)
);

CREATE TABLE IF NOT EXISTS decks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    display_name TEXT NOT NULL,
    format TEXT,
    created_at TEXT,
    last_seen_at TEXT
);

CREATE TABLE IF NOT EXISTS deck_versions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    deck_id INTEGER NOT NULL,
    deck_fingerprint TEXT NOT NULL,
    captured_at TEXT,
    maindeck_count INTEGER,
    sideboard_count INTEGER,
    FOREIGN KEY(deck_id) REFERENCES decks(id)
);

CREATE TABLE IF NOT EXISTS deck_cards (
    deck_version_id INTEGER NOT NULL,
    arena_card_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL,
    board_group TEXT NOT NULL CHECK(board_group IN ('maindeck','sideboard')),
    PRIMARY KEY(deck_version_id, arena_card_id, board_group),
    FOREIGN KEY(deck_version_id) REFERENCES deck_versions(id)
);

CREATE TABLE IF NOT EXISTS participants (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    screen_name TEXT NOT NULL,
    player_type TEXT,
    first_seen_at TEXT,
    last_seen_at TEXT
);

CREATE TABLE IF NOT EXISTS participant_rank_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    participant_id INTEGER NOT NULL,
    captured_at TEXT NOT NULL,
    rank_class TEXT,
    rank_tier TEXT,
    rank_step TEXT,
    limited_or_constructed TEXT,
    FOREIGN KEY(participant_id) REFERENCES participants(id)
);

CREATE TABLE IF NOT EXISTS matches (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    match_id TEXT NOT NULL,
    event_name TEXT,
    format TEXT,
    queue_type TEXT,
    started_at TEXT,
    ended_at TEXT,
    result TEXT,
    deck_version_id INTEGER,
    opponent_id INTEGER,
    raw_start_segment_id INTEGER,
    raw_end_segment_id INTEGER,
    FOREIGN KEY(deck_version_id) REFERENCES deck_versions(id),
    FOREIGN KEY(opponent_id) REFERENCES participants(id),
    FOREIGN KEY(raw_start_segment_id) REFERENCES raw_segments(id),
    FOREIGN KEY(raw_end_segment_id) REFERENCES raw_segments(id)
);

CREATE TABLE IF NOT EXISTS games (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    match_id INTEGER NOT NULL,
    game_number INTEGER NOT NULL,
    started_at TEXT,
    ended_at TEXT,
    result TEXT,
    play_draw TEXT,
    turn_count INTEGER,
    win_type TEXT,
    end_reason TEXT,
    UNIQUE(match_id, game_number),
    FOREIGN KEY(match_id) REFERENCES matches(id)
);

CREATE TABLE IF NOT EXISTS opponent_observed_cards (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    game_id INTEGER NOT NULL,
    participant_id INTEGER NOT NULL,
    arena_card_id INTEGER NOT NULL,
    first_seen_turn INTEGER,
    last_seen_turn INTEGER,
    times_seen INTEGER NOT NULL DEFAULT 1,
    observation_type TEXT,
    FOREIGN KEY(game_id) REFERENCES games(id),
    FOREIGN KEY(participant_id) REFERENCES participants(id)
);

CREATE TABLE IF NOT EXISTS turn_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    game_id INTEGER NOT NULL,
    turn_number INTEGER,
    phase TEXT,
    step TEXT,
    actor_seat TEXT,
    event_type TEXT NOT NULL,
    arena_card_id INTEGER,
    instance_id TEXT,
    zone_from TEXT,
    zone_to TEXT,
    payload_json TEXT,
    raw_segment_id INTEGER,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(game_id) REFERENCES games(id),
    FOREIGN KEY(raw_segment_id) REFERENCES raw_segments(id)
);

CREATE TABLE IF NOT EXISTS parser_errors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    captured_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    parser_name TEXT NOT NULL,
    raw_segment_id INTEGER,
    error_message TEXT NOT NULL,
    stack_trace TEXT,
    FOREIGN KEY(raw_segment_id) REFERENCES raw_segments(id)
);

CREATE TABLE IF NOT EXISTS app_settings (
    key TEXT PRIMARY KEY,
    value_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS ingest_checkpoints (
    source_file TEXT PRIMARY KEY,
    last_offset INTEGER NOT NULL,
    last_segment_id INTEGER,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(last_segment_id) REFERENCES raw_segments(id)
);

CREATE TABLE IF NOT EXISTS collection_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    captured_at TEXT NOT NULL,
    source_kind TEXT,
    snapshot_fingerprint TEXT,
    parser_schema_version TEXT,
    client_build TEXT,
    unique_cards INTEGER,
    total_cards INTEGER,
    raw_segment_id INTEGER,
    FOREIGN KEY(raw_segment_id) REFERENCES raw_segments(id)
);

CREATE TABLE IF NOT EXISTS collection_cards (
    collection_snapshot_id INTEGER NOT NULL,
    arena_card_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL,
    PRIMARY KEY(collection_snapshot_id, arena_card_id),
    FOREIGN KEY(collection_snapshot_id) REFERENCES collection_snapshots(id)
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_matches_match_id ON matches(match_id);
CREATE INDEX IF NOT EXISTS idx_matches_started_at ON matches(started_at);
CREATE INDEX IF NOT EXISTS idx_matches_deck_version_id ON matches(deck_version_id);
CREATE UNIQUE INDEX IF NOT EXISTS idx_raw_segments_source ON raw_segments(source_file, source_offset);
CREATE INDEX IF NOT EXISTS idx_participants_screen_name ON participants(screen_name);
CREATE INDEX IF NOT EXISTS idx_observed_cards_participant_card ON opponent_observed_cards(participant_id, arena_card_id);
CREATE INDEX IF NOT EXISTS idx_turn_events_game_turn ON turn_events(game_id, turn_number);
CREATE UNIQUE INDEX IF NOT EXISTS idx_collection_snapshots_fingerprint ON collection_snapshots(snapshot_fingerprint);
CREATE INDEX IF NOT EXISTS idx_collection_snapshots_captured_at ON collection_snapshots(captured_at);

COMMIT;

