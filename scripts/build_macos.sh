#!/bin/sh
set -eu

ROOT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
cd "$ROOT_DIR"

PYTHON=${PYTHON:-python3}
"$PYTHON" -m venv .venv-packaging
BUILD_PYTHON="$ROOT_DIR/.venv-packaging/bin/python"
"$BUILD_PYTHON" -m pip install --upgrade pip
"$BUILD_PYTHON" -m pip install -e ".[packaging]"

ARCH=$(uname -m)
DIST_DIR="dist/macos-$ARCH"
"$BUILD_PYTHON" -m PyInstaller \
    --noconfirm \
    --clean \
    --distpath "$DIST_DIR" \
    --workpath "build/pyinstaller-macos-$ARCH" \
    build/banking-support-evaluation.spec

cp scripts/run_macos.command "$DIST_DIR/RunBankingSupportAgent.command"
chmod +x "$DIST_DIR/RunBankingSupportAgent.command"
printf 'Built macOS executable in %s\n' "$DIST_DIR"