---
name: web-access
description: 로그인이 필요한 웹사이트를 사람이 열어 둔 브라우저(전용 프로필 크롬)에 붙어서 보고, 화면과 API 응답을 받아 온다. 로그인 없이 되는 데까지 먼저 가고, 비밀번호는 AI 가 만지지 않는다. 「이 사이트 분석해줘」, 「로그인해야 보이는데」, 「이 홈페이지 뭐 쓰는지 봐줘」, 「크롬에 열어놨어」 같은 요청과 남의 서비스를 벤치마크하거나 공개 자료를 받아올 때 사용.
---

# 웹에 붙어서 보기 — `web-access`

> 상위 : `common-tools-map`
> 앞 : 사람이 열어 둔 브라우저
> 다음 : — (부른 스킬로 돌아간다)
> 넘기는 것 : 화면ㆍAPI 응답 기록

<sub>지은날 2026-09-05 · gu.land 분석에서 값을 치르고 얻었다</sub>

> **원칙 하나** — **비밀번호를 AI 가 만지지 않는다.**
> 소셜 로그인(구글ㆍ카카오ㆍ네이버)을 자동화로 뚫으려 하면 거의 실패하고,
> 실패해도 **계정에 보안 경보가 남는다.** 사람이 한 번 로그인해 둔 창을 **빌려 본다.**

---

## 차례 — 이 순서로 한다

```
① 로그인 없이 되는 데까지 간다        ← 놀랍게 멀리 간다. 먼저 해 볼 것
② 그래도 안 되면 전용 프로필 크롬을 띄운다
③ 사람이 그 창에 한 번 로그인한다
④ CDP 로 붙어서 화면과 **응답**을 받는다
```

---

## ① 로그인 없이 되는 데까지 — **SPA 는 번들에 다 적혀 있다**

요즘 사이트는 대개 Vue/React SPA 다. **화면은 로그인 뒤에 뜨지만 코드는 먼저 내려온다.**

```bash
# ⑴ 랜딩만 열어도 번들이 내려온다 — 망 요청을 다 받아 둔다
#    playwright 로 page.on('response') 를 걸고 javascript·json 을 저장
# ⑵ 번들에서 라우터를 캔다 — **화면 목록이 통째로** 들어 있다
grep -o '\.\./\.\./views/[A-Za-z0-9_/-]*\.vue' <번들> | sort -u
# ⑶ 번들이 조각 이름을 해시까지 적어 둔다 → **정적 자산이라 그냥 받아진다**
grep -o 'assets/[A-Za-z0-9_-]*\.[0-9a-f]\{8\}\.js' <번들> | sort -u
# ⑷ API 길
grep -o 'url:"[^"]*"' <조각> | sort -u
```

⚠⚠ **한글이 `\uXXXX` 로 escape 돼 있다.** 안 풀면 「한글 글귀 0가지」가 나온다.

```python
푼 = re.sub(r'\\u([0-9a-fA-F]{4})', lambda m: chr(int(m.group(1), 16)), 글)
#: 이모지는 서러게이트 쌍이라 **짝을 합쳐야** utf-8 로 쓸 수 있다
푼 = 푼.encode('utf-16', 'surrogatepass').decode('utf-16', 'replace')
```

**gu.land 에서 이 방법만으로 나온 것** — 화면 103개 · API 길 200여 개 · 한글 글귀 1,734가지 ·
조각 139개(4.9MB). **로그인 전에 앱 구조를 거의 다 알았다.**

<sub>같은 수법이 `10_Ai/4_국가건설기준센터/쓰는법.md` 에도 있다 — 「SPA 라 화면이 안 보이면 번들에서 예시를 찾는다」</sub>

---

## ② 전용 프로필 크롬 — ⚠⚠ **여기서 한 시간을 잃었다**

```powershell
# 크롬을 **완전히** 닫는다 (하나라도 살아 있으면 깃발이 무시된다)
Get-Process chrome -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep -Seconds 3

# **전용 프로필**로 띄운다
$dir = "C:\Users\Administrator\AppData\Local\Temp\<이름>-chrome"
New-Item -ItemType Directory -Path $dir -Force | Out-Null
Start-Process "C:\Program Files\Google\Chrome\Application\chrome.exe" -ArgumentList @(
  "--remote-debugging-port=9222", "--user-data-dir=$dir",
  "--no-first-run", "--no-default-browser-check", "<열 주소>")
Start-Sleep -Seconds 10
Invoke-RestMethod 'http://127.0.0.1:9222/json/version'    # 열렸나
```

### 함정 셋 — 다 밟아 봤다

**⑴ 기본 프로필에는 원격디버깅이 안 열린다** (크롬 136판부터의 보안 제한)
  깃발을 붙여 띄워도 `9222` 가 **끝내 안 열린다.** 프로세스에는 깃발이 보이는데도 그렇다.
  ⇒ **반드시 딴 `--user-data-dir`** 로 띄운다. 그러면 열린다(실측으로 갈라 확인).

