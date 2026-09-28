#!/usr/bin/env python3
"""Seal or verify the prepared data catalog. No network or Flutter required."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VERSION = "0.1.0"
DATASETS = ("step-tahot-lqr", "step-tagnt-n")


def digest(content):
    return hashlib.sha256(content).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read(root, path):
    return json.loads((root / path).read_bytes())


def inventory(root):
    result = []
    # Sort strings: Path ordering is case-insensitive on Windows, unlike Linux.
    for path in sorted((root / "assets").rglob("*"), key=lambda path: path.relative_to(root).as_posix()):
        require(not path.is_symlink(), f"Symlink in data: {path}")
        if path.is_file():
            content = path.read_bytes()
            result.append({"path": path.relative_to(root).as_posix(), "bytes": len(content), "sha256": digest(content)})
    return result


def validate(root):
    """Read every chapter, check hashes, identity, coverage and sidecar ownership."""
    owners, source_hashes = {}, {}
    expected_files = set()
    summaries = []
    for dataset, count, token_count in ((DATASETS[0], 929, 305486), (DATASETS[1], 260, 137646)):
        base = f"assets/interlinear/{dataset}"
        raw_manifest = (root / base / "manifest.json").read_bytes()
        manifest = json.loads(raw_manifest)
        expected_files.add(f"{base}/manifest.json")
        # The core codec binds attribution and chapter JSON to the manifest.
        attribution = manifest["attribution"]
        expected_files.add(f"{base}/{attribution['path']}")
        require(digest((root / base / attribution["path"]).read_bytes()) == attribution["sha256"], "Attribution hash mismatch")
        seen = set()
        for resource in manifest["chapters"]:
            canonical = f"chapters/{resource['book']}.{resource['chapter']}.json"
            require(resource["path"] == canonical, "Unexpected corpus chapter path")
            expected_files.add(f"{base}/{canonical}.gz")
            raw = gzip.decompress((root / base / (canonical + ".gz")).read_bytes())
            require(digest(raw) == resource["sha256"], f"Chapter hash mismatch: {canonical}")
            chapter = json.loads(raw)
            key = (chapter["book"], chapter["chapter"])
            require(key == (resource["book"], resource["chapter"]), "Chapter identity mismatch")
            for entry in chapter["verses"] + chapter["specialEntries"]:
                for token in entry["tokens"]:
                    occurrence = token["occurrenceId"]
                    require(occurrence not in seen, "Duplicate source occurrence")
                    seen.add(occurrence)
                    if dataset == DATASETS[0]:
                        owners[occurrence] = key
            if dataset == DATASETS[0]:
                source_hashes[key] = resource["sha256"]
        require(len(manifest["chapters"]) == count and len(seen) == token_count, "Source coverage changed")
        summaries.append({"id": dataset, "manifestPath": f"{base}/manifest.json", "manifestSha256": digest(raw_manifest),
                          "chapters": count, "tokens": token_count, "humanReview": "Published source; not independently fully human-reviewed by this project"})
    for name in ("asset-index.json", "provenance.json", "sources.lock.json", "THIRD_PARTY_NOTICES.md"):
        expected_files.add(f"assets/interlinear/{name}")
    provenance = read(root, "assets/interlinear/provenance.json")
    for entry in provenance["transportResources"]:
        content = (root / "assets/interlinear" / entry["assetPath"]).read_bytes()
        require(digest(content) == entry["transportSha256"] and len(content) == entry["transportBytes"], "Historical transport bytes changed")
    known_generators = ["provenance/generate_interlinear_assets.original.dart", "tool/generate_interlinear_assets.dart"]
    require(provenance["generatorSha256"] in {
        digest((root / name).read_bytes().replace(b"\r\n", b"\n")) for name in known_generators
    }, "Dataset provenance generator mismatch")
    base = "assets/interlinear_glosses/es-tahot"
    raw_manifest = (root / base / "manifest.json").read_bytes()
    manifest = json.loads(raw_manifest)
    expected_files.add(f"{base}/manifest.json")
    require(manifest["boundDataset"]["manifestSha256"] == summaries[0]["manifestSha256"], "Spanish source binding mismatch")
    seen = set()
    for resource in manifest["chapterResources"]:
        canonical = f"chapters/{resource['book']}.{resource['chapter']}.json.gz"
        require(resource["path"] == canonical, "Unexpected gloss path")
        expected_files.add(f"{base}/{canonical}")
        content = (root / base / canonical).read_bytes()
        raw = gzip.decompress(content)
        require(digest(content) == resource["compressedSha256"] and len(content) == resource["bytes"], "Spanish transport mismatch")
        require(digest(raw) == resource["sha256"], "Spanish chapter hash mismatch")
        chapter = json.loads(raw)
        key = (resource["book"], resource["chapter"])
        require((chapter["book"], chapter["chapter"]) == key and chapter["sourceChapterSha256"] == source_hashes[key], "Spanish chapter identity mismatch")
        require(len(chapter["glosses"]) == resource["tokens"], "Spanish chapter count mismatch")
        for occurrence, gloss in chapter["glosses"].items():
            require(occurrence not in seen and owners.get(occurrence) == key, "Wrong/duplicate Spanish occurrence")
            require(isinstance(gloss, str) and gloss.strip() and "*" not in gloss, "Spanish placeholder")
            seen.add(occurrence)
    require(len(seen) == 269777 and len(manifest["chapterResources"]) == 928, "Spanish coverage changed")
    for resource in manifest["additionalResources"]:
        require("/" not in resource["path"] and "\\" not in resource["path"], "Unsafe additional resource")
        expected_files.add(f"{base}/{resource['path']}")
        require(digest((root / base / resource["path"]).read_bytes()) == resource["sha256"], "Spanish provenance mismatch")
    for path, expected in ((manifest["generator"]["path"], manifest["generator"]["sha256"]),
                           (manifest["generator"]["correctionsPath"], manifest["generator"]["correctionsSha256"]),
                           (manifest["correspondence"]["path"], manifest["correspondence"]["sha256"])):
        require(digest((root / path).read_bytes().replace(b"\r\n", b"\n")) == expected, f"Generation input changed: {path}")
    require((root / "metadata/spanish-manifest.sha256").read_text().strip() == digest(raw_manifest), "Spanish digest record mismatch")
    require({item["path"] for item in inventory(root)} == expected_files, "Missing or extra prepared data files")
    summaries.append({"id": "es-tahot", "manifestPath": f"{base}/manifest.json", "manifestSha256": digest(raw_manifest),
                      "chapters": 928, "tokens": len(seen), "humanReview": "Provisional AI-assisted; not fully human-reviewed; 99 AI-assisted corrections"})
    return summaries


def build(root):
    datasets = validate(root)
    sources = {}
    for path in sorted((root / "tool").rglob("*"), key=lambda path: path.relative_to(root).as_posix()):
        if path.is_file() and path.suffix in (".py", ".dart", ".json"):
            sources[path.relative_to(root).as_posix()] = digest(path.read_bytes().replace(b"\r\n", b"\n"))
    return {"schemaVersion": 1, "name": "bible_io_interlinear_data", "version": VERSION,
            "datasets": datasets, "generationInputs": sources, "files": inventory(root)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="Explicitly seal a new catalog after validation")
    parser.add_argument("--data-root", type=Path, default=ROOT)
    args = parser.parse_args()
    root = args.data_root.resolve()
    content = (json.dumps(build(root), ensure_ascii=False, indent=2) + "\n").encode()
    path = root / "catalog.json"
    if args.write:
        path.write_bytes(content)
    else:
        require(path.read_bytes() == content, "Catalog differs; review changes before --write")
    print(f"Verified all data; catalog SHA-256: {digest(content)}")


if __name__ == "__main__":
    main()
