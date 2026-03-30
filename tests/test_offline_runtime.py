from __future__ import annotations

import socket
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from arena_companion.app.lifecycle import bootstrap_application


class OfflineRuntimeTests(unittest.TestCase):
    def test_bootstrap_does_not_attempt_outbound_network(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            with mock.patch.dict("os.environ", {"APPDATA": tmp}, clear=False):
                with mock.patch.object(socket.socket, "connect", side_effect=AssertionError("network call attempted")):
                    state = bootstrap_application()
                    self.assertTrue(state.paths.appdata_root.exists())


if __name__ == "__main__":
    unittest.main()
