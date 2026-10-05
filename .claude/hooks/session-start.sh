#!/bin/bash
# 클라우드 세션에서만 — Jakin_workspace 도구가 쓰는 파이썬 꾸러미를 깐다.
set -euo pipefail
if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi
python3 -m pip install -q --disable-pip-version-check pyyaml pymupdf pandas beautifulsoup4 pillow 2>&1 | grep -v "Running pip as the 'root'" || true
echo 'export JAKIN_DIR="$HOME/Jakin_workspace"' >> "${CLAUDE_ENV_FILE:-/dev/null}"
if [ -n "${GDRIVE_REFRESH_TOKEN:-}" ]; then
  echo "드라이브 열쇠 있음 — python3 tools/드라이브.py 받기 <폴더> 로 Jakin_workspace 를 받는다"
else
  echo "드라이브 열쇠 없음 — tools/드라이브.py 는 환경변수 GDRIVE_CLIENT_ID · GDRIVE_CLIENT_SECRET · GDRIVE_REFRESH_TOKEN 이 있어야 돈다"
fi
