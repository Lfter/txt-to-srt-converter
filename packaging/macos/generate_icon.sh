#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
ICON_DIR="$ROOT_DIR/assets/icon"
SVG_PATH="$ICON_DIR/txt_to_srt.svg"
MASTER_PNG="$ICON_DIR/txt_to_srt_1024.png"
ICNS_PATH="$ICON_DIR/txt_to_srt.icns"
PYTHON_BIN="$ROOT_DIR/.venv/bin/python"

if ! command -v rsvg-convert >/dev/null 2>&1; then
  echo "rsvg-convert 未找到，请先安装 librsvg（例如: brew install librsvg）。" >&2
  exit 1
fi

if [ ! -x "$PYTHON_BIN" ]; then
  echo "未找到虚拟环境 Python: $PYTHON_BIN" >&2
  exit 1
fi

if ! "$PYTHON_BIN" -c "import PIL" >/dev/null 2>&1; then
  echo "未检测到 Pillow，请先执行: .venv/bin/pip install -r requirements-build.txt" >&2
  exit 1
fi

mkdir -p "$ICON_DIR"

cat > "$SVG_PATH" <<'SVG'
<svg xmlns="http://www.w3.org/2000/svg" width="1024" height="1024" viewBox="0 0 1024 1024">
  <rect x="96" y="96" width="832" height="832" rx="192" fill="#0F68D8" />
  <rect x="238" y="160" width="548" height="704" rx="72" fill="#FFFFFF" />

  <rect x="296" y="248" width="212" height="112" rx="28" fill="#F28B3A" />
  <text x="402" y="322" text-anchor="middle" font-family="Helvetica, Arial, sans-serif" font-size="68" font-weight="700" fill="#FFFFFF">TXT</text>

  <path d="M534 268h132v-38l114 86-114 86v-38H534z" fill="#0F68D8" />

  <rect x="296" y="468" width="212" height="112" rx="28" fill="#2FB36A" />
  <text x="402" y="542" text-anchor="middle" font-family="Helvetica, Arial, sans-serif" font-size="68" font-weight="700" fill="#FFFFFF">SRT</text>

  <rect x="296" y="640" width="430" height="34" rx="17" fill="#DCE6F5" />
  <rect x="296" y="696" width="430" height="34" rx="17" fill="#DCE6F5" />
  <rect x="296" y="752" width="320" height="34" rx="17" fill="#DCE6F5" />
</svg>
SVG

rsvg-convert -w 1024 -h 1024 "$SVG_PATH" -o "$MASTER_PNG"

"$PYTHON_BIN" - "$MASTER_PNG" "$ICNS_PATH" <<'PY'
from pathlib import Path
import sys

from PIL import Image

master_png = Path(sys.argv[1])
icns_path = Path(sys.argv[2])
sizes = [(16, 16), (32, 32), (64, 64), (128, 128), (256, 256), (512, 512), (1024, 1024)]

with Image.open(master_png) as img:
    img.convert("RGBA").save(icns_path, format="ICNS", sizes=sizes)
PY

echo "图标已生成: $ICNS_PATH"
