---
name: revit-control
description: Revit MCP 연결ㆍ진단과 쓰기 전 제어 규칙. 「Revit 연결이 안 된다」, 「MCP 도구가 안 보인다」, HTTP 500ㆍRouteHandlerNotDefinedExceptionㆍ10054ㆍ타임아웃이 나거나 pyRevit 익스텐션 등록이 의심될 때 파일을 뒤지기 전에 연다. 활성 문서 확인, 트랜잭션, Revit 인쇄ㆍPDF, 제목블록 크기, 그린 요소 지우고 다시 그리기도 다룬다. Revit 에 무엇이든 쓰기 전에 먼저 읽는다.
---

# Revit 제어

> 상위 : `revit-map`
> 앞 : 열린 Revit (사용자)
> 다음 : `revit-modeling` · `family-from-drawings` · `design-summary`
> 넘기는 것 : 붙은 상태 · 활성 문서 확인

> **2026-09-02 확정.** 쌍문동 315-232 설계개요·주차계획도 작업과 PDF 출력에서
> 실제로 값을 틀리게 하거나 사용자 파일을 건드린 것들만 모았다.
> **가정으로 쓴 줄은 없다 — 전부 한 번씩 당해 본 것이다.**

---

## §0 ★ 무엇을 하기 전이든 — 활성 문서를 먼저 확인한다

**이 세션에서 가장 크게 잘못한 것이다.** Revit 에 문서가 두 개 열려 있었고,
`revit_exec` 의 `doc` 은 **그때그때의 활성 문서**다. 사용자가 창을 바꾸면 조용히 바뀐다.

그 결과 **쌍문동에 하려던 인쇄·시트세트 조작이 마천동에 들어갔다.**
「쌍문동315-232 시트세트가 사라졌다」고 잘못 진단하고 복구를 시도하기까지 했다.

```python
#  ★ 모든 exec 의 첫 줄에 넣는다
d = globals()["doc"]
assert u"쌍문동" in d.Title, u"활성 문서가 다르다: %s" % d.Title
```

**더 나은 방법 — 활성 문서에 기대지 말고 문서를 이름으로 집는다.**

```python
target = None
for od in uiapp.Application.Documents:
    if (not od.IsFamilyDocument) and (not od.IsLinked) and od.Title.startswith(u"쌍문동"):
        target = od
        break
```

문서 객체만 있으면 **활성화하지 않고도** 조회·트랜잭션·인쇄까지 다 된다.
결과를 돌려줄 때도 **어느 문서에 했는지 always 같이 적는다.**

⚠ `revit_ping` 의 `doc_title` 도 **호출 시점의** 활성 문서다.
ping 과 exec 사이에 바뀔 수 있으니 ping 결과를 믿고 exec 하지 말 것.

---

## §1 exec 스코프 — import 한 이름이 함수 안에서 안 보인다

`revit_exec` 는 `exec(code, exec_globals, exec_locals)` 로 돌아서
모듈 최상단의 `import` 가 **함수 본문에서 NameError** 를 낸다.

```python
import Autodesk.Revit.DB as DB
globals()["doc"] = doc          # ★ 쓸 것을 전부 hoist 한다
globals()["uiapp"] = uiapp
globals()["DB"] = DB

def run():
    X = globals()["DB"]
    ...
result = run()
```

IronPython 2.7 이다 — `except Exception, e:` 문법을 쓰고,
`print()` 대신 `result = {...}` 로 돌려받는다.

---

## §2 트랜잭션이 필요한 것 / 아닌 것

| 하는 일 | 트랜잭션 |
|---|---|
| 조회 (`FilteredElementCollector`, 파라미터 읽기) | 필요 없음 |
| 요소 만들기·지우기·파라미터 쓰기 | **필요** |
| `PrintSetup.Save()` / `SaveAs()` | **필요** ← 안 하면 「document is not modifiable」 |
| `ViewSheetSetting.CurrentViewSheetSet = …` | **필요** ← 안 하면 「modify the model outside of transaction」 |
| `PrintManager` 의 나머지 속성(프린터·범위·파일명) | 필요 없음 |
| `SubmitPrint()` | **트랜잭션 밖에서** |

