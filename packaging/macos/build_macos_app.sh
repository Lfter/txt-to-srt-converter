#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 未找到，请先安装 Python 3。" >&2
  exit 1
fi

if [ ! -d ".venv" ]; then
  python3 -m venv .venv
fi

.venv/bin/pip install -r requirements.txt -r requirements-build.txt
.venv/bin/pytest -q

rm -rf build dist

.venv/bin/pyinstaller \
  --noconfirm \
  --clean \
  --windowed \
  --name txt_to_srt \
  --osx-bundle-identifier com.ltzz.txttosrt \
  --specpath "$ROOT_DIR/packaging/macos" \
  --distpath "$ROOT_DIR/dist" \
  --workpath "$ROOT_DIR/build" \
  "$ROOT_DIR/main.py"

echo "打包完成: $ROOT_DIR/dist/txt_to_srt.app"
