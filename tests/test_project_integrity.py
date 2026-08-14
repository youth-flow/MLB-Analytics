from __future__ import annotations

import hashlib
import tempfile
import unittest
from pathlib import Path

from scripts.verify_project import (
    EXPECTED_CORE_METRICS,
    EXPECTED_RECONCILIATION,
    ROOT,
    build_artifact_manifest_bytes,
    check_core_metrics,
    check_data_reconciliation,
    check_source_manifest,
    scan_public_pii,
    write_artifact_manifest,
)


class FrozenProjectTests(unittest.TestCase):
    def test_raw_source_hashes(self) -> None:
        result = check_source_manifest(ROOT)
        self.assertEqual(result["entries"], 17)
        self.assertEqual(result["errors"], [])
        self.assertEqual(result["status"], "passed")

    def test_reconciled_core_counts(self) -> None:
        result = check_data_reconciliation(ROOT)
        self.assertEqual(result["status"], "passed", result["errors"])
        observed = {row["check"]: row["computed"] for row in result["rows"]}
        self.assertEqual(observed, EXPECTED_RECONCILIATION)

    def test_frozen_headline_conclusions(self) -> None:
        result = check_core_metrics(ROOT)
        self.assertEqual(result["status"], "passed", result["errors"])
        for key, expected in EXPECTED_CORE_METRICS.items():
            self.assertAlmostEqual(float(result["observed"][key]), float(expected), places=8)


class VerificationMechanismTests(unittest.TestCase):
    def test_manifest_is_deterministic_and_excludes_transients(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "scripts" / "__pycache__").mkdir(parents=True)
            (root / "qa" / "rendered").mkdir(parents=True)
            (root / "scripts" / "kept.py").write_text("print('ok')\n", encoding="utf-8")
            (root / "scripts" / "__pycache__" / "ignored.pyc").write_bytes(b"cache")
            (root / "qa" / "rendered" / "ignored.pdf").write_bytes(b"render")
            first, rows = build_artifact_manifest_bytes(root)
            (root / "scripts" / "kept.py").write_bytes(b"print('ok')\r\n")
            second, _ = build_artifact_manifest_bytes(root)
            self.assertEqual(first, second)
            paths = [row["file"] for row in rows]
            self.assertEqual(paths, ["scripts/kept.py"])
            self.assertEqual(rows[0]["digest_kind"], "text-lf-sha256-v1")
            out = root / "qa" / "artifact_manifest.csv"
            receipt = write_artifact_manifest(root, out)
            first_hash = hashlib.sha256(out.read_bytes()).hexdigest()
            write_artifact_manifest(root, out)
            self.assertEqual(first_hash, hashlib.sha256(out.read_bytes()).hexdigest())
            self.assertEqual(receipt["status"], "passed")

    def test_pii_scan_reports_kind_without_repeating_value(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "reports" / "sources" / "draft.md"
            source.parent.mkdir(parents=True)
            synthetic_email = "person" + "@" + "example.com"
            source.write_text(f"contact: {synthetic_email}\n", encoding="utf-8")
            result = scan_public_pii(root)
            self.assertEqual(result["status"], "failed")
            self.assertEqual(result["findings"][0]["kind"], "email")
            self.assertNotIn(synthetic_email, str(result["findings"]))


if __name__ == "__main__":
    unittest.main()