---

## §3 인쇄와 PDF — 여기서 제일 오래 헤맸다

### 3-1. ★ 설정을 고쳐도 저장하지 않으면 인쇄에 안 먹는다

```python
p = pm.PrintSetup.CurrentPrintSetting.PrintParameters
p.ZoomType = X.ZoomType.FitToPage      # ← 이것만 하면 SubmitPrint 는 옛 값을 쓴다
```

**반드시 트랜잭션 안에서 `ps.Save()`(또는 `SaveAs`) 를 부른다.**
저장하고 **되읽어 확인**한 뒤에 인쇄한다. 이걸 몰라서 같은 잘못된 PDF 를 네 번 뽑았다.

```python
t = X.Transaction(d, "인쇄설정")
t.Start()
p = ps.CurrentPrintSetting.PrintParameters
...
ps.Save()          # 「세션 내」 설정이면 Save 가 실패한다 → SaveAs(새 이름)
t.Commit()
p = ps.CurrentPrintSetting.PrintParameters      # ★ 되읽어 확인
```

### 3-2. 속성 순서가 있다

```python
p.PaperPlacement = X.PaperPlacementType.Margins   # ★ 먼저
p.MarginType     = X.MarginType.NoMargin          # 그 다음
```
Center 인 채로 MarginType 을 주면 **「The PaperPlacement is NOT Margins」** 로 거부된다.

`p.Zoom` 은 **ZoomType 이 Zoom 일 때만** 읽고 쓸 수 있다.
FitToPage 인 채로 읽으면 **「Current Zoom Type is NOT Zoom」** 예외가 나고,
로그 한 줄 때문에 인쇄 전체가 멈춘다. 로그에도 조건을 걸 것.

### 3-3. 용지 목록은 PrintManager 에 있다

```python
for sz in pm.PaperSizes:        # ← PrintSetup 아님. ps.PaperSizes 는 없다
    if "A3" in sz.Name:
        p.PaperSize = sz
```
프린터를 바꾸면 용지 객체도 새로 골라야 한다.

### 3-4. 가상 프린터의 버릇

| | 버릇 |
|---|---|
| Adobe PDF · MS Print to PDF | **가상 프린터라 `PrintToFile` 을 False 로 못 바꾼다** |
| Adobe PDF | `PrintToFileName` 의 **폴더를 무시**하고 **파일명만** 쓴다 — 마지막에 쓰던 폴더에 떨군다 |
| Adobe PDF | 같은 이름이 있으면 `…2.pdf`, `…3.pdf` 로 자동 증가 |
| MS Print to PDF | 저장 대화상자가 떠서 API 인쇄가 막힐 수 있다 |

⇒ **인쇄 뒤에는 파일명으로 찾지 말고, 관련 폴더들을 「최근 수정」으로 훑어 찾는다.**

### 3-5. 인쇄가 통째로 실패할 수 있다 — Distiller 글꼴 오류

```
HaansoftBatang not found, using Courier.
%%[ Error: typecheck; OffendingCommand: show ]%%   Stack: (性)
%%[ Warning: PostScript error. No PDF file produced. ]%%
```

**설치 안 된 글꼴이 Courier 로 대체되고, 그 글꼴에 없는 한자에서 PostScript 가 죽는다.**
파일이 아예 안 만들어진다. 오류는 Revit 이 아니라 **Distiller 로그**에만 나오므로,
파일이 안 생기면 사용자에게 그 로그를 확인해 달라고 한다.

### 3-6. 쓰이는 설정 (JK 표준, 2026-09-02 확정)

```
용지        A3 · Landscape
용지 배치   코너에서 간격 띄우기(Margins)      ← 「중앙」보다 크게 나온다
여백        여백 없음(NoMargin)
배율        용지에 맞춤(FitToPage)             ← Zoom 50% 로 두면 반만 나온다
색          컬러
숨김        범위상자 · 잘라내기 경계 · 참조/작업 평면 · 미참조 뷰 태그
프린터 기본 용지도 A3 로 맞춘다 (Adobe PDF 기본이 A4 였다)
```

