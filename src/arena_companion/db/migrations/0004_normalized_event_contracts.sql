BEGIN;

CREATE TABLE IF NOT EXISTS normalized_event_contracts (
    raw_segment_id INTEGER PRIMARY KEY,
    family TEXT NOT NULL,
    contract_version TEXT NOT NULL,
    applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(raw_segment_id) REFERENCES raw_segments(id)
);

COMMIT;
