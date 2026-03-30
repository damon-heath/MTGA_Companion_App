from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from arena_companion.ui.collection.view import (
    CollectionDiffRow,
    CollectionSnapshotRow,
    CollectionTrendRow,
    build_collection_view_model,
)


class CollectionUiTests(unittest.TestCase):
    def test_empty_state_includes_diagnostics_warning(self) -> None:
        view_model = build_collection_view_model(
            snapshots=(),
            diff_rows=(),
            diagnostics_warning="Detailed logging is disabled.",
        )
        self.assertIsNotNone(view_model.empty_state_message)
        self.assertIn("No collection snapshots", view_model.empty_state_message or "")
        self.assertIn("Detailed logging is disabled.", view_model.empty_state_message or "")

    def test_snapshot_and_diff_rows_are_preserved(self) -> None:
        snapshots = (
            CollectionSnapshotRow(
                snapshot_id=2,
                captured_at="2026-03-30T16:00:00Z",
                source_kind="owned_cards_v2",
                client_build="2026.3.30",
                unique_cards=2,
                total_cards=6,
            ),
        )
        diff_rows = (
            CollectionDiffRow(
                arena_card_id=67330,
                card_name="Plains",
                set_code="FDN",
                rarity="common",
                quantity_from=3,
                quantity_to=4,
                delta=1,
            ),
        )
        trends = (
            CollectionTrendRow(
                from_snapshot_id=1,
                to_snapshot_id=2,
                from_captured_at="2026-03-27T16:00:00Z",
                to_captured_at="2026-03-30T16:00:00Z",
                gained_cards=1,
                lost_cards=0,
                gained_quantity=1,
                lost_quantity=0,
                net_delta=1,
            ),
        )
        view_model = build_collection_view_model(
            snapshots=snapshots,
            diff_rows=diff_rows,
            trend_rows=trends,
            diagnostics_warning=None,
        )
        self.assertIsNone(view_model.empty_state_message)
        self.assertEqual(view_model.snapshots[0].snapshot_id, 2)
        self.assertEqual(view_model.diff_rows[0].delta, 1)
        self.assertEqual(view_model.trend_rows[0].net_delta, 1)

    def test_filtered_state_shows_filter_empty_message(self) -> None:
        snapshots = (
            CollectionSnapshotRow(
                snapshot_id=2,
                captured_at="2026-03-30T16:00:00Z",
                source_kind="owned_cards_v2",
                client_build="2026.3.30",
                unique_cards=2,
                total_cards=6,
            ),
        )
        view_model = build_collection_view_model(
            snapshots=snapshots,
            diff_rows=(),
            trend_rows=(),
            diagnostics_warning=None,
            filters_applied=True,
        )
        self.assertEqual(view_model.empty_state_message, "No collection changes match the active filters.")


if __name__ == "__main__":
    unittest.main()
