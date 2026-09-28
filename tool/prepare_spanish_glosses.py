#!/usr/bin/env python3
"""Reproduce and verify provisional Spanish OT gloss assets, entirely offline.

Requires Python 3.10+ and its standard library. The explicit input archive,
reference-order snapshot, corpus manifest, and every corpus chapter are
hash-checked before any output is replaced. --verify-only reconstructs the
alignment from those inputs and compares every installed byte and occurrence.
"""

from __future__ import annotations

import argparse
from collections import Counter
import gzip
import hashlib
import io
import json
from pathlib import Path
import shutil
import struct
import sys
import time
import unicodedata
import uuid
import xml.etree.ElementTree as ET
import zipfile
import zlib


SOURCE_COMMIT = "79df943ef7ff280fe6d05c1e7419dcdb655c80b1"
ARCHIVE_SHA256 = "c8844e1dc55c492bda9ae8141ab0df1eb52fac6ff7e92196e214da8068f2f5ff"
MANIFEST_SHA256 = "37af75f19a83b06cd8fe59811bbae07a7c7d97666aef6e4e380626108f531c4c"
MAPPING_SHA256 = "01c0f6e4f5244828bcbf56bd2c3607ac1f513d43745f10dccb75b8a1346b4b05"
EDITION_SHA256 = "9ab7084bec5509a4ce6c7632cbba3aa79bb75563b2cb30f26383abd32cb58a2c"
DATASET_PATH = "assets/interlinear/step-tahot-lqr"
REFERENCE_PATH = "tool/inputs/spanish-ot-reference.json"
REFERENCE_SHA256 = "a58eb41654c415607a956d8cd63255d24d648a4f7c1877d6cd1e44d147525990"
ASSETS_PATH = "assets/interlinear_glosses/es-tahot"
CONSTANT_PATH = "metadata/spanish-manifest.sha256"
CORRECTIONS_PATH = "tool/spanish_gloss_corrections.json"
CORRECTION_REVIEW_STATUS = "AI-assisted corrections; not human-reviewed"
MEMBERS = {
    "mods.d/ljmtintspachirho.conf": "7b2ba705812b41dd287f542317541fd1a9835d55ef387cf5539bd479c88c5454",
    "modules/texts/ztext/LJMTIntSpaChirho/ot.bzs": "bb54045eefdeed1b1c4dcde4a7ceb7b013ce660a0a2783d19438b7de1e43a401",
    "modules/texts/ztext/LJMTIntSpaChirho/ot.bzv": "3102db5b7dfd6e58779b37be6590a38df952b1f8541e8bb45dd2d90f4f4d832e",
    "modules/texts/ztext/LJMTIntSpaChirho/ot.bzz": "f3cf6cba61bc1ad8399d631506f15395f93bb0c56bd5515c8b70125f316e4cac",
}
BOOKS = "GEN EXO LEV NUM DEU JOS JDG RUT 1SA 2SA 1KI 2KI 1CH 2CH EZR NEH EST JOB PSA PRO ECC SNG ISA JER LAM EZK DAN HOS JOL AMO OBA JON MIC NAM HAB ZEP HAG ZEC MAL".split()
BOOK_KEYS = "gn ex lv nm dt js jud rt 1sm 2sm 1kgs 2kgs 1ch 2ch ezr ne et job ps prv ec so is jr lm ez dn ho jl am ob jn mi na hk zp hg zc ml".split()
MATCHING_RULE = (
    "An entire canonical KJV-reference verse must contain the same ordered "
    "original-word surfaces after Unicode NFC. No diacritics/punctuation stripped; "
    "no Strong-only or numerical-only alignment. The hash-bound reference-order "
    "snapshot exported from the historical KJV mapping supplies TAHOT source groups."
)
STRUCTURAL_RULES = [
    "Ignore whitespace and Unicode Cf formatting controls only.",
    "A standalone pe/samekh word with lemma strong:H???? and no morphology is "
    "appended to the preceding word for comparison only. The same exact paragraph "
    "letter must exist in that TAHOT token surface AND be classified as a "
    "punctuation segment, or the verse fails. The paragraph word contributes no translated meaning.",
]
# Explicit, reviewed omissions are whole-token occurrence identities, never
# lexical-number replacements. Reasons are preserved in validation.json.
QUARANTINE: dict[str, str] = {}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def digest(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def checked(path: Path, expected: str) -> bytes:
    require(path.is_file() and not path.is_symlink(), f"Expected ordinary file: {path}")
    content = path.read_bytes()
    require(digest(content) == expected, f"SHA-256 mismatch: {path}")
    return content


def json_bytes(value: object, *, pretty: bool = False) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2 if pretty else None,
                       separators=None if pretty else (",", ":")) + "\n").encode("utf-8")


