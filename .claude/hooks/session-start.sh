#!/bin/bash
# 클라우드 세션에서만 — Jakin_workspace 도구가 쓰는 파이썬 꾸러미를 깐다.
set -euo pipefail
if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi
python3 -m pip install -q --disable-pip-version-check pyyaml pymupdf pandas beautifulsoup4 pillow \
  openpyxl markdown pypdf pdfplumber olefile shapely matplotlib ezdxf fonttools 2>&1 | grep -v "Running pip as the 'root'" || true
# 한글 글꼴 — 없으면 PDF 에 한글이 네모(□)로 찍힌다
if ! fc-list :lang=ko 2>/dev/null | grep -qi nanum; then
  (apt-get install -y -q fonts-nanum fonts-noto-cjk >/dev/null 2>&1 && fc-cache -f >/dev/null 2>&1) || echo "한글 글꼴을 못 깔았다 (apt)"
fi
echo 'export JAKIN_DIR="$HOME/Jakin_workspace"' >> "${CLAUDE_ENV_FILE:-/dev/null}"
if [ -n "${GDRIVE_REFRESH_TOKEN:-}" ]; then
  echo "드라이브 열쇠 있음 — python3 tools/드라이브.py 받기 <폴더> 로 Jakin_workspace 를 받는다"
else
  echo "드라이브 열쇠 없음 — tools/드라이브.py 는 환경변수 GDRIVE_CLIENT_ID · GDRIVE_CLIENT_SECRET · GDRIVE_REFRESH_TOKEN 이 있어야 돈다"
fi