⚠ **「중앙 배치」로 바꿔도 여백은 안 바뀐다.** 이 세션에서 둘 다 찍어 확인했다 —
좌우 여백이 다른 것은 배치 탓이 아니라 **제목블록 크기**(§4) 탓이었다.

---

## §4 ★ 제목블록 크기는 「테두리 선」이 아니라 「안에 든 것 전부의 바깥 범위」다

마천동 A1 제목블록이 **868.07 × 594** 로 인식됐다. 테두리 선은 정확히 841 × 594 였는데.

범인은 로고 옆 문자 하나였다.

```
TextNote 「Since 2001 / Jakin Archtecture」  유형 2.7mm_logo
기준점 x = 778.90 · 폭 89.67mm · 왼쪽 정렬
→ 오른쪽 끝 868.57.  시트 폭 = 868.57 − 0.50(테두리 왼쪽) = 868.07   ← 정확히 일치
```

A 계열 용지는 비가 **1 : 1.414** 다. 868.07/594 = 1.461 이라 비가 깨져서
A3 에 맞출 때 **우상단에만 여백이 남았다.** 폭을 60mm 로 줄이니 841 × 594 가 되고
출력이 90% → **93%**, 우측 여백 26.9 → **14.2mm** 로 좌우가 맞았다.

### 진단하는 법

```python
#  ⚠ get_BoundingBox(None) 은 문자·라벨을 안 잡는다 — 따로 훑어야 한다
for te in X.FilteredElementCollector(fd).OfClass(X.TextElement).WhereElementIsNotElementType():
    x, w = te.Coord.X * 304.8, te.Width * 304.8
    al = str(te.HorizontalAlignment)
    #  ★ 정렬에 따라 상자의 좌/우 끝이 다르다. 이걸 놓치면 엉뚱한 것을 범인으로 지목한다
    if   al == "Right":  L, R = x - w,       x
    elif al == "Center": L, R = x - w/2.0,   x + w/2.0
    else:                L, R = x,           x + w
```

프로젝트 쪽에서는 제목블록 **인스턴스**의 `SHEET_WIDTH`/`SHEET_HEIGHT` 로 읽는다
(유형·시트에서는 `None` 이 온다). `ViewSheet.Outline` 도 같은 값을 준다.

---

## §5 시트세트 다루기

```python
vss.CurrentViewSheetSet.Views = vs     # ★ 「현재 세트의 내용을 덮어쓴다」
vss.SaveAs(u"_tmp_A022")               # 새 이름으로 저장 (원본 세트는 살아남는다)
```

임시 세트는 **쓰고 나서 지운다.** 이름은 `_tmp_` 로 시작해 나중에 걸러내기 쉽게.

⚠ 위 두 줄은 트랜잭션 안에서만 된다. 그리고 실행 전에 **§0 문서 확인**을 반드시 한다 —
잘못된 문서에서 하면 남의 세트를 망가뜨린다.

---

## §6 그리고 지우기 — ID 목록으로만

드래프팅 뷰에 표를 그렸다가 다시 그릴 때:

```
그린 ID 를 json 에 남긴다  →  다음에 그 ID 로만 지운다
ID 로 하나도 못 지웠으면(파일이 롤백됐거나 손으로 지웠으면)
   폴백: 그 뷰 안의 TextNote · DetailCurve 를 전부 지운다
```

**좌표 범위로 지우지 않는다** — 사용자가 그 뷰에 넣은 다른 것을 같이 지운다.

`Viewport.GetBoxOutline()` 은 **같은 트랜잭션 안에서는 갱신 전 크기**를 준다.
커밋한 뒤에 다시 재고, 필요하면 두 번 반복한다.

---

## §7 결과를 눈으로 확인하는 법

### 7-1. Revit 에서 PNG

