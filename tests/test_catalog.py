"""Check that catalog ordering is independent of the checkout platform."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tool import catalog


class CatalogOrderingTests(unittest.TestCase):
    def test_inventory_uses_case_sensitive_posix_order(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            assets = root / "assets"
            assets.mkdir()
            for name in ("asset-index.json", "THIRD_PARTY_NOTICES.md", "NOTICE.md"):
                (assets / name).write_bytes(b"example")

            self.assertEqual(
                [entry["path"] for entry in catalog.inventory(root)],
                ["assets/NOTICE.md", "assets/THIRD_PARTY_NOTICES.md", "assets/asset-index.json"],
            )

    def test_generation_inputs_use_case_sensitive_posix_order(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            tool = root / "tool"
            tool.mkdir()
            for name in ("alpha.py", "Zebra.py", "Beta.dart"):
                (tool / name).write_bytes(b"example\n")

            with patch.object(catalog, "validate", return_value=[]):
                result = catalog.build(root)

            self.assertEqual(
                list(result["generationInputs"]),
                ["tool/Beta.dart", "tool/Zebra.py", "tool/alpha.py"],
            )


if __name__ == "__main__":
    unittest.main()
