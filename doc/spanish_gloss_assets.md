# Provisional Spanish Old Testament study meanings

This data repository supplies 269,777 Spanish contextual meanings in 928 chapter sidecars
under `assets/interlinear_glosses/es-tahot/`. They are a separate layer attached
to existing TAHOT word occurrences. The original Hebrew/Aramaic corpus, its
English meanings, verse mappings, and original bundle remain unchanged.

**All included word alignments and asset hashes pass technical validation.
The Spanish wording has not received complete human linguistic validation.**
The provider describes its material as AI-assisted machine translation that has
not been fully reviewed by human translators. This layer is installed with
`status: provisional`; it is a study aid, not an authoritative translation.
The app retains an explicit English fallback wherever Spanish is unavailable.

## Source, attribution, and review status

The source is Love Jesus / Global Bible Tools, SWORD module
`LJMTIntSpaChirho` version 1.0, pinned to commit
`79df943ef7ff280fe6d05c1e7419dcdb655c80b1` of
[sword-modules-chirho](https://github.com/loveJesus/sword-modules-chirho/tree/79df943ef7ff280fe6d05c1e7419dcdb655c80b1).
The [pinned module configuration](https://github.com/loveJesus/sword-modules-chirho/blob/79df943ef7ff280fe6d05c1e7419dcdb655c80b1/mods.d/ljmtintspachirho.conf)
declares CC BY 4.0; the
[pinned README](https://github.com/loveJesus/sword-modules-chirho/blob/79df943ef7ff280fe6d05c1e7419dcdb655c80b1/README.md)
states the review limitation. The generated asset root preserves the original
module configuration, an attribution and modification notice, source links,
license links, provenance, limitations, and technical validation results.

The [local review](spanish_gloss_validation.md) documents sample checks and a
corpus-wide screen. It is not a substitute for full review by people qualified
in Biblical Hebrew/Aramaic and Spanish. Provider spellings such as `'Elohim`
and other uncorrected literal phrasing are preserved. Changes are limited to exact
occurrences listed in the separate correction table. The local corrections
are also AI-assisted and have not received human linguistic review. These
meanings are not copied from the selected RVA translation, and they do not
provide Spanish dictionary definitions or per-morpheme translations. Spanish
New Testament meanings continue to come from TAGNT's existing Spanish fields.

## Reproduce and verify

Python 3.10 or later and the standard library are sufficient. Download the
[pinned archive](https://raw.githubusercontent.com/loveJesus/sword-modules-chirho/79df943ef7ff280fe6d05c1e7419dcdb655c80b1/raw/LJMTIntSpaChirho.zip)
separately, then run these commands from the data repository root:

```sh
python tool/prepare_spanish_glosses.py --source-archive /path/to/LJMTIntSpaChirho.zip
python tool/prepare_spanish_glosses.py --verify-only --source-archive /path/to/LJMTIntSpaChirho.zip
python -B tool/test_prepare_spanish_glosses.py --source-archive /path/to/LJMTIntSpaChirho.zip
```

`--data-root /path/to/data` is optional; it defaults to the repository containing the
tool, independently of the current working directory. The importer itself
does not use the network, install SWORD, or depend on research directories.
Both modes require the explicit source archive: verification reconstructs
the original-word alignment, rather than trusting an existing validation
report or hashes alone.

The regression command also exercises incorrect correction originals,
duplicate/unknown/unmatched correction identities, modified output, extra files,
an unpinned archive, repeated byte-identical generation, and rollback after a
simulated manifest-constant promotion failure. Its temporary copies are separate
from the installed assets.

The archive SHA-256 is
`c8844e1dc55c492bda9ae8141ab0df1eb52fac6ff7e92196e214da8068f2f5ff`.
The importer also pins individual module members, the exported reference-order snapshot and the TAHOT manifest. The snapshot
records the exact historical KJV edition and mapping hashes. The TAHOT manifest SHA-256 is
`37af75f19a83b06cd8fe59811bbae07a7c7d97666aef6e4e380626108f531c4c`;
its dataset is `step-tahot-lqr` revision `0.1.0`, profile `L+Q+R`, reading policy
`qere`, source revision `b99716b0cddb648ddb95cc786a197180f2f97d48`, and reference
system `STEPBible-NRSV`. Every one of its 929 decompressed chapter hashes is
checked before source occurrences are used.

Generation builds and verifies a replacement in a sibling staging directory
before promoting it. It also writes the corresponding pinned manifest hash to
`metadata/spanish-manifest.sha256`. A failure during preparation leaves the
installed output intact; a promotion error attempts rollback and preserves
recovery data if rollback itself fails. Existing output must identify the same
Spanish module before the tool replaces it. Unrecognized output is refused.

Serialization uses UTF-8 JSON and LF. Gzip uses compression level 9, zero mtime,
no filename, and OS byte 255. Output includes no timestamps or absolute paths.
The generator source digest is recorded with LF normalization, so a deliberate
importer edit requires regeneration. Repeated builds with the same generator
and inputs produce byte-identical assets and manifest constants when using the
same compression implementation and version. Different zlib implementations
(including zlib-ng) can produce different gzip bytes for identical JSON.
Verification compares decompressed chapter bytes exactly against source-derived
output and checks each installed gzip file's hash and size against the installed
manifest. Only the regenerated manifest's compressed hashes and sizes may differ;
all other metadata must match. The catalog still pins every installed byte.
The exact
normalized-LF bytes of `tool/spanish_gloss_corrections.json` are also fingerprinted
and copied into the installed `corrections.json` resource.

## Alignment rules and exclusions

The SWORD module indexes words by KJV passage references. The pinned reference-order snapshot exported from the historical
KJV correspondence table resolves those passages to original TAHOT occurrences;
the same resulting occurrence meanings can then serve other mapped editions.
It does not align words from the selected Spanish translation.

For each of the 23,145 candidate OT verses, the importer compares the entire
ordered original-word sequence. It accepts a verse only if every surface
matches after these narrowly defined structural rules:

1. Normalize Unicode to NFC and ignore whitespace and Unicode `Cf` format
   controls. Hebrew letters, vowel marks, cantillation, and other punctuation
   remain significant.
2. A separately encoded `פ` or `ס` paragraph marker may be appended to the
   preceding candidate token for comparison only when its lexical value is
   `strong:H????` and its morphology is empty. The identical marker must occur
   in the corresponding TAHOT surface and be explicitly classified as a
   punctuation segment. Its candidate gloss contributes no meaning.
3. Refuse the whole verse if any remaining token count, order, spelling,
   punctuation, reading, or boundary differs. Strong numbers are never a join
   key or fallback.

Psalm headings are accepted only when the full ordered source sequence agrees;
their native special-entry occurrence identities are retained. Accepted meanings
are keyed by actual corpus occurrence IDs, not by parsing or guessing IDs from
the selected translation's numbering.

| Check | Result |
| --- | ---: |
| Candidate OT verses | 23,145 |
| Complete source sequences accepted | 20,834 |
| Complete verse sequences refused | 2,311 |
| Original source tokens covered by correspondence | 305,486 |
| Tokens in accepted sequences | 270,141 |
| Empty or sole-asterisk glosses omitted | 98 |
| Nonverbal glosses omitted | 266 |
| Mixed-asterisk incomplete glosses explicitly corrected | 49 |
| Mixed-asterisk glosses remaining/omitted | 0 |
| Spanish meanings installed | 269,777 |
| Original corpus chapters hash-checked | 929 |
| Chapters with at least one installed meaning | 928 |

The correction table contains 99 explicit occurrence entries: 49 placeholder
repairs, 33 orthographic corrections, one object-marker correction, three
explanatory alternatives for Ehyeh, and 13 contextual wording corrections.
Its normalized-LF SHA-256 is
`7849577d0922fef881ddf9ab2d8d6fbcda7047fe21fe34e96d9d90977677eb2e`.

The 49 mixed-asterisk values, such as `Y–*` and `*-a-él`, were initially identified
for omission in the [audit record](spanish_gloss_quarantine.json). They now have
explicit occurrence-specific repairs in `tool/spanish_gloss_corrections.json`,
along with documented accent and wording corrections. Every record preserves
the original string, corrected string, reason, and evidence. These are
AI-assisted corrections, not a claim of human translation review.

The importer applies corrections only after the entire source sequence has
matched, and before checking for placeholders. It verifies the original string
exactly, rejects duplicate correction IDs, and requires every correction to
identify an occurrence in a matched verse. An unknown occurrence, unmatched
verse, or unexpected raw wording fails the build. No global string replacement
or lexical-number substitution is used. Any remaining asterisk-containing
placeholder would still be omitted. `GEN.2.10` is an example of a fully refused
verse; `GEN.1.4` has all 12 source-word meanings. Other incomplete or absent
coverage continues to use fallback.

The committed asset root contains 933 files totaling 2,579,033 bytes,
including 928 compressed chapters and the manifest, validation report, correction
table, attribution notice, and original module configuration.

## Runtime asset contract

`manifest.json` schema 1 declares the provisional status, provenance, full
`boundDataset` identity, exact corpus-manifest digest, correspondence inputs,
coverage, generator identity, and resource hashes. The app pins its bytes using
`spanishGlossManifestSha256` and resolves its root using
`spanishGlossAssetsRoot`.

Each `chapterResources` entry contains `book`, `chapter`, `tokens`, and a path
such as `chapters/GEN.1.json.gz`. `sha256` is the digest of the **decompressed**
JSON bytes; `compressedSha256` and `bytes` describe the compressed transport.
Each chapter payload has this shape:

```json
{
  "schemaVersion": 1,
  "book": "GEN",
  "chapter": 1,
  "language": "es",
  "sourceChapterSha256": "digest from the original corpus manifest",
  "glosses": {"TAHOT:Gen.1.1#01": "En–principio"}
}
```

The separate asset root also contains `NOTICE.md`, the original
`source-module.conf`, the full `corrections.json` provenance table, and
`validation.json`. The latter records refused verse references, placeholder
omissions, applied correction IDs, a digest of accepted verse references,
coverage, and the distinction between technical and linguistic validation.
The original interlinear bundle's strict inventory is unaffected.

## Validation performed

The final build was checked by full offline source reconstruction and every
installed occurrence was checked against its actual original chapter. Every
installed gloss also agreed with the independently prepared research extraction
after applying only the documented occurrence corrections. Repeated source-derived
builds were byte-identical. Deliberately changed gloss content, undeclared files,
an unpinned source archive, an incorrect correction original, and an unknown
correction occurrence were rejected. Every pre-existing corpus, mapping,
and bundle file remained byte-identical to the baseline.

These checks establish reproducibility, input identity, exact included source
alignment, and asset integrity. They do not establish that every Spanish meaning
is linguistically correct or fully human reviewed.
