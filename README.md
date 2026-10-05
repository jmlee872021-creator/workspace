# workspace

클라우드 세션에서 구글 드라이브 `Jakin_workspace` 의 도구를 돌리기 위한 저장소.

- `tools/드라이브.py` — 드라이브에서 받기 · 바뀐 것 견주기 · 올리기 (`python3 tools/드라이브.py --help`)
- `.claude/hooks/session-start.sh` — 클라우드 세션이 열릴 때 파이썬 꾸러미(pyyaml, pymupdf, pandas …)를 깐다

열쇠: 프로젝트 클라우드 환경의 환경변수 `GDRIVE_CLIENT_ID` · `GDRIVE_CLIENT_SECRET` · `GDRIVE_REFRESH_TOKEN`.
받은 사본은 `~/Jakin_workspace` 에 생긴다 (도구들은 `.뿌리` 표식으로 뿌리를 찾아 G: 경로가 필요 없다).