def compressed(content: bytes) -> bytes:
    # GzipFile fixes the OS byte to 255 across platforms. No filename or time.
    buffer = io.BytesIO()
    with gzip.GzipFile(filename="", mode="wb", fileobj=buffer, mtime=0, compresslevel=9) as stream:
        stream.write(content)
    return buffer.getvalue()


def normalized(surface: str) -> str:
    return unicodedata.normalize("NFC", "".join(
        character for character in surface
        if not character.isspace() and unicodedata.category(character) != "Cf"
    ))


class SwordSource:
    def __init__(self, archive: Path):
        archive_bytes = checked(archive, ARCHIVE_SHA256)
        with zipfile.ZipFile(io.BytesIO(archive_bytes)) as source:
            require(len(source.namelist()) == len(set(source.namelist())), "Duplicate archive member")
            members = {name: source.read(name) for name in MEMBERS}
        for name, content in members.items():
            require(digest(content) == MEMBERS[name], f"Archive member mismatch: {name}")
        self.configuration = members["mods.d/ljmtintspachirho.conf"]
        prefix = "modules/texts/ztext/LJMTIntSpaChirho/ot."
        self.blocks, self.verses, self.content = [members[prefix + suffix] for suffix in ("bzs", "bzv", "bzz")]
        require(len(self.blocks) % 12 == 0 and len(self.verses) % 10 == 0, "Invalid SWORD index width")
        self.cache: dict[int, bytes] = {}

    def words(self, index: int) -> list[dict]:
        require(0 <= index < len(self.verses) // 10, f"SWORD verse index outside archive: {index}")
        block, offset, length = struct.unpack_from("<IIH", self.verses, index * 10)
        if not length:
            return []
        require(block < len(self.blocks) // 12, "SWORD block outside archive")
        if block not in self.cache:
            start, size, raw_size = struct.unpack_from("<III", self.blocks, block * 12)
            require(start + size <= len(self.content), "SWORD block bounds mismatch")
            raw = zlib.decompress(self.content[start:start + size])
            require(len(raw) == raw_size, "SWORD decompressed block length mismatch")
            self.cache[block] = raw
        raw = self.cache[block]
        require(offset + length <= len(raw), "SWORD verse bounds mismatch")
        xml = ET.fromstring("<r>" + raw[offset:offset + length].decode("utf-8") + "</r>")
        return [{"surface": "".join(word.itertext()), "gloss": word.get("gloss", ""),
                 "lemma": word.get("lemma", ""), "morph": word.get("morph", "")}
                for word in xml.iter("w")]


class Corpus:
    def __init__(self, app: Path):
        self.manifest = json.loads(checked(app / DATASET_PATH / "manifest.json", MANIFEST_SHA256))
        self.reference = json.loads(checked(app / REFERENCE_PATH, REFERENCE_SHA256))
        require(self.reference["sourceEditionSha256"] == EDITION_SHA256
                and self.reference["sourceMappingSha256"] == MAPPING_SHA256
                and self.reference["sourceManifestSha256"] == MANIFEST_SHA256,
                "Reference snapshot provenance mismatch")
        self.selections = {
            f"{book['book']}.{chapter['chapter']}.{verse['verse']}": verse["sources"]
            for book in self.reference["books"] for chapter in book["chapters"] for verse in chapter["verses"]
        }
        self.resources: dict[tuple[str, int], dict] = {}
        self.groups: dict[tuple[str, int, bool, str], list[dict]] = {}
        self.owners: dict[str, tuple[str, int]] = {}
        for resource in self.manifest["chapters"]:
            key = (resource["book"], resource["chapter"])
            require(key not in self.resources, f"Duplicate source chapter: {key}")
            path = f"chapters/{key[0]}.{key[1]}.json"
            require(resource["path"] == path, "Noncanonical source chapter path")
            transport = app / DATASET_PATH / (path + ".gz")
            require(transport.is_file() and not transport.is_symlink(), f"Invalid source chapter: {transport}")
            content = gzip.decompress(transport.read_bytes())
            require(digest(content) == resource["sha256"], f"Source chapter SHA-256 mismatch: {path}")
            chapter = json.loads(content)
            require((chapter["book"], chapter["chapter"]) == key, f"Source chapter identity mismatch: {path}")
            self.resources[key] = resource
            for special, entries in ((False, chapter["verses"]), (True, chapter["specialEntries"])):
                for entry in entries:
                    label = entry["sourceLabel"] if special else entry["label"]
                    group_key = (*key, special, label)
                    require(group_key not in self.groups, "Duplicate source verse/special entry")
                    tokens = []
                    for token in entry["tokens"]:
                        occurrence = token["occurrenceId"]
                        require(occurrence not in self.owners, f"Duplicate source occurrence: {occurrence}")
                        self.owners[occurrence] = key
                        tokens.append({"occurrenceId": occurrence, "surface": token["surface"],
                                       "punctuation": [part["text"] for part in token["segments"]
                                                       if part["kind"] == "punctuation"]})
                    self.groups[group_key] = tokens
        require(len(self.resources) == 929 and len(self.owners) == 305486, "Pinned TAHOT coverage changed")

    def tokens(self, reference: str) -> list[dict]:
        result = []
        for selection in self.selections[reference]:
            require("occurrenceIds" not in selection, "Pinned OT mapping has an unexpected subset")
            special = "specialEntryLabel" in selection
            label = selection["specialEntryLabel"] if special else selection["verseLabel"]
            result.extend(self.groups[(selection["book"], selection["chapter"], special, label)])
        return result


def merge_markers(words: list[dict]) -> list[dict]:
    result: list[dict] = []
    for word in words:
        if result and word["surface"] in ("פ", "ס") and word["lemma"] == "strong:H????" and not word["morph"]:
            # One standalone marker per token is the pinned source contract.
            require("marker" not in result[-1], "Multiple structural markers on a word")
            result[-1] = {**result[-1], "surface": result[-1]["surface"] + word["surface"],
                          "marker": word["surface"]}
        else:
            result.append(word)
    return result


def correction_records(content: bytes) -> dict[str, dict]:
    table = json.loads(content)
    require(table.get("schemaVersion") == 1 and table.get("reviewStatus") == CORRECTION_REVIEW_STATUS,
            "Unexpected correction schema/review status")
    records = {}
    for record in table["corrections"]:
        occurrence = record.get("occurrenceId")
        require(isinstance(occurrence, str) and occurrence.startswith("TAHOT:") and occurrence not in records,
                f"Invalid/duplicate correction occurrence: {occurrence}")
        require(isinstance(record.get("original"), str) and isinstance(record.get("corrected"), str),
                f"Correction must preserve original and corrected strings: {occurrence}")
        require(record["original"] != record["corrected"] and "*" not in record["corrected"]
                and any(unicodedata.category(c).startswith("L") for c in record["corrected"]),
                f"Correction is unchanged or still a placeholder: {occurrence}")
        require(bool(record.get("reason")) and bool(record.get("evidence")),
                f"Correction lacks reason/evidence: {occurrence}")
        records[occurrence] = record
    return records


def align(corpus: Corpus, sword: SwordSource, corrections: dict[str, dict]) -> tuple[dict, dict]:
    chapters: dict[tuple[str, int], dict[str, str]] = {}
    counts: Counter = Counter()
    accepted, refused, excluded, mixed_placeholders, quarantined = [], [], [], [], []
    source_seen: set[str] = set()
    applied_corrections: set[str] = set()
    cursor = 2
    require(not sword.words(0) and not sword.words(1), "Unexpected testament header words")
    require([item["book"] for item in corpus.reference["books"]] == BOOKS, "Pinned OT book order changed")
    for book_entry in corpus.reference["books"]:
        book = book_entry["book"]
        require(not sword.words(cursor), "Unexpected book header words")
        cursor += 1
        for chapter_entry in book_entry["chapters"]:
            chapter = chapter_entry["chapter"]
            require(not sword.words(cursor), "Unexpected chapter header words")
            cursor += 1
            for verse_entry in chapter_entry["verses"]:
                verse = verse_entry["verse"]
                reference = f"{book}.{chapter}.{verse}"
                actual, expected = merge_markers(sword.words(cursor)), corpus.tokens(reference)
                cursor += 1
                counts["candidateOtVerses"] += 1
                counts["sourceTokens"] += len(expected)
                for token in expected:
                    require(token["occurrenceId"] not in source_seen, "Correspondence repeats a source occurrence")
                    source_seen.add(token["occurrenceId"])
                matches = [normalized(t["surface"]) for t in actual] == [normalized(t["surface"]) for t in expected]
                if matches:
                    matches = all(not word.get("marker") or word["marker"] in token["punctuation"]
                                  for word, token in zip(actual, expected))
                if not matches:
                    refused.append(reference)
                    continue
                accepted.append(reference)
                counts["exactNormalizedTokens"] += len(expected)
                for word, token in zip(actual, expected):
                    occurrence, gloss = token["occurrenceId"], word["gloss"]
                    if occurrence in corrections:
                        correction = corrections[occurrence]
                        require(gloss == correction["original"], f"Correction original mismatch: {occurrence}")
                        require(occurrence not in applied_corrections, f"Repeated correction: {occurrence}")
                        if "*" in gloss and gloss.strip() != "*":
                            counts["upstreamMixedStarGlossesCorrected"] += 1
                        gloss = correction["corrected"]
                        applied_corrections.add(occurrence)
                    if not gloss.strip() or gloss.strip() == "*":
                        counts["upstreamEmptyOrStarGlossesExcluded"] += 1
                        continue
                    if "*" in gloss:
                        mixed_placeholders.append({"occurrenceId": occurrence, "rawGloss": gloss,
                                                   "reason": "Mixed asterisk placeholder is not a complete Spanish meaning."})
                        continue
                    if not any(unicodedata.category(c).startswith("L") for c in gloss):
                        excluded.append(occurrence)
                        continue
                    if occurrence in QUARANTINE:
                        quarantined.append(occurrence)
                        continue
                    key = corpus.owners[occurrence]
                    chapter_glosses = chapters.setdefault(key, {})
                    require(occurrence not in chapter_glosses, "Duplicate imported occurrence")
                    chapter_glosses[occurrence] = gloss
    require(cursor * 10 == len(sword.verses), "SWORD verse index has missing or extra records")
    require(source_seen == set(corpus.owners), "KJV correspondence does not cover every source occurrence")
    require(applied_corrections == set(corrections),
            "Correction contains an unknown or unmatched occurrence: " + ", ".join(sorted(set(corrections) - applied_corrections)))
    require(set(quarantined) == set(QUARANTINE), "Quarantine contains an unknown or otherwise omitted occurrence")
    counts.update({"exactNormalizedVerses": len(accepted), "refusedVerses": len(refused),
                   "upstreamMixedStarGlossesExcluded": len(mixed_placeholders),
                   "correctedGlossTokens": len(applied_corrections),
                   "nonverbalGlossesExcluded": len(excluded), "quarantinedGlossesExcluded": len(quarantined),
                   "importedGlossTokens": sum(map(len, chapters.values())), "chaptersWithAnyGlosses": len(chapters)})
    require(counts["candidateOtVerses"] == 23145 and counts["exactNormalizedVerses"] == 20834
            and counts["exactNormalizedTokens"] == 270141 and counts["refusedVerses"] == 2311
            and counts["upstreamEmptyOrStarGlossesExcluded"] == 98 and len(excluded) == 266
            and len(mixed_placeholders) + counts["upstreamMixedStarGlossesCorrected"] == 49
            and counts["importedGlossTokens"] == 269777 - len(mixed_placeholders) - len(QUARANTINE), "Pinned alignment coverage changed")
    report = {"schemaVersion": 1, "validation": "All included alignments and occurrence identities verified; not a human linguistic review.",
              "coverage": dict(counts), "sourceChaptersVerified": len(corpus.resources),
              "matchedVerseReferencesSha256": digest(json_bytes(accepted)), "refusedVerseReferences": refused,
              "nonverbalGlossOccurrenceIds": excluded,
              "mixedStarGlossExclusions": mixed_placeholders,
              "appliedCorrectionOccurrenceIds": sorted(applied_corrections),
              "quarantinedGlosses": [{"occurrenceId": item, "reason": QUARANTINE[item]} for item in quarantined]}
    return chapters, report


def build(app: Path, archive: Path) -> tuple[dict[str, bytes], bytes, dict, Corpus]:
    corpus, sword = Corpus(app), SwordSource(archive)
    corrections_bytes = Path(__file__).with_name("spanish_gloss_corrections.json").read_bytes().replace(b"\r\n", b"\n")
    corrections = correction_records(corrections_bytes)
    chapters, report = align(corpus, sword, corrections)
    files = {"validation.json": json_bytes(report, pretty=True), "source-module.conf": sword.configuration,
             "corrections.json": corrections_bytes}
    resources = []
    for key, glosses in sorted(chapters.items(), key=lambda item: f"{item[0][0]}.{item[0][1]}"):
        book, chapter = key
        payload = {"schemaVersion": 1, "book": book, "chapter": chapter, "language": "es",
                   "sourceChapterSha256": corpus.resources[key]["sha256"], "glosses": glosses}
        content = json_bytes(payload)
        path = f"chapters/{book}.{chapter}.json.gz"
        files[path] = compressed(content)
        resources.append({"path": path, "book": book, "chapter": chapter, "sha256": digest(content),
                          "compressedSha256": digest(files[path]), "bytes": len(files[path]), "tokens": len(glosses)})
    repository = "https://github.com/loveJesus/sword-modules-chirho"
    notice = f"""# Provisional Spanish contextual glosses

Love Jesus / Global Bible Tools, LJMTIntSpaChirho 1.0.
Source: {repository}/tree/{SOURCE_COMMIT}
Archive: https://raw.githubusercontent.com/loveJesus/sword-modules-chirho/{SOURCE_COMMIT}/raw/LJMTIntSpaChirho.zip
License: Creative Commons Attribution 4.0 International (CC BY 4.0).
License text: https://creativecommons.org/licenses/by/4.0/
The original module distribution notice is preserved in source-module.conf.

The upstream README identifies these as AI-assisted machine translations that
have not been fully reviewed by human translators. They are provisional study
meanings, not an authoritative translation or the selected Spanish Bible text.
Upstream notice: {repository}/blob/{SOURCE_COMMIT}/README.md

Modifications: extracted OT gloss attributes; retained only exact ordered
whole-verse Hebrew/Aramaic matches under the documented structural normalization;
applied the exact occurrence-specific corrections recorded in corrections.json,
preserving their original strings, reasons and evidence; omitted remaining
empty/star/mixed-star placeholders, nonverbal values and explicit quarantines;
attached gloss strings to existing TAHOT occurrence IDs; split and compressed
per-chapter sidecars. Local corrections are AI-assisted and have not received
human linguistic review. Hebrew/Aramaic text, morphology and original English glosses
were not modified. Full alignment/hash validation is not full human linguistic
validation. Missing meanings retain the app's explicit English fallback.
"""
    files["NOTICE.md"] = notice.encode("utf-8")
    metadata = corpus.manifest["metadata"]
    manifest = {
        "schemaVersion": 1, "status": "provisional", "installed": True, "language": "es",
        "kind": "original-language contextual study gloss",
        "reviewStatus": "upstream AI-assisted; not fully human-reviewed",
        "provider": "Love Jesus / Global Bible Tools", "module": "LJMTIntSpaChirho", "moduleVersion": "1.0",
        "sourceRepository": repository, "sourceCommit": SOURCE_COMMIT,
        "sourceUrl": f"https://raw.githubusercontent.com/loveJesus/sword-modules-chirho/{SOURCE_COMMIT}/raw/LJMTIntSpaChirho.zip",
        "sourceZipSha256": ARCHIVE_SHA256, "sourceMemberSha256": MEMBERS,
        "license": "CC-BY-4.0", "licenseUrl": "https://creativecommons.org/licenses/by/4.0/",
        "upstreamNoticeUrl": f"{repository}/blob/{SOURCE_COMMIT}/README.md",
        "moduleLicenseUrl": f"{repository}/blob/{SOURCE_COMMIT}/mods.d/ljmtintspachirho.conf",
        "boundDataset": {**{key: metadata[key] for key in ("datasetId", "datasetRevision", "sourceRevision", "profile", "referenceSystem", "readingPolicy")},
                         "manifestSha256": MANIFEST_SHA256},
        "correspondence": {"path": REFERENCE_PATH, "sha256": REFERENCE_SHA256,
                           "historicalMappingSha256": MAPPING_SHA256, "historicalEditionSha256": EDITION_SHA256},
        "generator": {"path": "tool/prepare_spanish_glosses.py", "sha256": digest(Path(__file__).read_bytes().replace(b"\r\n", b"\n")),
                      "correctionsPath": CORRECTIONS_PATH, "correctionsSha256": digest(corrections_bytes),
                      "serialization": "UTF-8 JSON with LF; deterministic gzip level 9, mtime 0, no filename, OS 255"},
        "localCorrections": {"path": "corrections.json", "sha256": digest(corrections_bytes),
                             "count": len(corrections), "reviewStatus": CORRECTION_REVIEW_STATUS},
        "matchingRule": MATCHING_RULE, "structuralRules": STRUCTURAL_RULES, "coverage": report["coverage"],
        "modifications": ["Extracted word gloss attributes from pinned SWORD zText OSIS records.",
                          "Required full ordered original-surface agreement; attached meanings to TAHOT occurrences.",
                          "Applied only documented occurrence-specific AI-assisted corrections after checking exact original gloss strings.",
                          "Omitted empty/star/mixed-star/nonverbal placeholders and explicitly quarantined meanings.",
                          "Stored whole-token meanings as separately hash-bound compressed chapter sidecars."],
        "limitations": ["AI-assisted Spanish wording has not been fully reviewed by human translators.",
                        "Local corrections preserve provenance but are AI-assisted, not human linguistic validation.",
                        "A technical alignment/hash pass does not validate linguistic meaning.",
                        "These are contextual whole-token glosses, not Spanish morphology or dictionary definitions.",
                        "Unmatched verses and omitted glosses receive no imported Spanish meaning.",
                        "Uncorrected provider spellings such as Elohim are preserved; these are not RVA translation words."],
        "additionalResources": [{"path": name, "sha256": digest(content)} for name, content in sorted(files.items()) if not name.startswith("chapters/")],
        "chapterResources": resources,
    }
    files["manifest.json"] = json_bytes(manifest, pretty=True)
    constant = (digest(files["manifest.json"]) + "\n").encode("ascii")
    return files, constant, report, corpus


def verify(root: Path, expected: dict[str, bytes], corpus: Corpus) -> None:
    require(root.is_dir() and not root.is_symlink(), f"Missing/unsafe sidecar directory: {root}")
    entries = list(root.rglob("*"))
    require(not any(path.is_symlink() for path in entries), "Sidecars must not contain symlinks")
    actual_paths = {path.relative_to(root).as_posix() for path in entries if path.is_file()}
    require(actual_paths == set(expected), "Sidecar inventory differs (missing or extra files)")
    manifest = json.loads(expected["manifest.json"])
    seen: set[str] = set()
    for name, content in expected.items():
        require((root / name).read_bytes() == content, f"Source-derived sidecar content differs: {name}")
    for resource in manifest["chapterResources"]:
        raw = gzip.decompress((root / resource["path"]).read_bytes())
        require(digest(raw) == resource["sha256"], "Sidecar uncompressed SHA-256 mismatch")
        payload = json.loads(raw)
        key = (resource["book"], resource["chapter"])
        require(payload["sourceChapterSha256"] == corpus.resources[key]["sha256"], "Sidecar source chapter binding mismatch")
        require(len(payload["glosses"]) == resource["tokens"], "Sidecar token count mismatch")
        for occurrence, gloss in payload["glosses"].items():
            require(occurrence not in seen and corpus.owners.get(occurrence) == key, f"Wrong/duplicate occurrence identity: {occurrence}")
            require(any(unicodedata.category(character).startswith("L") for character in gloss), "Nonverbal placeholder in installed sidecar")
            require("*" not in gloss, "Asterisk placeholder in installed sidecar")
            seen.add(occurrence)
    require(len(seen) == manifest["coverage"]["importedGlossTokens"], "Installed coverage mismatch")


def clean_temporary(path: Path, parent: Path) -> None:
    require(path.resolve().parent == parent.resolve() and path.name.startswith(".spanish-glosses-")
            and not path.is_symlink(), f"Refusing unexpected recursive cleanup: {path}")
    shutil.rmtree(path)


def rename_directory(source: Path, target: Path) -> None:
    # On Windows, an antivirus/indexer handle can briefly keep the just-vacated
    # target name locked. Retry only those sharing/access errors, never swallow
    # a persistent failure; install() still preserves recovery data in that case.
    for attempt in range(7):
        try:
            source.rename(target)
            return
        except PermissionError as error:
            if sys.platform != "win32" or getattr(error, "winerror", None) not in (5, 32, 33) or attempt == 6:
                raise
            time.sleep(0.05 * (attempt + 1))


def install(app: Path, files: dict[str, bytes], constant: bytes, corpus: Corpus) -> None:
    target, constant_file = app / ASSETS_PATH, app / CONSTANT_PATH
    target.parent.mkdir(parents=True, exist_ok=True)
    require(not target.is_symlink() and target.resolve().parent == target.parent.resolve(), "Unsafe sidecar destination")
    # Python 3.13+ gives Windows mkdtemp directories a restrictive 0700 ACL.
    # These public app assets must inherit the workspace ACL after promotion.
    scratch = target.parent / (".spanish-glosses-" + uuid.uuid4().hex)
    scratch.mkdir(mode=0o777)
    staged, previous = scratch / "new", scratch / "previous"
    old_constant = constant_file.read_bytes() if constant_file.exists() else None
    promoted = False
    cleanup = True
    try:
        for name, content in files.items():
            path = staged / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)
        verify(staged, files, corpus)
        if target.exists():
            existing = json.loads((target / "manifest.json").read_bytes())
            require(existing.get("module") == "LJMTIntSpaChirho" and existing.get("language") == "es", "Refusing to replace unrecognized directory")
            rename_directory(target, previous)
        rename_directory(staged, target)
        promoted = True
        constant_file.parent.mkdir(parents=True, exist_ok=True)
        temporary_constant = scratch / "spanish_gloss_asset.dart"
        temporary_constant.write_bytes(constant)
        temporary_constant.replace(constant_file)
        verify(target, files, corpus)
    except Exception:
        try:
            if promoted:
                rename_directory(target, scratch / "failed")
            if previous.exists():
                rename_directory(previous, target)
            if old_constant is not None:
                constant_file.write_bytes(old_constant)
            elif constant_file.exists():
                constant_file.unlink()
        except Exception:
            # Never delete a previous bundle if a filesystem error interrupts
            # rollback. Retain the complete recovery directory for inspection.
            cleanup = False
            print(f"Recovery data retained at {scratch}", file=sys.stderr)
            raise
        raise
    finally:
        if cleanup:
            clean_temporary(scratch, target.parent)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-archive", required=True, type=Path, help="Pinned local LJMTIntSpaChirho.zip; no network is used")
    parser.add_argument("--data-root", type=Path, default=Path(__file__).resolve().parent.parent)
    parser.add_argument("--verify-only", action="store_true", help="Recompute all alignments and verify installed bytes without writing")
    arguments = parser.parse_args()
    app = arguments.data_root.resolve()
    files, constant, report, corpus = build(app, arguments.source_archive.resolve())
    if arguments.verify_only:
        verify(app / ASSETS_PATH, files, corpus)
        require((app / CONSTANT_PATH).read_bytes().replace(b"\r\n", b"\n") == constant, "Manifest digest record differs")
    else:
        install(app, files, constant, corpus)
    print(json.dumps({"result": "verified" if arguments.verify_only else "generated-and-verified",
                      "manifestSha256": digest(files["manifest.json"]), "coverage": report["coverage"],
                      "sourceChaptersVerified": len(corpus.resources), "files": len(files),
                      "assetBytes": sum(map(len, files.values()))}, sort_keys=True))


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError, KeyError, ET.ParseError, zipfile.BadZipFile, zlib.error) as error:
        print(f"Spanish gloss operation failed: {error}", file=sys.stderr)
        sys.exit(1)
