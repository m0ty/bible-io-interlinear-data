import 'dart:convert';
import 'dart:io';
import 'dart:isolate';

import 'package:bible_io_interlinear/bible_io_interlinear.dart';

/// Uses the same package selected by pub for the running generator. Works with
/// hosted, Git and path dependencies; callers may explicitly inspect a checkout.
Future<String> resolveInterlinearPackageRoot(String? explicit) async {
  if (explicit != null) return Directory(explicit).absolute.path;
  final uri = await Isolate.resolvePackageUri(
    Uri.parse('package:bible_io_interlinear/bible_io_interlinear.dart'),
  );
  if (uri == null || uri.scheme != 'file') {
    throw StateError(
      'Cannot resolve bible_io_interlinear; run pub get or pass --package-root.',
    );
  }
  return File.fromUri(uri).parent.parent.path;
}

Future<List<int>> normalizedTextBytes(File file) async =>
    utf8.encode((await file.readAsString()).replaceAll('\r\n', '\n'));

/// Hashes the actual source, including uncommitted edits, not a version label.
/// LF normalization makes the fingerprint independent of Git checkout settings.
Future<Map<String, Object?>> interlinearPackageIdentity(String root) async {
  final directory = Directory(root);
  final names = <String>['pubspec.yaml', 'THIRD_PARTY_NOTICES.md'];
  for (final subdirectory in ['lib', 'bin', 'tool']) {
    final source = Directory('$root/$subdirectory');
    if (!await source.exists()) continue;
    await for (final entity in source.list(
      recursive: true,
      followLinks: false,
    )) {
      if (entity is Link) {
        throw StateError('Package source contains a symlink.');
      }
      if (entity is File &&
          (entity.path.endsWith('.dart') ||
              entity.path.endsWith('sources.lock.json'))) {
        names.add(
          entity.absolute.path
              .substring(directory.absolute.path.length + 1)
              .replaceAll('\\', '/'),
        );
      }
    }
  }
  names.sort();
  final hashes = <String, Object?>{};
  for (final name in names) {
    hashes[name] = resourceSha256(
      await normalizedTextBytes(File('$root/$name')),
    );
  }
  final pubspec = await File('$root/pubspec.yaml').readAsString();
  final version = RegExp(
    r'^version:\s*(\S+)',
    multiLine: true,
  ).firstMatch(pubspec)?.group(1);
  return {
    'name': 'bible_io_interlinear',
    'version': version,
    ..._identity(hashes),
  };
}

Map<String, Object?> _identity(Map<String, Object?> hashes) => {
  'hashEncoding':
      'SHA-256 of canonical JSON path-to-SHA-256 map; source text normalized to UTF-8 LF',
  'sha256': resourceSha256(
    utf8.encode(const InterlinearJsonCodec().encodeJson(hashes)),
  ),
  'files': hashes,
};
