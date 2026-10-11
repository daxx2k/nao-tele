"""Render the actual Appearance UI on a connected Quest without launching VR.

Requires Python/Pillow and Android SDK/NDK. Generated files stay in .local.
The harness injects the app's drawing methods and shader verbatim, so this
preview cannot quietly use different artwork, layout or typography.
"""
import argparse
import json
import os
from pathlib import Path
import re
import subprocess
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
METHODS = ('vertices', 'text', 'centeredText', 'pixelLine', 'panel',
           'themedPanel', 'surfaceCard', 'drawNaoLeds')


def drawing_method(source, name):
    start = source.index('    void ' + name + '(')
    body = source.index('{', start)
    depth, end = 1, body + 1
    while depth:
        depth += (source[end] == '{') - (source[end] == '}')
        end += 1
    return source[start:end]


def run(*args):
    subprocess.run([str(a) for a in args], check=True, cwd=ROOT)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--serial', help='ADB serial when more than one device is connected')
    parser.add_argument('--sdk', type=Path, help='Android SDK directory')
    args = parser.parse_args()
    sdk = args.sdk or Path(os.environ.get('ANDROID_HOME') or
                           os.environ.get('ANDROID_SDK_ROOT') or
                           str(Path(os.environ.get('LOCALAPPDATA', '')) / 'Android/Sdk'))
    windows = os.name == 'nt'
    adb = sdk / 'platform-tools' / ('adb.exe' if windows else 'adb')
    gradle = (ROOT / 'quest/build.gradle').read_text(encoding='utf-8')
    ndk = re.search(r"ndkVersion '([^']+)'", gradle)[1]
    host = 'windows-x86_64' if windows else 'darwin-x86_64' if os.uname().sysname == 'Darwin' else 'linux-x86_64'
    compiler = sdk / 'ndk' / ndk / 'toolchains/llvm/prebuilt' / host / 'bin' / (
        'aarch64-linux-android29-clang++.cmd' if windows else 'aarch64-linux-android29-clang++')
    if not adb.is_file() or not compiler.is_file():
        raise SystemExit('Set --sdk to the Android SDK with the project NDK installed.')
    command = [adb] + (['-s', args.serial] if args.serial else [])
    source = (ROOT / 'quest/src/main/cpp/main.cpp').read_text(encoding='utf-8')
    fragment = re.search(r'const char\* frag=R"glsl\((.*?)\)glsl";', source, re.S)[1]
    template = (ROOT / 'tools/appearance_preview.cpp.in').read_text(encoding='utf-8')
    code = template.replace('@@FRAGMENT@@', json.dumps(fragment))
    canvas = re.search(r'static constexpr int W=(\d+),H=(\d+)', source)
    code = code.replace('@@CANVAS@@', f'    static constexpr int W={canvas[1]},H={canvas[2]};')
    code = code.replace('@@RENDER_METHODS@@', '\n'.join(drawing_method(source, n) for n in METHODS))
    code = code.replace('@@UI_TYPES@@', re.search(r'namespace ui_type \{[^}]+\}', source)[0])
    code = code.replace('@@LED_COLOURS@@', re.search(r'    const int ledColors\[7\]=[^;]+;', source)[0])
    local = ROOT / '.local'
    local.mkdir(exist_ok=True)
    cpp, executable = local / 'appearance-preview.cpp', local / 'appearance-preview'
    cpp.write_text(code, encoding='utf-8')
    run(compiler, '-std=c++17', '-static-libstdc++', cpp, '-lEGL', '-lGLESv3', '-o', executable)
    artwork = Image.open(ROOT / 'quest/src/main/assets/nao_led_avatar.png').convert('RGBA')
    raw = local / 'appearance-preview.rgba'
    raw.write_bytes(artwork.tobytes())
    remote = '/data/local/tmp/telenao-preview'
    run(*command, 'shell', 'mkdir', '-p', remote)
    run(*command, 'push', executable, remote + '/render')
    run(*command, 'push', raw, remote + '/avatar.rgba')
    run(*command, 'push', ROOT / 'quest/src/main/assets/ui_font.bin', remote + '/ui_font.bin')
    run(*command, 'shell', 'chmod', '755', remote + '/render')
    run(*command, 'shell', remote + '/render')
    ppm = local / 'appearance-real-preview.ppm'
    run(*command, 'pull', remote + '/panel.ppm', ppm)
    output = local / 'appearance-real-preview.png'
    Image.open(ppm).save(output)
    print('Actual app renderer at %d x %d pixels:' % Image.open(output).size, output.name)


if __name__ == '__main__':
    main()
