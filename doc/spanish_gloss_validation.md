# Migration note

This review was performed during the original Flutter-app integration. The
correction records and chapter meanings are preserved in this data repository;
only generation ownership and reference-input packaging changed. Historical
app paths in the audit JSON describe that review, not current build dependencies.

# Spanish original-language gloss validation

Audit date: 2026-09-27. This is an **automated integrity/alignment audit plus an
AI-assisted linguistic spot check**, not a human translator's review. No dataset
was newly or completely human-validated by this work. “Verified” below names a
specific check; it does not mean that every translation is correct.

Following the initial audit, **99 explicitly identified Spanish glosses were
corrected with AI assistance at the user's request**. This includes repairing
and restoring all 49 mixed-star placeholders that were initially quarantined.
The original findings remain below as evidence; the correction section records
their final disposition. These corrections are not human validation.

## Status by dataset

| Dataset or layer | What is established | Linguistic review status |
| --- | --- | --- |
| STEPBible TAHOT original Hebrew/Aramaic, English meanings and morphology | Imported from pinned STEPBible data with source identities and provenance. The source describes Tyndale/STEP scholarly work and its textual/morphological sources. | Established attributed source; no new complete human review by this application. Do not label every meaning “fully validated.” |
| STEPBible TAGNT original Greek, English meanings and morphology | Imported from pinned STEPBible data under the selected reading profile. | Established attributed source; no new complete human review by this application. |
| STEPBible TAGNT Spanish meanings | The source header credits Marvel Bible Project/OpenGNT as of 2019-01-09 and says the material was expanded beyond words available in NA28. OpenGNT credits E. Barrientos and Proyecto GALEED for its Spanish literal translation. | Human-attributed upstream translation lineage. Neither that credit nor this audit certifies complete human checking of every current TAGNT Spanish field or expansion. |
| Love Jesus / Global Bible Tools Spanish OT meanings | Pinned licensed source; accepted Hebrew/Aramaic occurrences pass complete ordered-verse matching, resource binding and format checks. | **AI-assisted, provisional; upstream explicitly says not fully reviewed by human translators.** The limited AI spot check below does not change that status. |
| Edition-to-source correspondence | Hash-bound edition profiles, explicit reference policies and unavailable entries. | Technical correspondence evidence, not word-for-word alignment to the selected Spanish Bible and not linguistic certification of that Bible. |

The README reports technical validation and linguistic review in separate
columns. Correct file and occurrence binding does not establish correct translation.

