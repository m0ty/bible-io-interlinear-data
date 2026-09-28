#!/usr/bin/env python3
"""Export the pinned SWORD OT reference order and TAHOT selectors, without Bible text.

This is a one-time provenance input, not an app edition mapping. Re-export only
from the exact historical KJV files used for the original Spanish alignment.
"""
import argparse
import hashlib
import json
from pathlib import Path

EDITION_SHA256 = "9ab7084bec5509a4ce6c7632cbba3aa79bb75563b2cb30f26383abd32cb58a2c"
MAPPING_SHA256 = "01c0f6e4f5244828bcbf56bd2c3607ac1f513d43745f10dccb75b8a1346b4b05"
MANIFEST_SHA256 = "37af75f19a83b06cd8fe59811bbae07a7c7d97666aef6e4e380626108f531c4c"
BOOKS = "GEN EXO LEV NUM DEU JOS JDG RUT 1SA 2SA 1KI 2KI 1CH 2CH EZR NEH EST JOB PSA PRO ECC SNG ISA JER LAM EZK DAN HOS JOL AMO OBA JON MIC NAM HAB ZEP HAG ZEC MAL".split()
KEYS = "gn ex lv nm dt js jud rt 1sm 2sm 1kgs 2kgs 1ch 2ch ezr ne et job ps prv ec so is jr lm ez dn ho jl am ob jn mi na hk zp hg zc ml".split()


def read(path, expected):
    content = path.read_bytes()
    if hashlib.sha256(content).hexdigest() != expected:
        raise ValueError(f"Wrong pinned input: {path}")
    return json.loads(content)


def export(edition, mapping):
    text = read(edition, EDITION_SHA256)
    table = read(mapping, MAPPING_SHA256)
    if list(text["books"])[:39] != KEYS:
        raise ValueError("OT book order changed")
    books = []
    for book, key in zip(BOOKS, KEYS):
        chapters = []
        for number, verses in text["books"][key]["chapters"].items():
            entries = []
            for verse in verses:
                entry = table["entries"][f"{book}.{number}.{verse}"]
                if entry["status"] != "matched" or entry["datasetId"] != "step-tahot-lqr":
                    raise ValueError("Unexpected OT selector")
                entries.append({"verse": verse, "sources": entry["sources"]})
            chapters.append({"chapter": int(number), "verses": entries})
        books.append({"book": book, "chapters": chapters})
    result = {"schemaVersion": 1, "purpose": "SWORD KJV reference order to TAHOT source groups; no translation text",
              "sourceEditionSha256": EDITION_SHA256, "sourceMappingSha256": MAPPING_SHA256,
              "sourceManifestSha256": MANIFEST_SHA256, "books": books}
    return (json.dumps(result, ensure_ascii=False, separators=(",", ":")) + "\n").encode()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--edition", required=True, type=Path)
    parser.add_argument("--mapping", required=True, type=Path)
    parser.add_argument("--output", type=Path, default=Path(__file__).parent / "inputs/spanish-ot-reference.json")
    args = parser.parse_args()
    content = export(args.edition, args.mapping)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(content)
    print(hashlib.sha256(content).hexdigest())
