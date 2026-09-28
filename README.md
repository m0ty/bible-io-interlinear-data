# Bible IO interlinear data

Versioned prepared Hebrew, Aramaic, Greek and Spanish study data for
[`bible_io_interlinear`](https://github.com/m0ty/bible-io-interlinear-dart).
Consumers can fetch these files during setup or a build, then run entirely
offline. This repository owns the data, corrections, provenance, licenses and
generation tools. The core Dart package owns the models, parsers and importers;
apps own their UI and translation-specific passage mappings.

This is a data distribution, not a Flutter runtime dependency. `pubspec.yaml`
resolves the tools' pinned Dart dependencies; `dart pub get` does not download
upstream sources, regenerate data, or install assets into another application.

## Included data and validation

**Complete technical validation is not complete human linguistic validation.**
No dataset has received a new complete human review by this project.

| Dataset | Complete technical checks | Human-review status |
| --- | --- | --- |
| STEPBible TAHOT `L+Q+R`, qere | 929 chapters and 305,486 Hebrew/Aramaic tokens; original identity, chapter hashes and transport hashes | Published source, preserved unchanged; not independently fully human-reviewed here |
| STEPBible TAGNT `N` | 260 chapters and 137,646 Greek tokens, including source English and Spanish meanings | Published source; English attribution includes Berean Study Bible and Spanish includes Marvel Bible Project/OpenGNT. Attribution does not certify every meaning as human validated |
| Spanish TAHOT supplement, LJMTIntSpaChirho | 928 sidecars, 269,777 meanings; every included occurrence has exact ordered whole-verse Hebrew/Aramaic matching and source/hash binding | **Provisional, AI-assisted, not fully human-reviewed.** The 99 local corrections and sample review are also AI-assisted |

The Spanish supplement covers 88.3% of TAHOT occurrences. It refuses 2,311 verse
sequences; consumers should use an explicitly labeled fallback for missing
Spanish. It includes the 49 repaired placeholder entries. Original wording,
replacements, reasons and evidence remain in
[the correction log](tool/spanish_gloss_corrections.json). See
[technical rules](doc/spanish_gloss_assets.md),
[review limitations](doc/spanish_gloss_validation.md), and
[original corpus provenance](doc/interlinear_assets.md).

TAHOT follows qere and TAGNT uses the `N` profile. Coverage does not imply that
every source reading or every translation's numbering agrees. These are study
meanings of original words, not word alignments to a particular Spanish Bible.

## Use the prepared data

Clone or download this repository. `catalog.json` inventories every consumable
file using its size and SHA-256. Pin the catalog hash in the consuming app, then
verify it before trusting individual file hashes. Consumer code should never
execute downloaded tools as part of a fetch.

The BibleIO Flutter app provides:

```sh
python tool/fetch_interlinear_data.py --source ../bible-io-interlinear-data
python tool/fetch_interlinear_data.py --verify-only
```

Those commands run **from the app**, materializing its ignored build assets.
The app's edition mappings remain app-owned. Its default fetch reuses verified
local assets, tries a matching sibling checkout, then downloads the URL in
`interlinear_data.lock.json`. No download occurs at app startup.

To verify this repository independently (Python 3.10+, standard library):

```sh
python tool/catalog.py
```

This reads every corpus and supplement chapter, checks identity and ownership,
coverage, attribution, compressed/uncompressed hashes, generator inputs, and
the complete data inventory. It does not require Dart, Flutter, raw sources or
network access. Full linguistic accuracy still requires human review.

## Reproduce the data

Dart 3.11.4 and the committed lockfile pin the corpus tooling dependencies:

```sh
dart pub get --enforce-lockfile
dart run tool/acquire_sources.dart --output .work/sources
dart run tool/generate_interlinear_assets.dart --source-root .work/sources --output .work/rebuilt-step
```

Acquisition is explicit and verifies all six pinned upstream files. The
generator uses the core package's importers and verifies all resulting chapters.
Use a scratch output first. Original chapter bytes are deterministic; an updated
generator or SDK can change the generation provenance. The committed
`provenance.json` retains the original import record, and
`provenance/generate_interlinear_assets.original.dart` preserves its exact
historical generator. It is a record, not the current entry point.

For Spanish, separately download the [pinned source ZIP](https://raw.githubusercontent.com/loveJesus/sword-modules-chirho/79df943ef7ff280fe6d05c1e7419dcdb655c80b1/raw/LJMTIntSpaChirho.zip), then:

```sh
python tool/prepare_spanish_glosses.py --source-archive /path/to/LJMTIntSpaChirho.zip
python tool/prepare_spanish_glosses.py --verify-only --source-archive /path/to/LJMTIntSpaChirho.zip
python -B tool/test_prepare_spanish_glosses.py --source-archive /path/to/LJMTIntSpaChirho.zip
```

The importer checks the archive and members, all 929 TAHOT chapters, the reference
snapshot, and correction originals. It reconstructs alignment from source,
without AI calls or an app checkout. The snapshot contains only SWORD reference
order and TAHOT selectors, not Bible text or runtime edition mappings. Its
historical edition/mapping hashes and exporter are retained for provenance.

After a reviewed change, update the data version in `pubspec.yaml` and
`tool/catalog.py`, run generation/tests, and explicitly reseal with:

```sh
python tool/catalog.py --write
python tool/catalog.py
```

Commit and publish the data repository before updating consumers. Prefer an
immutable commit or release archive URL, plus the printed catalog hash, in the
consumer lock. Until the initial commit exists, the app's bootstrap URL points
to `main`, but the catalog hash still rejects any changed content. Replace that
URL with the published commit's archive URL for durable historical builds.
The local `--source` workflow works before publication.

## License

Generation code is AGPL-3.0; see [LICENSE](LICENSE). Data keeps its original
component licensing and attribution, principally CC BY 4.0. See
[STEP notices](assets/interlinear/THIRD_PARTY_NOTICES.md), each dataset's
`attribution.json`, and the [Spanish notice](assets/interlinear_glosses/es-tahot/NOTICE.md).
The code license does not replace source-data licenses.
