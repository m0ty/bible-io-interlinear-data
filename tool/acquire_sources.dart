import 'dart:io';
import 'dart:isolate';

import 'interlinear_tool_support.dart';

/// Explicit source acquisition through the installed, pinned core package.
/// Never runs as a side effect of using the prepared data.
Future<void> main(List<String> arguments) async {
  final root = await resolveInterlinearPackageRoot(null);
  final config = await Isolate.packageConfig;
  if (config == null) throw StateError('Run dart pub get first.');
  final process = await Process.start(Platform.resolvedExecutable, [
    '--packages=${config.toFilePath()}',
    '$root/tool/acquire_sources.dart',
    '--lock',
    '$root/tool/sources.lock.json',
    ...arguments,
  ], mode: ProcessStartMode.inheritStdio);
  exitCode = await process.exitCode;
}
