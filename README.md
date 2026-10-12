# workspace

클라우드 세션에서 구글 드라이브 `Jakin_workspace` 의 도구를 돌리기 위한 저장소.

- `tools/드라이브.py` — 드라이브에서 받기 · 바뀐 것 견주기 · 올리기 (`python3 tools/드라이브.py --help`)
- `tools/법준비.sh` — 법률 문답에 쓸 것(법.db · 낱말.db · 찾기 도구 · 업무매뉴얼 정본)을 받고 매뉴얼 색인을 짓는다
- `tools/매뉴얼찾기.py` — 업무매뉴얼ㆍ지난 문답에서 이미 정리해 둔 답을 찾는다 (근거는 법.db 원문 — `CLAUDE.md` 「법률 문답」)
- `.claude/hooks/법답대조.py` — 법률 문답 답을 보내기 전에 잰다(Stop 훅): 결론ㆍ단서 문장마다 근거 원문 글귀가 붙었나 · 판단 말이 섞였나 · 근거 인용이 법.db 원문 글자 그대로인가(`법답원문.py`) (`--자가검사` · 케이스는 `법답케이스.yaml`)
- `tools/법답시험.py` — 법률 문답 시험 문제(`법답시험.yaml`, 12문제)를 채점한다: 규칙ㆍ훅을 바꾼 뒤 답이 흐트러지지 않았나
- `.claude/skills/` — 드라이브 스킬 41개의 사본(SKILL.md 만 커밋). `tools/스킬받기.sh` 가 세션마다 드라이브 최신으로 맞춘다 — 클라우드 세션에도 스킬이 실리게
- `.claude/hooks/session-start.sh` — 클라우드 세션이 열릴 때 파이썬 꾸러미(pyyaml, pymupdf, pandas …)를 깔고 `스킬받기.sh` 와 `법준비.sh` 를 뒤에서 돌린다

허용 도메인(네트워크): [`클라우드_허용도메인.md`](클라우드_허용도메인.md) — 환경을 다시 세팅할 때 그대로 붙여 넣는다.

열쇠: 프로젝트 클라우드 환경의 환경변수 `GDRIVE_CLIENT_ID` · `GDRIVE_CLIENT_SECRET` · `GDRIVE_REFRESH_TOKEN`.

열쇠가 끊겼을 때(`invalid_grant` — 「7일 지남 또는 취소됨」) — Refresh token 만 다시 받는다 (2026-10-12):
1. https://developers.google.com/oauthplayground → 오른쪽 위 톱니 → 「Use your own OAuth credentials」 에 Client ID · Client secret(환경변수와 같은 값, Google Cloud 콘솔 › API 및 서비스 › 사용자 인증 정보) 을 넣는다.
2. 왼쪽 Step 1 에 `https://www.googleapis.com/auth/drive` 를 넣고 「Authorize APIs」 → 드라이브 주인 계정으로 허용.
3. Step 2 「Exchange authorization code for tokens」 → **Refresh token** 을 복사한다.
4. 클라우드 환경 설정(세션 제목줄의 환경 메뉴 → Edit)에서 `GDRIVE_REFRESH_TOKEN` 값을 바꾼다 → 새 세션부터 쓴다. 열쇠는 채팅창에 붙이지 않는다.
- Client ID · 보안 비밀번호는 드라이브 `Jakin_workspace/클라우드세션설정/구글드라이브 api연결 (claude)/환경변수.txt` (와 client_secret_….json)에 있다. 자세한 차례ㆍ「확인하지 않은 앱」 경고 넘기는 법은 같은 폴더 `클라우드_드라이브연결.md` 4 장.
- 7일마다 끊기는 까닭 — 앱이 「테스트」 상태라서다. 「게시(프로덕션)」 로 바꾸면 끊기지 않지만, 게시 버튼이 브랜딩(홈페이지ㆍ개인정보처리방침 주소)을 채우기 전엔 막혀 있다(2026-10-05 · 아직 안 함).
받은 사본은 `~/Jakin_workspace` 에 생긴다 (도구들은 `.뿌리` 표식으로 뿌리를 찾아 G: 경로가 필요 없다).
