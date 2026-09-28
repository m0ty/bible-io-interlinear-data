import 'dart:convert';
import 'dart:io';

import 'package:bible_io/bible_io.dart';
import 'package:bible_io_interlinear/bible_io_interlinear.dart';
import 'package:bible_io_interlinear/stepbible.dart';

const _revision = 'b99716b0cddb648ddb95cc786a197180f2f97d48';
const _generator = 'bibleio-full-interlinear-assets-v1';
const _codec = InterlinearJsonCodec();

/// Explicit offline development operation; never called by application startup.
///
/// dart run tool/generate_interlinear_assets.dart [--package-root DIRECTORY]
///   [--source-root DIRECTORY] [--lock FILE] [--output DIRECTORY] [--overwrite]
///
/// Inputs must be all six complete upstream files matching the source lock.
/// Output chapters use deterministic gzip transport. The package manifest paths
/// and SHA-256 hashes still describe the decompressed chapter JSON.
Future<void> main(List<String> arguments) async {
  Directory? staging;
  try {
    final options = _options(arguments);
    if (options.containsKey('help')) {
      stdout.writeln(
          'Generate full offline STEPBible assets from pinned sources.\n'
          '--package-root  Companion package directory (default ../bible-io-interlinear-dart)\n'
          '--source-root   Directory containing the six raw source files\n'
          '--lock          Source lock JSON (default PACKAGE/tool/sources.lock.json)\n'
          '--output        Asset directory (default assets/interlinear)\n'
          '--overwrite     Replace a previous generated asset directory; retain a backup');
      return;
    }
    final packageRoot =
        options['package-root'] ?? '../bible-io-interlinear-dart';
    final sourceRoot =
        Directory(options['source-root'] ?? '$packageRoot/.work/sources');
    final lockFile =
        File(options['lock'] ?? '$packageRoot/tool/sources.lock.json');
    final output =
        Directory(options['output'] ?? 'assets/interlinear').absolute;
    final lockBytes = await lockFile.readAsBytes();
    final lock = jsonDecode(utf8.decode(lockBytes)) as Map<String, dynamic>;
    if (lock['lockVersion'] != 1 ||
        lock['revision'] != _revision ||
        lock['repository'] != 'https://github.com/STEPBible/STEPBible-Data') {
      throw const FormatException('Expected the supported pinned source lock.');
    }
    final entries = (lock['files'] as List).cast<Map<String, dynamic>>();
    if (entries.length != 6 ||
        entries.map((e) => e['localPath']).toSet().length != 6) {
      throw const FormatException(
          'All six distinct complete source files are required.');
    }
    final outputType =
        await FileSystemEntity.type(output.path, followLinks: false);
    if (outputType != FileSystemEntityType.notFound) {
      if (outputType != FileSystemEntityType.directory ||
          !options.containsKey('overwrite')) {
        throw const FileSystemException(
            'Output exists; choose a new directory or --overwrite.');
      }
      final oldIndex = jsonDecode(
          await File('${output.path}/asset-index.json').readAsString());
      if (oldIndex is! Map || oldIndex['generator'] != _generator) {
        throw const FormatException(
            'Refusing to replace a directory not created by this generator.');
      }
    }
    // Check the entire acquisition set before beginning an import.
    for (final entry in entries) {
      final name = entry['localPath'] as String;
      if (name.isEmpty ||
          name.contains(RegExp(r'[/\\:\x00-\x1f]')) ||
          name == '.' ||
          name == '..') {
        throw const FormatException('Unsafe local source filename in lock.');
      }
      final file = File('${sourceRoot.path}/$name');
      final bytes = await file.readAsBytes();
      if (bytes.length != entry['bytes'] ||
          resourceSha256(bytes) != entry['sha256']) {
        throw FormatException(
            'Source file does not match the pinned bytes: $name');
      }
    }
    await output.parent.create(recursive: true);
    staging = await output.parent.createTemp('.interlinear-assets-');
    final datasetSummaries = <Map<String, Object?>>[];
    final transportResources = <Map<String, Object?>>[];
    final notices =
        await File('$packageRoot/THIRD_PARTY_NOTICES.md').readAsBytes();
    final reports = <String, Object?>{};
    for (final type in [StepSourceType.tahot, StepSourceType.tagnt]) {
      final greek = type == StepSourceType.tagnt;
      final datasetId = greek ? 'step-tagnt-n' : 'step-tahot-lqr';
      final sourceEntries = entries
          .where((entry) => entry['type'] == type.name.toUpperCase())
          .toList();
      if (sourceEntries.length != (greek ? 2 : 4)) {
        throw FormatException('Wrong number of ${type.name} source files.');
      }
      final sources = <StepSource>[];
      final inputDetails = <Map<String, Object?>>[];
      final sourceLabels = <String>{};
      for (final entry in sourceEntries) {
        final bytes = await File('${sourceRoot.path}/${entry['localPath']}')
            .readAsBytes();
        final source = StepSource.fromBytes(
            bytes: bytes, sourceFile: entry['localPath'] as String);
        sources.add(source);
        inputDetails.add({
          ...entry,
          'decodedTextSha256': resourceSha256(utf8.encode(source.text)),
          'hadUtf8Bom': bytes.length >= 3 &&
              bytes[0] == 0xef &&
              bytes[1] == 0xbb &&
              bytes[2] == 0xbf,
          'headerNotices': _header(source.text),
        });
        sourceLabels.addAll(_sourceLabels(source.text));
      }
      stdout.writeln(
          'Importing all ${type.name.toUpperCase()} inputs for $datasetId...');
      final imported = StepImporter().importSources(
        sources: sources,
        config: StepImportConfig(
          sourceType: type,
          datasetId: datasetId,
          datasetRevision: '0.1.0',
          sourceRevision: _revision,
          profile: greek ? 'N' : 'L+Q+R',
          readingPolicy: greek ? null : 'qere',
        ),
      );
      final prepared = PreparedInterlinearDataset.build(
        metadata: imported.metadata,
        chapters: imported.chapters,
      );
      final selectedLabels = <String>{};
      final emptyVerses = <String>[];
      var verseCount = 0;
      var specialCount = 0;
      var rawChapterBytes = 0;
      var gzipChapterBytes = 0;
      var plainBytes = 0;
      for (final chapter in imported.chapters) {
        for (final verse in chapter.verses) {
          final key =
              '${chapter.book.usfmIdentifier}.${chapter.chapter}.${verse.label.source}';
          selectedLabels.add(key);
          verseCount++;
          if (verse.tokens.isEmpty) emptyVerses.add(key);
        }
        for (final special in chapter.specialEntries) {
          selectedLabels.addAll(_sourceLabels('${special.sourceLabel}#00=L\t'));
          specialCount++;
        }
      }
      final paths = prepared.resources.keys.toList()..sort();
      for (final path in paths) {
        validateResourcePath(path);
        final raw = prepared.resources[path]!;
        final isChapter = path.startsWith('chapters/');
        final transportPath = isChapter ? '$path.gz' : path;
        final encoded = isChapter ? _gzip(raw) : raw;
        if (isChapter) {
          rawChapterBytes += raw.length;
          gzipChapterBytes += encoded.length;
          if (resourceSha256(gzip.decode(encoded)) != resourceSha256(raw)) {
            throw FormatException('gzip round-trip failed: $datasetId/$path');
          }
        } else {
          plainBytes += raw.length;
        }
        final file = File('${staging.path}/$datasetId/$transportPath');
        await file.parent.create(recursive: true);
        await file.writeAsBytes(encoded);
        transportResources.add({
          'datasetId': datasetId,
          'logicalPath': path,
          'assetPath': '$datasetId/$transportPath',
          'encoding': isChapter ? 'gzip' : 'identity',
          'uncompressedBytes': raw.length,
          'uncompressedSha256': resourceSha256(raw),
          'transportBytes': encoded.length,
          'transportSha256': resourceSha256(encoded),
        });
      }
      // Verify on-disk transport through the normal strict package reader.
      final source = JsonInterlinearDataSource(reader: (path) async {
        final compressed = path.startsWith('chapters/');
        final bytes = await File(
                '${staging!.path}/$datasetId/$path${compressed ? '.gz' : ''}')
            .readAsBytes();
        return compressed ? gzip.decode(bytes) : bytes;
      });
      final manifest = await source.loadManifest();
      final occurrenceIds = <String>{};
      var validatedTokens = 0;
      for (final resource in manifest.chapters) {
        final chapter =
            await source.loadChapter(resource.book, resource.chapter);
        for (final token in [
          ...chapter.verses.expand((verse) => verse.tokens),
          ...chapter.specialEntries.expand((entry) => entry.tokens),
        ]) {
          if (!occurrenceIds.add(token.occurrenceId)) {
            throw FormatException(
                'Duplicate occurrence ID: ${token.occurrenceId}');
          }
          validatedTokens++;
        }
      }
      if (validatedTokens != imported.report.tokenCount) {
        throw const FormatException(
            'On-disk transport token count differs from import.');
      }
      final profileGaps = sourceLabels.difference(selectedLabels).toList()
        ..sort();
      final summary = <String, Object?>{
        'datasetId': datasetId,
        'datasetRevision': '0.1.0',
        'assetRoot': datasetId,
        'manifestPath': '$datasetId/manifest.json',
        'manifestSha256': resourceSha256(prepared.resources['manifest.json']!),
        'profile': imported.metadata.profile,
        'readingPolicy': imported.metadata.readingPolicy,
        'referenceSystem': imported.metadata.referenceSystem,
        'books': imported.metadata.coverage.keys
            .map((book) => book.usfmIdentifier)
            .toList()
          ..sort(),
        'chapterCount': imported.chapters.length,
        'ordinaryVerseCount': verseCount,
        'specialEntryCount': specialCount,
        'tokenCount': validatedTokens,
        'emptyVerseEntries': emptyVerses..sort(),
        'sourceEntriesWithoutSelectedTokens': profileGaps,
        'uncompressedChapterBytes': rawChapterBytes,
        'compressedChapterBytes': gzipChapterBytes,
        'plainMetadataBytes': plainBytes,
        'originalLanguages': imported.metadata.originalLanguages,
        'glossLanguages': imported.metadata.glossLanguages,
      };
      datasetSummaries.add(summary);
      reports[datasetId] = {
        'inputs': inputDetails,
        'importReport': imported.report.toJson(),
        'summary': summary
      };
      stdout.writeln(
          '$datasetId: ${imported.chapters.length} chapters, $validatedTokens tokens, '
          '$gzipChapterBytes gzip bytes from $rawChapterBytes chapter JSON bytes; '
          '${profileGaps.length} source entries have no selected tokens.');
    }
    final generatorBytes = await File.fromUri(Platform.script).readAsBytes();
    final index = <String, Object?>{
      'schemaVersion': 1,
      'generator': _generator,
      'sourceRevision': _revision,
      'transport': 'gzip-per-chapter',
      'datasets': datasetSummaries,
      'bookCount': datasetSummaries.fold<int>(
          0, (sum, dataset) => sum + (dataset['books'] as List).length),
      'chapterCount': datasetSummaries.fold<int>(
          0, (sum, dataset) => sum + (dataset['chapterCount'] as int)),
      'tokenCount': datasetSummaries.fold<int>(
          0, (sum, dataset) => sum + (dataset['tokenCount'] as int)),
    };
    final provenance = <String, Object?>{
      'schemaVersion': 1,
      'generator': _generator,
      'generatorScript': 'tool/generate_interlinear_assets.dart',
      'generatorSha256': resourceSha256(generatorBytes),
      'companionPackage': 'bible_io_interlinear 0.1.0',
      'dartSdk': Platform.version.split(' ').first,
      'sourceLockSha256': resourceSha256(lockBytes),
      'sourceLock': lock,
      'thirdPartyNoticesSha256': resourceSha256(notices),
      'compression':
          'gzip level 9; timestamp 0; operating-system byte 255; no filename; '
              'manifest hashes describe uncompressed JSON; transport hashes recorded separately.',
      'decodedTextHashes': 'Dart UTF-8 decoding removes the optional UTF-8 BOM. '
          'Raw source hashes in sourceLock cover all downloaded bytes including BOM.',
      'coverageMeaning': 'All 66 supported books and all 1189 source chapters. '
          'A source profile may omit complete verse entries or individual variants; '
          'no empty positive verse is fabricated. Coverage is not a universal translation alignment.',
      'limitations': [
        'TAGNT N is a source-row reading, not an independently reproduced NA27/NA28 edition.',
        'TAHOT L+Q+R follows qere, includes restorations and excludes X additions and inline variants.',
        'Verse zero is preserved as special entries. Other edition reference mappings are separate.',
        'Display spacing is reconstructed; original language, translation and gloss language are independent.',
      ],
      'datasets': reports,
      'transportResources': transportResources,
    };
    if (index['bookCount'] != 66 ||
        index['chapterCount'] != 1189 ||
        index['tokenCount'] != 443132) {
      throw const FormatException(
          'The pinned full-source coverage/count expectations were not met.');
    }
    await File('${staging.path}/asset-index.json')
        .writeAsString('${_codec.encodeJson(index)}\n');
    await File('${staging.path}/provenance.json')
        .writeAsString('${_codec.encodeJson(provenance)}\n');
    await File('${staging.path}/sources.lock.json').writeAsBytes(lockBytes);
    await File('${staging.path}/THIRD_PARTY_NOTICES.md').writeAsBytes(notices);
    Directory? backup;
    if (await output.exists()) {
      backup = await output.rename(
          '${output.path}.previous-${DateTime.now().microsecondsSinceEpoch}');
    }
    try {
      await staging.rename(output.path);
      staging = null;
    } catch (_) {
      if (backup != null && !await output.exists()) {
        await backup.rename(output.path);
      }
      rethrow;
    }
    if (backup != null) {
      stdout.writeln('Previous generated assets retained at ${backup.path}');
    }
    stdout.writeln(
        'Generated and verified ${index['bookCount']} books, ${index['chapterCount']} chapters, '
        '${index['tokenCount']} tokens at ${output.path}.');
  } catch (error) {
    stderr.writeln('Asset generation failed: $error');
    if (staging != null) {
      stderr.writeln('Incomplete staging retained at ${staging.path}');
    }
    exitCode = 1;
  }
}

