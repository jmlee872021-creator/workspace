---
name: revit-map
description: Revit 을 MCP 로 붙여 읽고 쓰는 일의 상위 지도. 연결ㆍ진단, 요소ㆍ주석 쓰기, 패밀리, 설계개요 가운데 어느 하위 스킬을 어떤 차례로 쓸지 적는다. 「Revit 작업하자」, 「레빗 붙여줘」, 「Revit 에 그려줘」, 「어느 Revit 스킬 써야 돼」, 「Revit 스킬 정리」 같은 요청이면 하위 스킬보다 먼저 연다. 하위 스킬은 revit-control · revit-modeling · family-from-drawings · design-summary.
---

# Revit 지도 — 연결 → 쓰기 → 패밀리ㆍ설계개요

> 📄 사용자 (2026-09-17) : *"스킬들이 중구난방으로 분류되어있는거 같은데 스킬들을 잘 분류해야되는거 같아"* → Q1 ① 일감 다섯 묶음마다 지도 하나

**이 스킬은 얇게 둔다.** 절차ㆍAPI 함정은 하위 스킬에 있다.

## 1 · 일감별 차례

```
가. 무엇이든 Revit 에 닿기 전     revit-control — 붙었나(revit_ping) · 안 붙으면 여기부터
나. 요소ㆍ주석ㆍ뷰를 쓴다          revit-control → revit-modeling
다. 제조사 도면 → 패밀리           revit-control → family-from-drawings (→ revit-modeling 의 API 함정)
라. 설계개요 표를 도면에            design-summary (→ revit-modeling)
```
⚠ 이미지 원도를 캐드로 옮기는 일은 Revit 이 아니라 `cad-work-map`(drawing-analysis) 이다 — 옛 Revit 경로(대시보드 → Revit)는 보관했다.

## 3 · 하위 스킬 — 받는 것 · 내는 것 · 다음

| 스킬 | 하는 일 | 받는 것 | 내는 것 | 다음 |
|---|---|---|---|---|
| `revit-control` | MCP 연결ㆍ진단 · 트랜잭션ㆍ인쇄 규칙 | 열린 Revit | 붙은 상태 · 활성 문서 확인 | revit-modeling |
| `revit-modeling` | IronPython 으로 요소ㆍ주석ㆍ뷰 쓰기 · API 함정 | 붙은 Revit · 값(CSVㆍ표) | 요소 · 작업일지 | — |
| `family-from-drawings` | 제조사 CAD → Revit 패밀리 | DWGㆍDXF ㆍ카탈로그 | .rfa · 검산 | revit-modeling |
| `design-summary` | 설계개요(건축ㆍ층별ㆍ정화조ㆍ주차) 표 | 대장ㆍ모델 값 | 도면 위 표 | revit-modeling |

## 4 · 연계 규약

하위 스킬 제목 아래 머리 넉 줄 — 꼴은 `cad-work-map` 4절과 같다(`> 상위 : \`revit-map\`` · `> 앞 :` · `> 다음 :` · `> 넘기는 것 :`). 가이드검사 ⒅ 이 잰다.
