#!/bin/bash
# 클라우드 세션에 한글 글꼴을 깐다 — 나눔고딕(보통ㆍ굵게)을 구글 폰트에서 받고, 「맑은 고딕」 을 나눔고딕으로 찍게 별칭을 둔다.
# apt(fonts-nanum)는 이 환경에서 막혀 있다 (2026-10-10). fonts.googleapis.com · fonts.gstatic.com 은 열려 있다.
# 해체계획서샘플쪽.py 는 맑은 고딕이 없으면 나눔고딕으로 글 폭을 잰다 — 찍는 글꼴(LibreOffice)도 같아야 자리가 맞는다.
set -uo pipefail
DIR="$HOME/.fonts"
mkdir -p "$DIR" "$HOME/.config/fontconfig"
for PAIR in "400 NanumGothic-Regular.ttf" "700 NanumGothic-Bold.ttf"; do
  set -- $PAIR
  [ -s "$DIR/$2" ] && [ "$(stat -c %s "$DIR/$2")" -gt 1000000 ] && continue
  # 옛 브라우저 이름으로 물어야 한글이 다 든 ttf 하나를 준다 (새 이름이면 조각난 woff2)
  URL=$(curl -sS --max-time 30 -A "Mozilla/4.0" "https://fonts.googleapis.com/css?family=Nanum+Gothic:$1&subset=korean" | grep -o 'https://[^)]*\.ttf' | head -1)
  [ -n "$URL" ] && curl -sS --max-time 120 -o "$DIR/$2" "$URL" || echo "한글 글꼴을 못 받았다 — $2"
done
cat > "$HOME/.config/fontconfig/fonts.conf" <<'X'
<?xml version="1.0"?>
<!DOCTYPE fontconfig SYSTEM "fonts.dtd">
<fontconfig>
  <!-- 맑은 고딕이 없는 클라우드 세션: ppt 의 「맑은 고딕」 을 나눔고딕으로 찍는다 (tools/한글글꼴.sh) -->
  <alias binding="same"><family>맑은 고딕</family><prefer><family>NanumGothic</family></prefer></alias>
  <alias binding="same"><family>Malgun Gothic</family><prefer><family>NanumGothic</family></prefer></alias>
</fontconfig>
X
fc-cache -f >/dev/null 2>&1
fc-match "맑은 고딕" | grep -q NanumGothic && echo "한글 글꼴 — 나눔고딕 (맑은 고딕 자리에)" || echo "한글 글꼴을 못 맞췄다 — bash tools/한글글꼴.sh"
