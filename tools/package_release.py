"""Create audited source and Quest install packages without local configuration."""
import argparse
import hashlib
from pathlib import Path
import shutil
import zipfile
from privacy_check import ROOT, source_files, audit, findings, local_secrets


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--export-source', type=Path, help='New, empty standalone source directory')
    args = parser.parse_args()
    version = '0.1.22-nao-test'
    apk = ROOT / 'dist/TeleNao-Quest.apk'
    files = list(source_files())
    if not apk.is_file():
        raise SystemExit('Build the Quest APK first')
    problems = audit(files + [apk])
    if problems:
        raise SystemExit('Privacy audit failed; inspect source/APK before packaging')
    if args.export_source:
        target = args.export_source.resolve()
        if target.exists() and any(target.iterdir()):
            raise SystemExit('Source export must be a new or empty directory')
        target.mkdir(parents=True, exist_ok=True)
        for path in files:
            dest = target / path.relative_to(ROOT)
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, dest)
    output = ROOT / 'dist/release'
    output.mkdir(parents=True, exist_ok=True)
    shutil.copy2(apk, output / apk.name)
    source = output / ('TeleNao-source-' + version + '.zip')
    install = output / ('TeleNao-Quest-install-' + version + '.zip')
    with zipfile.ZipFile(source, 'w', zipfile.ZIP_DEFLATED) as archive:
        for path in files:
            archive.write(path, 'nao-tele/' + path.relative_to(ROOT).as_posix())
    with zipfile.ZipFile(install, 'w', zipfile.ZIP_DEFLATED) as archive:
        archive.write(apk, apk.name)
        archive.write(ROOT / 'tools/Install-Release.ps1', 'Install-Release.ps1')
        for path in files:
            rel = path.relative_to(ROOT)
            if rel.as_posix() in {'README.md', 'LICENSE', 'NOTICE', 'SECURITY.md'} or rel.parts[0] == 'docs' or (rel.parts[0] == 'third_party' and path.suffix.lower() == '.txt'):
                archive.write(path, rel.as_posix())
    secrets = local_secrets()
    for bundle in (source, install):
        with zipfile.ZipFile(bundle) as archive:
            for name in archive.namelist():
                if name.endswith('/'):
                    continue
                if findings(archive.read(name), secrets):
                    raise SystemExit('Release archive privacy audit failed')
    assets = [output / apk.name, install, source]
    sums = ''.join(hashlib.sha256(p.read_bytes()).hexdigest() + '  ' + p.name + '\n' for p in assets)
    (output / 'SHA256SUMS.txt').write_text(sums, encoding='ascii')
    print('Audited %d source files; created APK, installation ZIP, source ZIP and SHA256SUMS.txt.' % len(files))


if __name__ == '__main__':
    main()