```python
opt = X.ImageExportOptions()
opt.ExportRange = X.ExportRange.SetOfViews
opt.SetViewsAndSheets(ids)          # ★ 뷰 Id 로 지정 — 이름으로 하면 동명 시트를 잡는다
opt.ImageResolution = X.ImageResolution.DPI_300
opt.PixelSize = 3508
opt.FilePath = base                 # 확장자·뷰이름이 뒤에 붙는다
d.ExportImage(opt)
```
**폴더가 없으면 「경로가 존재하지 않습니다」로 죽는다** — 미리 만들 것.

### 7-2. PDF 를 재는 법 (pymupdf)

```python
p = doc[0]
pix = p.get_pixmap(dpi=150)      # ★ rotation 이 적용된 「보이는 그대로」
#  어두운 픽셀의 행·열 범위를 찾아 내용 bbox 와 네 변 여백을 낸다
```

⚠ **`page.rotation` 을 무시하면 가로/세로가 뒤바뀌어 보인다.**
`p.rect` 는 회전을 반영하지만 `get_drawings()` 의 좌표는 회전 전이다.
이걸 놓쳐 「아래가 107mm 잘렸다」고 잘못 보고했다 — 실제로는 멀쩡했다.

유채색 개수로 컬러/흑백도 가른다 —
`dr['color']`/`dr['fill']` 의 RGB 세 성분이 서로 다르면 유채색.

---

## §8 하지 않는 것

```
사용자가 맞춰 놓은 배치·치수·그리드를 옮기지 않는다
「파악해봐」는 「고쳐라」가 아니다
모델을 바꾸는 것은 명시적으로 요청받았을 때만
바꾼 것은 되돌릴 수 있게 「무엇을 · 어떤 값에서 어떤 값으로」 남긴다
   ★ 원래 값을 기록하지 않고 고치면 되돌릴 수 없다 — 마천동에서 실제로 그랬다
사용자 파일을 저장하는 것도 요청받았을 때만
```

---

## §9 이어서 볼 것

```
10_Ai/9_Revit/system_가이드/MCP연동_가이드.md   ★연결·진단 원전 — 셋업 7단계 · 진단 사다리 · 함정 · 엔드포인트
10_Ai/9_Revit/system_표준/16_Revit 제어·인쇄 노하우.md    사람이 읽는 판
10_Ai/9_Revit/system_표준/15_설계개요 작성·삽입 가이드.md  설계개요 절차
.claude/skills/design-summary/SKILL.md     설계개요 AI 지침
```

### ★ 연결이 안 될 때 — 파일시스템을 뒤지기 전에 이 네 줄부터

| 증상 | 깨진 곳 | 조치 |
|---|---|---|
| HTTP **500** `RouteHandlerNotDefinedException` | Routes 는 살아있고 **익스텐션만 미등록** | `pyRevit_config.ini` 의 `userextensions` 확인 → 등록 → **전체 재시작** |
| **10054** ConnectionReset | reload·재시작 **진행 중** | 기다린다. 정상 과도기다 |
| 응답 없이 타임아웃 | 문서 로딩 중 · **모달 대화상자** | Revit 화면을 본다 |
| `ok:true` 인데 `doc_title: null` | 연결 정상, **문서 미개방** | 파일을 열면 된다 |

나머지 증상과 조치 상세는 **MCP연동_가이드 「진단 사다리」** 에 표로 있다. 세 줄만 옮겨 둔다.

```
★ 500 은 등록 문제, 10054 는 기다리면 되는 것 — 둘 다 「안 된다」로 보인다
★ 「껐다 켰는데 그대로」면 거의 항상 userextensions = []  ─ 등록 없는 재시작은 아무것도 안 바꾼다
   Select-String "$env:APPDATA\pyRevit\pyRevit_config.ini" -Pattern "userextensions"
★ 구글드라이브 파일은 hidden 이라 Get-ChildItem -Recurse 가 0건을 낸다.
   -Force 없이 「startup.py 가 없다」고 판정하지 말 것
```

> **2026-09-03** 이 사다리가 가이드에 이미 있었는데 안 읽고 `%APPDATA%`·G드라이브를
> 전수 재귀검색해 120초 타임아웃까지 갔다. 문서가 없어서가 아니라 **거기로 가는 길이
> 없어서** 생긴 손실이라, 그 길을 이 절로 냈다.
