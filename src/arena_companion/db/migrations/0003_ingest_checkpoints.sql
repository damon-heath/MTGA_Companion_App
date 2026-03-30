BEGIN;

CREATE TABLE IF NOT EXISTS ingest_checkpoints (
    source_file TEXT PRIMARY KEY,
    last_offset INTEGER NOT NULL,
    last_segment_id INTEGER,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(last_segment_id) REFERENCES raw_segments(id)
);

COMMIT;
