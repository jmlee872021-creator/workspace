#!/bin/bash
# 법률 문답에 쓸 것을 드라이브에서 받는다 — 세션 시작 훅이 뒤에서 돌린다 (손으로 다시 돌려도 된다).
# 이미 받은 것은 md5 가 같으면 건너뛴다.  다 되면 ~/Jakin_workspace/.법준비됨 에 시각을 적는다.
set -uo pipefail
cd "$(dirname "$0")/.."
ROOT="${JAKIN_DIR:-$HOME/Jakin_workspace}"
rm -f "$ROOT/.법준비됨"
받기() { python3 tools/드라이브.py 받기 "$@" || { echo "✗ 못 받음: $*"; FAIL=1; }; }
FAIL=0

# ① 도구 — 찾기.py 는 짓기/ 와 뿌리의 자리.py 를 부른다 · 개정이유찾기.py 는 0_원본/받기/ 를 부른다
받기 자리.py 10_Ai/1_법DB/찾기.py 10_Ai/1_법DB/개정이유찾기.py 10_Ai/1_법DB/쓰는법.md \
     10_Ai/1_법DB/짓기 10_Ai/1_법DB/0_원본/받기 \
     .claude/skills/law-lookup .claude/skills/law-site-qna

# ③ 큰 것 — 법.db 2.3GB · 낱말.db(검색 색인) 3GB.  ② 와 함께 받는다 (따로 두면 1분 더 든다)
python3 tools/드라이브.py 받기 --큰것 10_Ai/1_법DB/법.db 10_Ai/1_법DB/낱말.db > /tmp/법준비_큰것.log 2>&1 &
BIG=$!

# ② 업무매뉴얼 정본 — 「자주 하는 답」 으로 먼저 훑는다 (근거는 늘 법.db 원문)
받기 10_Ai/3_한국건축규정/system_표 \
     10_Ai/10_업무매뉴얼/12_용도변경_검토 10_Ai/10_업무매뉴얼/13_요소별_설계기준 10_Ai/10_업무매뉴얼/11_법률검토 \
     10_Ai/2_묻고답하기 --꼴 "*.yaml" "*.md"

# ②-가 질의회신집 PDF (국토부ㆍ서울시ㆍ소방청 · 30MB 남짓) — 매뉴얼찾기 의 「질의회신」 갈래
받기 "10_Ai/10_업무매뉴얼/사용자폴더_건축법 메뉴얼 작성용 참고자료" "10_Ai/10_업무매뉴얼/원본/공공기관_안내문/소방청 인허가 자료" \
     --큰것 --꼴 "*회신*.pdf"

wait $BIG || { echo "✗ 못 받음: 법.db · 낱말.db (/tmp/법준비_큰것.log)"; FAIL=1; }
cat /tmp/법준비_큰것.log

# ④ 매뉴얼 색인 (20초쯤) — tools/매뉴얼찾기.py 가 쓴다
python3 tools/매뉴얼찾기.py --짓기 || FAIL=1

if [ "$FAIL" = 0 ]; then
  date '+%F %T' > "$ROOT/.법준비됨"
  echo "✔ 법률 문답 준비됨"
else
  echo "✗ 일부를 못 받았다 — 위 줄을 보고 bash tools/법준비.sh 를 다시 돌린다"
fi