The STEPBible header and README are available at the
[pinned source directory](https://github.com/STEPBible/STEPBible-Data/tree/b99716b0cddb648ddb95cc786a197180f2f97d48/Translators%20Amalgamated%20OT%2BNT)
and [pinned repository README](https://github.com/STEPBible/STEPBible-Data/blob/b99716b0cddb648ddb95cc786a197180f2f97d48/README.md).
See also [OpenGNT's Spanish credits](https://github.com/eliranwong/OpenGNT#other-credits).
The latter documents source lineage, not a retroactive review of our pinned STEP
snapshot. STEP is licensed CC BY 4.0; its existing attribution remains necessary.

## Candidate and reproducibility

The candidate is `LJMTIntSpaChirho` 1.0, published 2026-01-30, at repository commit
`79df943ef7ff280fe6d05c1e7419dcdb655c80b1`. The
[upstream warning](https://github.com/loveJesus/sword-modules-chirho/blob/79df943ef7ff280fe6d05c1e7419dcdb655c80b1/README.md)
identifies it as an AI-assisted study aid, not fully human-reviewed. Its
[module metadata](https://github.com/loveJesus/sword-modules-chirho/blob/79df943ef7ff280fe6d05c1e7419dcdb655c80b1/mods.d/ljmtintspachirho.conf)
declares CC BY 4.0. This audit does not replace that warning.

The [pinned archive](https://raw.githubusercontent.com/loveJesus/sword-modules-chirho/79df943ef7ff280fe6d05c1e7419dcdb655c80b1/raw/LJMTIntSpaChirho.zip)
has SHA-256
`c8844e1dc55c492bda9ae8141ab0df1eb52fac6ff7e92196e214da8068f2f5ff`.
It is joined to `step-tahot-lqr` 0.1.0, STEP revision
`b99716b0cddb648ddb95cc786a197180f2f97d48`, source manifest SHA-256
`37af75f19a83b06cd8fe59811bbae07a7c7d97666aef6e4e380626108f531c4c`.

The comparison uses the entire original token sequence at a resolved verse
reference, including occurrence order. It normalizes Unicode NFC, whitespace
and Unicode `Cf` formatting controls. A separate pe/samekh paragraph marker can
be reconciled only when it has the documented nonlexical source encoding and
the same exact letter is punctuation in TAHOT. Other letters, vowel points,
cantillation and punctuation remain significant. There is no Strong-only join,
fuzzy match, diacritic stripping or guessed partial-verse alignment. Uncertain
verses receive no imported Spanish.

The research comparison accepted 20,834 of 23,145 OT verse sequences, containing
270,141 of 305,486 selected source tokens. It refused 2,311 verse sequences.
Removing 98 empty/star glosses and 266 nonverbal strings left a draft of 269,777
glosses across 928 chapters. The 49 mixed-star placeholders found during this
audit were first quarantined, then explicitly repaired and restored. The final
correction set therefore retains **269,777 meanings, about 88.3% of source tokens**.
Chapter availability does not mean complete
Spanish coverage in that chapter. These counts include the original corpus's
Psalm headings where the complete sequence was accepted; an edition's heading
policy still controls whether those source entries are displayed.

The research verification checked the archive hash, bound source-manifest hash,
all 928 sidecar hashes, corresponding source chapter hashes and all 269,777 draft
occurrence identities. The app importer's final generated manifest and its
verification report are authoritative for the final corrected output counts.

## Full-draft format screening

All 269,777 draft strings were screened. This is a set of explicit heuristics,
not a general Spanish language detector or a semantic correctness test.

| Screen | Hits | Interpretation and action |
| --- | ---: | --- |
| Empty or no Unicode letters | 0 | Earlier import filters already removed these. |
| Mixed asterisk placeholders | 49 | Original draft findings: `Y–*`, `y–*`, `*-a-él`, `*-a-ellos` in Numbers 1, 3–6. All 49 source object-marker forms were inspected, then repaired through the explicit correction table and restored. The historical `spanish_gloss_quarantine.json` now records that repaired status, not current omissions. |
| Unicode control/format character | 1 | Original `TAHOT:Psa.48.11(48.12)#04`: `go\u00adcense`, containing U+00AD SOFT HYPHEN. Corrected explicitly to `gócense`, preserving the contextual plural exhortation and restoring its Spanish accent. |
| Obvious HTML/XML delimiters or escaped entities | 0 | Does not rule out every possible markup convention. |
| Replacement character or selected common UTF-8 mojibake patterns | 0 | Only the explicit patterns in the JSON audit were checked. |
| Newline or tab | 0 | — |
| Selected unambiguous English function words | 0 | Does not detect all English vocabulary or Hebrew transliterations. |
| Hebrew, Greek or Cyrillic characters in Spanish strings | 0 | Latin-script Hebrew transliterations remain possible. |
| Over 100 characters | 0 | — |
| Unequal counts of parentheses, brackets or braces | 0 | Does not test cross-token punctuation or grammatical correctness. |

The initial placeholder experiment treated case-insensitive `TODO` as a marker;
that was rejected because Spanish `todo` is a normal word. The final screen
does not classify ordinary `todo`/`Todo` as a defect. No glossary wording was
silently rewritten by this audit.

The table above reports the original draft. The final corrections remove all 49
mixed-star strings and the one soft hyphen. Other identified accent and wording
corrections are semantic/orthographic findings, not additional hits from these
format-only screening rules.

## Bounded linguistic spot check

A fixed, purposive list was selected before reading its glosses: 29 verses and
one Psalm heading spanning Torah, narrative/history, poetry, major and minor
prophets, and two Aramaic passages. It is deterministic, not a random sample.
It supports no numerical accuracy estimate. Twenty-eight units supplied 380
Spanish glosses; two complete verses were correctly absent, leaving 401 source
tokens in the full selection. The 380 available meanings were read against
their Hebrew/Aramaic surfaces, source morphological segmentation, the STEP
English context, and passage context. This review was performed by an AI
assistant; **zero human translator reviews were performed**.

The following sample table records **original candidate wording before local
corrections**. Raw strings remain in the companion JSON alongside an added
`correctedEs` value where applicable; they are not claims that the shipped
sidecar still contains every listed defect.

Morphological observations use the recorded STEP codes. The source says these
adapt the [OpenScriptures morphology conventions](https://hb.openscriptures.org/parsing/HebrewMorphologyCodes.html).
For example, Deuteronomy 2:1's first-person plural narrative verbs correspond to
`nos–volvimos`, `partimos` and `rodeamos`; its directional suffix is reflected in
`al–desierto`. Ezra 4:24 and Daniel 2:20 are marked `arc` by the source and were
checked as Aramaic. These examples do not prove every tense or construction is
rendered correctly throughout the corpus.

| Reference | Spanish/source tokens | AI-assisted observation; no human approval implied |
| --- | ---: | --- |
| Genesis 1:4 | 12/12 | Seeing/separating light and darkness are plausible. `'Elohim` is a transliteration rather than `Dios`; `(a)–` represents an object marker. |
| Genesis 12:3 | 9/9 | Bless/curse contrast and second-person suffixes are plausible; `familias–de` fits the family/clan context. |
| Exodus 3:14 | 15/15 | Remaining narration is plausible, but three `Ehyeh` entries transliterate a first-person Hebrew verb instead of explaining its meaning in Spanish. Names also use `Mosheh` and `Yisrael`. Retain as an explicit upstream limitation, not a fully translated Spanish explanation. |
| Leviticus 19:18 | 12/12 | Prohibitions, neighbor and self comparison are plausible; `guardarás–rencor` supplies contextual sense. |
| Numbers 6:24 | 3/3 | Blessing/wish readings and second-person object suffixes are plausible. Final paragraph marker is punctuation, not a fourth word. |
| Deuteronomy 2:1 | 16/16 | First-person plural journey verbs and directional phrase fit. `Rojo` belongs to the conventional Spanish sea-name phrase; it is not the standalone dictionary meaning of `סוף`, glossed “reed[s]” by STEP. |
| Deuteronomy 6:4 | 6/6 | Hear/Israel/our God/one readings are plausible. This does not settle theological or syntactic interpretation. |
| Joshua 1:9 | 15/15 | Commands, negations and accompanying-presence clause are plausible. |
| Judges 6:12 | 0/10 | Whole verse refused: candidate has an additional dagesh in source word 3. No partial glosses were guessed. |
| Ruth 1:16 | 20/20 | Plausible agency, travel/lodging and possessive contrasts; independently compared with the credited Door43 Spanish text below. |
| Ruth 2:12 | 15/15 | Reward/refuge/wing imagery agrees in sense with the independent Spanish reference; `de–con` is awkward literal phrasing. |
| 1 Samuel 16:7 | 25/25 | Rejection and outward appearance/heart contrast are plausible; `Shemuel` is a name transliteration. |
| 2 Samuel 7:16 | 11/11 | Original `Y–será–fiel` weakens the contextual establishment/persistence sense identified by STEP. The explicit correction is now `Y–quedará–firme`; further human review remains outstanding. |
| 1 Kings 8:27 | 18/18 | Dwelling/containment contrast is recognizable. The separately glossed `cuánto–menos` and `porque` show why concatenating token glosses is not a fluent translation. |
| Ezra 4:24 | 16/16 | Aramaic cessation of work and regnal date are recognizable. `y–fue cesada` is awkward Spanish; this is not a grammatical Spanish sentence rendering. |
| Esther 4:14 | 23/23 | Deliverance, peril and royal-position context agree with the independent Spanish reference. `callar callares` exposes literal treatment of the emphatic construction. |
| Job 19:25 | 8/8 | Vindicator/redeemer, life and standing-on-dust vocabulary are plausible; `Redentor` capitalization is interpretive style. |
| Psalm 3 heading | 6/6 | Psalm, David, flight from Absalom and son suffix align plausibly. It remains a heading, not a new numbered verse. |
| Psalm 23:1, including source heading | 6/6 | Shepherd/possessive/lack sense is plausible; two tokens belong to the heading. |
| Psalm 51:10 | 9/9 | Creation/renewal/purity/interior sense is plausible; `en–mí` is contextual rather than a literal explanation of every Hebrew preposition. |
| Proverbs 3:5 | 9/9 | Trust/heart/understanding/negative command are plausible; divine name is `YHWH`, unlike `Yahweh` elsewhere. |
| Ecclesiastes 3:1 | 7/7 | Time/purpose vocabulary is plausible, with awkward `Para–el–todo`. |
| Song of Songs 2:4 | 7/7 | Bringing, wine-house, banner and love vocabulary are plausible. |
| Isaiah 53:5 | 0/11 | Whole verse refused: retained Hebrew point differs in source word 5 (holam versus holam haser for vav). Matching does not erase this distinction. |
| Jeremiah 31:31 | 14/14 | New-covenant vocabulary is recognizable; `y–cortaré ... pacto` is Hebrew idiom rendered literally and needs contextual explanation. |
| Ezekiel 36:26 | 17/17 | New heart/spirit, stone/flesh contrast and plural addressees are plausible; `(marca–de–objeto)` is a grammatical aid, not prose. |
| Daniel 2:20 | 18/18 | Aramaic blessing, eternity, wisdom and power are recognizable. `el–nombre–de` followed by `de` duplicates phrase linkage if concatenated; whole-token glosses do not independently explain every morpheme. |
| Jonah 2:2 | 12/12 | Sense agrees with the independent Spanish reference, but upstream has `clame`, `y–me–respondio`, `pedi–auxilio`, `oiste`, and `de–mi` without expected accents. Raw source wording is preserved and flagged. |
| Jonah 4:2 | 32/32 | Prayer, fleeing and compassion/relenting sense agrees with the independent reference. `Y–oro`, `me–adelante`, `tu` have accent issues; phrasing remains literal. |
| Micah 6:8 | 19/19 | Justice, mercy and walking/humility vocabulary are recognizable. Adjacent `sino` / `si–no` looks awkward and needs translator review at phrase level; no silent rewrite. |

These findings justify provisional study use with provenance and fallback. They
do **not** justify “all meanings are correct,” “fully human-reviewed,” or “exact
RVA word alignment.” The bounded corrections below address supported defects;
they do not rewrite all literal phrasing or settle debatable readings throughout
the corpus. Word-by-word glosses need not concatenate into a fluent sentence.

## Explicit AI-assisted corrections

The authoritative, machine-readable list is
[`tool/spanish_gloss_corrections.json`](../tool/spanish_gloss_corrections.json).
It records **99 exact occurrence IDs**, each with `original`, `corrected`,
`reason` and source evidence (Hebrew/Aramaic surface, English contextual gloss,
morphology, and a contextual explanation). The importer applies a correction
only after full ordered-verse alignment succeeds and its exact original raw
Spanish value matches. It rejects duplicate, unknown, unmatched and unused
correction entries. There are no global string replacements.

| Correction category | Occurrences | Scope |
| --- | ---: | --- |
| Incomplete placeholder repair | 49 | Conjunctions and object pronouns in the individually inspected Numbers contexts. |
| Orthography | 33 | Accents, the Psalm soft hyphen, and the malformed `escarlatain` color word. |
| Contextual wording | 13 | The explicitly inspected Ruth, 2 Samuel, 1 Kings, Ezra, Esther, Ecclesiastes, Jeremiah, Daniel and Micah constructions. |
| Explanatory meaning | 3 | Three Exodus 3:14 `Ehyeh` occurrences, preserving alternatives. |
| Function-marker correction | 1 | Joshua 1:8's pure Hebrew object marker incorrectly glossed `tu`. |

The 49 repaired placeholders retain meaningful grammatical content. For
example, `TAHOT:Num.1.3#10` changes `*-a-ellos` to `a–ellos`, referring to the
men being counted. Conjunction-plus-marker forms become `y` or `Y`, with
Spanish personal `a` only in the three inspected personal-object contexts.
Pronominal forms use the actual referent: the tribe is `la`, the tabernacle is
`lo`, and utensils are `los`. Hebrew and Spanish noun gender can differ: Numbers
4:10's Hebrew feminine pronoun refers to the source Spanish masculine
`candelero`, so its contextual Spanish object is `lo`. Pure object markers are
grammatical aids, not invented Spanish content words.

The accent review inspected every occurrence of the same suspicious raw
strings found in the sample. Twenty `tu` entries were independent Hebrew
personal pronouns (`HPp2ms`), so they become `tú`. The remaining raw `tu` at
Joshua 1:8 was actually `HTo`, so it becomes `[objeto]` instead. Three `oiste`
entries become `oíste`; both inspected `Y–oro` narrative-prayer entries become
`Y–oró`. **Deuteronomy 24:15's `clame` remains unchanged**: its subjunctive sense
fits the warning clause, whereas Jonah 2:2's first-person completed action
requires `clamé`. This is why raw-string equality alone is insufficient. The
[RAE accent rules](https://www.rae.es/dpd/tilde) support the written-accent and
personal/possessive distinctions; Hebrew morphology and context determine which
Spanish form is intended.

Selected wording changes include `de–con` → `de–parte–de` in Ruth 2:12,
`y–fue cesada` → `y–permaneció suspendida` across Ezra 4:24's two source words,
and `y–cortaré` → `y–estableceré` in Jeremiah's covenant-making expression.
These address the contextual sense, not a demand for fluent concatenation.
Esther 4:14 retains the infinitive absolute's emphasis through `por–completo`
with `callas`; Daniel 2:20 becomes `su–nombre` to represent its actual possessive
suffix, even though the following source words also identify the possessor.
The two-word constructions in 1 Kings 8:27 and Micah 6:8 are explicitly paired
as `cuánto` / `menos` and `más` / `que`, rather than treating a phrase-dependent
conjunction as an independent causal or conditional word. The corresponding
[NET 1 Kings text](https://classic.net.bible.org/verse.php?book=1Ki&chapter=8&verse=27)
and [Micah translation note](https://classic.net.bible.org/verse.php?book=Mic&chapter=6&verse=8)
provide independent support for these constructions. The
[2 Samuel text](https://classic.net.bible.org/verse.php?book=2Sa&chapter=7&verse=16)
also supports the permanence/establishment sense retained by `quedará–firme`.

For Exodus 3:14, all three bare `Ehyeh` transliterations become
`Yo–soy / Yo–seré`. This explicitly lists present/future interpretive alternatives
of the first-person Hebrew form; it does not assert both as simultaneous
predicates or settle the passage's theology. The
[NET translation note](https://classic.net.bible.org/passage.php?passage=ex+3%3A14)
discusses those alternatives. Other names and divine-name transliterations are
not globally rewritten.

All corrections remain **AI-assisted and not human-reviewed**. The original
provider archive is unchanged, and its raw wording is preserved in the
correction log. Neither the corrected subset nor the remaining corpus is
certified linguistically complete or error-free.

Final cross-checks compared all 99 correction records with the actual bound
corpus: exact source surface, language, English gloss, and complete segment and
morphology evidence matched. A separate AI-assisted check reviewed the 17
contextual/explanatory/function-marker corrections plus selected placeholder
cases and found no concrete conflicting correction. This is an additional AI
check, not human translation review. The importer also verified the full pinned
source and rejection cases for invalid corrections. An independent read-only
simulation matched every original value, retained 269,777 corrected meanings,
and found no remaining asterisk strings or Unicode control/format characters
in that corrected draft. Twenty-four of the original 380 sampled meanings have
an explicit local correction; the sample is still not an accuracy estimate.

## Independent Spanish comparison

Five sampled verses were compared with *Texto Puente Literal* (TPL), Fundación
Idiomas Puentes / Door43 World Missions Community, v41, pinned at commit
`3f9bf7e8806f2e310601d723eb201334fe3be1ab`. Its
[manifest](https://git.door43.org/es-419_gl/es-419_glt/src/commit/3f9bf7e8806f2e310601d723eb201334fe3be1ab/manifest.yaml)
names Idiomas Puentes as checking entity and records checking level 3. This is
upstream review metadata, not a fresh inspection of its review history by us.
The manifest lists English ULT v39 as its translation source and UHB/UGNT
relations; do not describe it as a newly commissioned direct Hebrew-to-Spanish
review. Its [license](https://git.door43.org/es-419_gl/es-419_glt/src/commit/3f9bf7e8806f2e310601d723eb201334fe3be1ab/LICENSE.md)
is CC BY-SA 4.0, copyright 2022 Fundación Idiomas Puentes. These independent
reference excerpts are for comparison only; they are not replacement app glosses.

| TPL passage and primary source | Evidence compared |
| --- | --- |
| [Ruth 1:16 and 2:12](https://git.door43.org/es-419_gl/es-419_glt/src/commit/3f9bf7e8806f2e310601d723eb201334fe3be1ab/08-RUT.usfm) | “No me presiones a abandonarte” agrees with the candidate's refusal-to-leave sense; “bajo cuyas alas tú has venido por refugio” agrees with its refuge/wing imagery. |
| [Esther 4:14](https://git.door43.org/es-419_gl/es-419_glt/src/commit/3f9bf7e8806f2e310601d723eb201334fe3be1ab/17-EST.usfm) | “alivio y liberación” and “has llegado a la realeza” support the broad sense; TPL expresses the emphatic silence clause naturally rather than copying the candidate's literal doubled verb. |
| [Jonah 2:2 and 4:2](https://git.door43.org/es-419_gl/es-419_glt/src/commit/3f9bf7e8806f2e310601d723eb201334fe3be1ab/32-JON.usfm) | “Clamé”, “me respondió”, and “él oró” confirm the intended past-tense readings and demonstrate the candidate's missing accents. The same broad prayer/compassion context is present. |

The exact downloaded comparator hashes and source URLs are in the companion
JSON. USFM word spans were read in their recorded order; markup was removed
for comparison, and verse punctuation was not reconstructed. No statistical
independence is asserted: both resources may draw on shared traditional
translation choices. Agreement of five verses is a useful cross-check, not
proof of the remaining corpus.

## Remaining work and machine-readable evidence

`spanish_gloss_validation.json` contains all sampled raw Spanish strings, source
surfaces, English glosses, morphological segments, screen definitions and hits,
source/comparator hashes, and these audit observations. It intentionally records
the original draft, so defects remain visible as evidence, with local corrected
values recorded separately. The historically named
`spanish_gloss_quarantine.json` enumerates the 49 placeholder findings by exact
occurrence ID, their source object-marker evidence and their corrected values;
its status now states that they were **repaired and restored**, with zero of
those 49 still quarantined.

A qualified Hebrew/Aramaic-to-Spanish translator would still need to review
wording and difficult constructions, establish an editorial policy for names,
idioms and object markers, and check the whole corpus before any complete human
validation claim. Runtime integrity checks and this AI-assisted audit cannot
provide that certification.
