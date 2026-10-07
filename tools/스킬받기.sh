#!/bin/bash
# 드라이브 Jakin_workspace/.claude/skills (원본) → 이 저장소 .claude/skills (사본) — 세션 시작 훅이 뒤에서 돌린다.
# 클라우드 세션은 이 저장소에서 시작하므로 드라이브의 스킬이 저절로 안 실린다. 사본을 두어 PC 에서처럼 말에 걸려 켜지게 한다.
# 저장소에 SKILL.md 사본이 커밋돼 있어 받기가 실패해도 목록은 뜬다. 이것은 그 사본을 드라이브 최신으로 맞추고 references 등을 채운다.
# ⚠ 사본을 고치지 않는다 — 원본은 드라이브다. git status 에 바뀐 SKILL.md 가 보이면 드라이브 쪽이 새것이다(커밋하면 다음 세션 목록이 새것).
set -uo pipefail
cd "$(dirname "$0")/.."
ROOT="${JAKIN_DIR:-$HOME/Jakin_workspace}"
python3 tools/드라이브.py 받기 .claude/skills || { echo "✗ 스킬을 못 받았다 — 커밋된 사본으로 간다"; exit 1; }
[ -d "$ROOT/.claude/skills" ] || { echo "✗ $ROOT/.claude/skills 가 없다"; exit 1; }
mkdir -p .claude/skills
cp -r "$ROOT/.claude/skills/." .claude/skills/
find .claude/skills -name __pycache__ -type d -prune -exec rm -rf {} + 2>/dev/null
echo "✔ 스킬 $(ls "$ROOT/.claude/skills" | wc -l)개를 드라이브 최신으로 맞췄다"