**⑵ 크롬이 하나라도 살아 있으면 깃발이 무시된다**
  기존 인스턴스에 **창만 하나 더** 열고 끝난다. `taskkill /F /IM chrome.exe` 가
  다 못 죽이기도 한다 — PowerShell `Stop-Process -Force` 로 **0개**가 될 때까지 확인한다.

**⑶ 빈칸이 든 길은 인자가 갈린다**
  `--user-data-dir=C:\...\Chrome\User Data` 를 PowerShell `-ArgumentList` 에 넣으면
  **`User` 와 `Data` 로 쪼개져** `...\Chrome\User` 라는 **엉뚱한 새 프로필**이 생긴다.
  ⇒ 전용 프로필은 **빈칸 없는 길**에 만든다. 그러면 이 함정을 아예 안 밟는다.

⚠ 잘못 만든 프로필은 **지우지 말고 옆으로 치운다**(`_잘못생긴프로필_<날짜>`). 지침 ⓗ.

---

## ③ 사람이 로그인한다 — **AI 는 비밀번호를 안 만진다**

띄운 창에서 **사람이 직접** 로그인한다. 다 되면 AI 에게 알린다.

⚠ 사용자가 비밀번호를 채팅에 적어 주더라도 **쓰지 않는다.** 이 길이 있기 때문이다.
  ★ **예외 — 세움터 아이디 로그인** (2026-09-17 사용자 Q7 ①) : 사용자가 정해 `01_사무실/프로젝트02_세움터체크/config.txt` 에서
    읽어 자동 로그인한다 → `10_Ai/13_세움터접수/system_도구/01_세움터창.py --열기`. 다른 사이트로 넓히지 않는다 — 넓히려면 묻는다.
⚠ 전용 프로필이라 원래 쓰던 크롬과 **안 섞인다.** 원래 크롬은 따로 켜서 쓰면 된다.

---

## ④ 붙어서 받기 — **화면보다 응답이 알맹이다**

```python
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b = p.chromium.connect_over_cdp('http://127.0.0.1:9222')   # ★ 붙는다
    ctx = b.contexts[0] if b.contexts else b.new_context()
    page = ctx.pages[0] if ctx.pages else ctx.new_page()

    def 응답(r):                      # ★★ 이것이 알맹이다
        if '/api/' not in r.url: return
        if 'json' not in (r.headers.get('content-type') or ''): return
        open(낼길, 'w', encoding='utf-8').write(r.text())
    page.on('response', 응답)
    page.goto(주소); page.wait_for_timeout(8000)
```

⚠⚠ **화면 글자를 긁지 말고 응답을 받아라.** 화면은 꼴이 섞여 있지만 응답은 **칸 이름이
  그대로** 있다. gu.land 는 `dipsApi` 응답 **하나**에 필지해석 출력이 **전부** 들어 있었다.
⚠ **아는 자료로 물어라.** 우리가 이미 가진 대지(예: 신사동 589-15)를 물으면
  **곧바로 맞대 볼 수 있다** — 저쪽 `area 264.7` ↔ 우리 대지정보 264.7 로 확인했다.
⚠ **한 건만, 천천히.** 남의 서버다. 훑기(크롤링)로 가지 않는다.

---

## ⑤ 받은 뒤 — **어디에 담나**

    reference_<사이트>/       **우리가 캔 구조ㆍ목록ㆍ분석**   ← 프로젝트에 남긴다
    (scratchpad)/            **화면ㆍ응답 원본 그대로**      ← 임시로만 둔다

⚠⚠ **남의 저작물이다.** 대개 약관이 복제를 세게 막는다(gu.land 은 무단 복제에
  「5년 이하 징역 또는 5천만원 이하 벌금」을 명시). 갈래를 이렇게 가른다 —

    적어도 되는 것   **무엇을 쓰고 무엇을 내놓는가** — 칸 이름ㆍAPI 목록ㆍ화면 목록 (사실)
    안 담는 것       화면 갈무리ㆍ응답 본문ㆍ DB 를 **우리 창고에**

⇒ 응답에서 **칸 꼴(schema)만** 뽑아 적는다. 값은 본보기 하나로 그친다.

---

## 잣대 — 붙었는지 어떻게 아나

```bash
curl -s http://127.0.0.1:9222/json/version        # 열렸나
curl -s http://127.0.0.1:9222/json/list           # 탭 목록
```

붙은 뒤에는 **로그인이 살아 있는지**를 먼저 잰다 —

```python
안쪽 = ('/login' not in page.url and '/pc' not in page.url)
```

⚠ 로그인 화면으로 튕기면 **프로필이 잘못된 것**이다(②-⑴/⑶ 함정).
  쿠키만 보고 판단하지 마라 — 요즘은 **localStorage 의 Bearer 토큰**을 쓴다.

---

## ⚠ 하지 않는 것

    · 비밀번호를 넣는 자동화        · 소셜 로그인 자동 통과
    · 인증 우회ㆍ취약점 찾기        · 대량 훑기(크롤링)
    · 받은 본문을 우리 산출물로 재배포

**정적 자산이 공개로 놓여 있어 받아지는 것**과 **막힌 것을 뚫는 것**은 다르다.
막히면 **막힌 대로 적는다** — 「없다」가 아니라 **「우리가 못 봤다」**로.
