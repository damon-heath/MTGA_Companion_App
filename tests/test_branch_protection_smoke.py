from __future__ import annotations

import unittest


class BranchProtectionSmokeTest(unittest.TestCase):
    def test_intentional_failure(self) -> None:
        self.fail("Intentional failure for branch-protection smoke test.")


if __name__ == "__main__":
    unittest.main()