Map<String, String> _options(List<String> arguments) {
  final result = <String, String>{};
  for (var index = 0; index < arguments.length; index++) {
    final argument = arguments[index];
    if (argument == '--help' || argument == '--overwrite') {
      result[argument.substring(2)] = 'true';
      continue;
    }
    if (!['--package-root', '--source-root', '--lock', '--output']
            .contains(argument) ||
        index + 1 >= arguments.length ||
        arguments[index + 1].startsWith('--')) {
      throw FormatException('Unknown option or missing value: $argument');
    }
    result[argument.substring(2)] = arguments[++index];
  }
  return result;
}

List<int> _gzip(List<int> bytes) {
  final encoded = GZipCodec(level: 9).encode(bytes);
  if (encoded.length < 18 || encoded[3] != 0) {
    throw const FormatException('Unexpected gzip header.');
  }
  encoded.fillRange(4, 8, 0); // MTIME: reproducible independent of wall clock.
  encoded[9] = 255; // OS: reproducible independent of the generation host.
  return encoded;
}

final _recordPrefix = RegExp(
    r'^([1-3]?[A-Za-z]{2,3})\.([1-9][0-9]*)\.([0-9]+[a-z]?(?:-[0-9]+[a-z]?)?)(?:[({\[].*)?#');

Iterable<String> _sourceLabels(String text) sync* {
  // This inventories source addresses only; StepImporter validates/normalizes
  // the complete rows. It neither selects readings nor maps edition references.
  for (final line in const LineSplitter().convert(text)) {
    final match = _recordPrefix.firstMatch(line);
    if (match != null) {
      yield '${match[1]!.toUpperCase()}.${match[2]}.${match[3]}';
    }
  }
}

String _header(String text) {
  final lines = const LineSplitter().convert(text);
  return lines
      .takeWhile(
          (line) => !line.startsWith('# ') && !_recordPrefix.hasMatch(line))
      .join('\n');
}
