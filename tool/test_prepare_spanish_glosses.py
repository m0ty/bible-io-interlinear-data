#!/usr/bin/env python3
"""Offline full-corpus importer regression; requires the pinned source archive."""

import argparse
import copy
import gzip
import json
from pathlib import Path
import shutil
import sys
import unittest
from unittest.mock import patch
import uuid

sys.dont_write_bytecode = True
import prepare_spanish_glosses as gloss


class SpanishGlossImportTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.files, cls.constant, cls.report, cls.corpus = gloss.build(APP, ARCHIVE)
        cls.records = gloss.correction_records(cls.files["corrections.json"])
        cls.sword = gloss.SwordSource(ARCHIVE)

    def test_installed_assets_reproduce(self):
        gloss.verify(APP / gloss.ASSETS_PATH, self.files, self.corpus)
        self.assertEqual((APP / gloss.CONSTANT_PATH).read_bytes().replace(b"\r\n", b"\n"), self.constant)
        self.assertEqual(self.report["coverage"]["importedGlossTokens"], 269777)
        self.assertEqual(self.report["coverage"]["correctedGlossTokens"], 99)
        self.assertEqual(self.report["coverage"]["upstreamMixedStarGlossesCorrected"], 49)

    def test_repeated_generation_is_byte_identical(self):
        files, constant, _, _ = gloss.build(APP, ARCHIVE)
        self.assertEqual(files, self.files)
        self.assertEqual(constant, self.constant)

    def test_wrong_correction_original_is_rejected(self):
        records = copy.deepcopy(self.records)
        records[next(iter(records))]["original"] = "deliberately wrong original"
        with self.assertRaisesRegex(ValueError, "Correction original mismatch"):
            gloss.align(self.corpus, self.sword, records)

    def test_unknown_and_unmatched_correction_ids_are_rejected(self):
        for occurrence in ("TAHOT:Gen.999.1#01", "TAHOT:Gen.2.10#01"):
            with self.subTest(occurrence=occurrence):
                records = copy.deepcopy(self.records)
                records[occurrence] = {"original": "unknown", "corrected": "corregido"}
                with self.assertRaisesRegex(ValueError, "unknown or unmatched occurrence"):
                    gloss.align(self.corpus, self.sword, records)

    def test_duplicate_correction_id_is_rejected(self):
        table = json.loads(self.files["corrections.json"])
        table["corrections"].append(table["corrections"][0])
        with self.assertRaisesRegex(ValueError, "duplicate correction"):
            gloss.correction_records(gloss.json_bytes(table))

    def test_altered_gloss_extra_file_and_wrong_archive_are_rejected(self):
        scratch = self.scratch()
        root = scratch / "assets"
        shutil.copytree(APP / gloss.ASSETS_PATH, root)
        chapter = root / "chapters/GEN.1.json.gz"
        original = chapter.read_bytes()
        payload = json.loads(gzip.decompress(original))
        payload["glosses"]["TAHOT:Gen.1.4#01"] = "wrong"
        chapter.write_bytes(gloss.compressed(gloss.json_bytes(payload)))
        with self.assertRaisesRegex(ValueError, "Source-derived sidecar content differs"):
            gloss.verify(root, self.files, self.corpus)
        chapter.write_bytes(original)
        (root / "extra.txt").write_text("extra", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "inventory differs"):
            gloss.verify(root, self.files, self.corpus)
        archive = scratch / "wrong.zip"
        archive.write_bytes(b"not the pinned archive")
        with self.assertRaisesRegex(ValueError, "SHA-256 mismatch"):
            gloss.SwordSource(archive)

    def test_failed_constant_promotion_restores_previous_assets(self):
        app = self.scratch()
        gloss.install(app, self.files, self.constant, self.corpus)
        with patch.object(Path, "replace", side_effect=OSError("simulated constant promotion failure")):
            with self.assertRaisesRegex(OSError, "simulated constant promotion failure"):
                gloss.install(app, self.files, self.constant, self.corpus)
        gloss.verify(app / gloss.ASSETS_PATH, self.files, self.corpus)
        self.assertEqual((app / gloss.CONSTANT_PATH).read_bytes(), self.constant)

    @unittest.skipUnless(sys.platform == "win32", "Windows transient sharing errors")
    def test_transient_windows_directory_lock_is_retried(self):
        root = self.scratch()
        source, target = root / "old", root / "new"
        source.mkdir()
        (source / "value").write_bytes(b"preserved")
        original = Path.rename
        calls = 0

        def temporary_lock(path, destination):
            nonlocal calls
            calls += 1
            if calls == 1:
                error = PermissionError("temporary Windows file lock")
                error.winerror = 5
                raise error
            return original(path, destination)

        with patch.object(Path, "rename", temporary_lock):
            gloss.rename_directory(source, target)
        self.assertEqual(calls, 2)
        self.assertEqual((target / "value").read_bytes(), b"preserved")

    def scratch(self):
        path = APP / (".spanish-glosses-test-" + uuid.uuid4().hex)
        path.mkdir()
        self.addCleanup(gloss.clean_temporary, path, APP)
        return path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-archive", required=True, type=Path)
    parser.add_argument("--data-root", type=Path, default=Path(__file__).resolve().parent.parent)
    arguments = parser.parse_args()
    APP, ARCHIVE = arguments.data_root.resolve(), arguments.source_archive.resolve()
    unittest.main(argv=[sys.argv[0]], verbosity=2)
