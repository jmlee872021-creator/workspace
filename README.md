# workspace

클라우드 세션에서 구글 드라이브 `Jakin_workspace` 의 도구를 돌리기 위한 저장소.

- `tools/드라이브.py` — 드라이브에서 받기 · 바뀐 것 견주기 · 올리기 (`python3 tools/드라이브.py --help`)
- `tools/법준비.sh` — 법률 문답에 쓸 것(법.db · 낱말.db · 찾기 도구 · 업무매뉴얼 정본)을 받고 매뉴얼 색인을 짓는다
- `tools/매뉴얼찾기.py` — 업무매뉴얼ㆍ지난 문답에서 이미 정리해 둔 답을 찾는다 (근거는 법.db 원문 — `CLAUDE.md` 「법률 문답」)
- `.claude/hooks/session-start.sh` — 클라우드 세션이 열릴 때 파이썬 꾸러미(pyyaml, pymupdf, pandas …)를 깔고 `법준비.sh` 를 뒤에서 돌린다

열쇠: 프로젝트 클라우드 환경의 환경변수 `GDRIVE_CLIENT_ID` · `GDRIVE_CLIENT_SECRET` · `GDRIVE_REFRESH_TOKEN`.
받은 사본은 `~/Jakin_workspace` 에 생긴다 (도구들은 `.뿌리` 표식으로 뿌리를 찾아 G: 경로가 필요 없다).
