BEGIN;

ALTER TABLE collection_snapshots ADD COLUMN snapshot_fingerprint TEXT;
ALTER TABLE collection_snapshots ADD COLUMN parser_schema_version TEXT;
ALTER TABLE collection_snapshots ADD COLUMN client_build TEXT;
ALTER TABLE collection_snapshots ADD COLUMN unique_cards INTEGER;
ALTER TABLE collection_snapshots ADD COLUMN total_cards INTEGER;

CREATE UNIQUE INDEX IF NOT EXISTS idx_collection_snapshots_fingerprint
    ON collection_snapshots(snapshot_fingerprint);
CREATE INDEX IF NOT EXISTS idx_collection_snapshots_captured_at
    ON collection_snapshots(captured_at);

COMMIT;
