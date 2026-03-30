from __future__ import annotations

import csv
import json
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from arena_companion.db.connection import apply_migrations
from arena_companion.services.export_service import ExportService


class ExportServiceTests(unittest.TestCase):
    def test_csv_and_json_exports(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            db_path = root / "arena_companion.db"
            export_dir = root / "exports"
            apply_migrations(db_path)

            conn = sqlite3.connect(db_path)
            try:
                conn.execute("INSERT INTO participants(screen_name, player_type, first_seen_at, last_seen_at) VALUES ('Alice','opponent',CURRENT_TIMESTAMP,CURRENT_TIMESTAMP)")
                opponent_id = conn.execute("SELECT id FROM participants WHERE screen_name='Alice'").fetchone()[0]
                conn.execute("INSERT INTO decks(display_name, format, created_at, last_seen_at) VALUES ('MonoBlue','standard',CURRENT_TIMESTAMP,CURRENT_TIMESTAMP)")
                deck_id = conn.execute("SELECT id FROM decks WHERE display_name='MonoBlue'").fetchone()[0]
                conn.execute("INSERT INTO deck_versions(deck_id, deck_fingerprint, captured_at, maindeck_count, sideboard_count) VALUES (?, 'fp-1', CURRENT_TIMESTAMP, 60, 15)", (deck_id,))
                deck_version_id = conn.execute("SELECT id FROM deck_versions WHERE deck_id=?", (deck_id,)).fetchone()[0]
                conn.execute("INSERT INTO matches(match_id, opponent_id, deck_version_id, result, started_at, ended_at) VALUES ('m1', ?, ?, 'Win', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)", (opponent_id, deck_version_id))
                match_pk = conn.execute("SELECT id FROM matches WHERE match_id='m1'").fetchone()[0]
                conn.execute("INSERT INTO games(match_id, game_number, result, play_draw, turn_count, started_at, ended_at) VALUES (?, 1, 'Win', 'play', 8, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)", (match_pk,))
                game_id = conn.execute("SELECT id FROM games WHERE match_id=?", (match_pk,)).fetchone()[0]
                conn.execute("INSERT INTO opponent_observed_cards(game_id, participant_id, arena_card_id, first_seen_turn, last_seen_turn, times_seen, observation_type) VALUES (?, ?, 123, 2, 4, 2, 'seen')", (game_id, opponent_id))
                conn.execute("INSERT INTO deck_cards(deck_version_id, arena_card_id, quantity, board_group) VALUES (?, 123, 4, 'maindeck')", (deck_version_id,))
                conn.execute("INSERT INTO turn_events(game_id, turn_number, event_type, arena_card_id, payload_json) VALUES (?, 2, 'spell_cast', 123, '{}')", (game_id,))
                conn.commit()
            finally:
                conn.close()

            exports = ExportService(db_path, export_dir)
            matches_path = exports.export_matches_csv()
            opponents_path = exports.export_opponents_csv()
            decks_path = exports.export_decks_csv()
            json_path = exports.export_json_bundle()

            self.assertTrue(matches_path.exists())
            self.assertTrue(opponents_path.exists())
            self.assertTrue(decks_path.exists())
            self.assertTrue(json_path.exists())

            with matches_path.open(encoding='utf-8', newline='') as handle:
                rows = list(csv.reader(handle))
            self.assertEqual(rows[0][0], 'match_id')

            payload = json.loads(json_path.read_text(encoding='utf-8'))
            self.assertIn('matches', payload)
            self.assertIn('turn_events', payload)
            self.assertIn('opponents', payload)


if __name__ == "__main__":
    unittest.main()
