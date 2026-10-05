# -*- coding: utf-8 -*-
"""**⑤ 근거 인용이 법.db 글자 그대로인가** — 법답대조.py 가 부른다 (CLAUDE.md 「법률 문답」 3)

    python3 .claude/hooks/법답원문.py < 답.md      답 하나의 근거 인용만 잰다

답의 근거 자리에서 머리 줄(`◆ …` · `Ⓐ …` 처럼 동그라미 글자)마다 법령 이름을 읽고,
그 밑의 인용 줄(`> …`)이 그 법령 원문 안에 **글자 그대로** 있는지 본다.
  · 법령ㆍ시행령ㆍ시행규칙ㆍ조례 — 조(제목ㆍ항ㆍ호ㆍ목) + 별표 + 부칙
  · 행정규칙(고시ㆍ기준) — 조문 + 절 + 별표
  · 머리에 「옛 판」 「종전 판」 「법.db 밖」 — 법.db 의 옛조 + `0_원본/법령_옛판본/<법령명>/*.xml`
  · 「같은 법」 「같은 규칙」 「같은 영」 — 바로 위 머리의 법령
견줄 때는 빈칸ㆍ굵게ㆍ가운뎃점 꼴을 무시하고, `…` 로 줄인 자리는 조각마다 본다.

못 재는 것은 못 잰다 — 법.db 가 없거나, 옛 판 XML 을 아직 안 받았으면 **건너뛴다**(막지 않는다).
법령 이름을 법.db 에서 못 찾으면 걸린다 — 머리에 정식 법령명(또는 약칭)을 쓴다.
"""
import glob
import os
import re
import sqlite3
import sys
import unicodedata

뿌리 = os.path.expanduser(os.environ.get('JAKIN_DIR', '~/Jakin_workspace'))
DB길 = os.path.join(뿌리, '10_Ai', '1_법DB', '법.db')
옛판자리 = os.path.join(뿌리, '10_Ai', '1_법DB', '0_원본', '법령_옛판본')

머리꼴 = re.compile(r'^[\s>*\-]*(?:\*\*)?\s*([◆Ⓐ-Ⓩ])\s*(?:\*\*)?\s*(.+)$')
#: 법령 이름이 끝나는 자리 — 「 제61조」 「 [별표 1]」 「 별표 1」 「 부칙」 「 — 」
이름끝 = re.compile(r'\s+(?:제\d+조|\d+(?:\.\d+)+(?:\s|$)|\[?별표|부칙|[—–-]\s|\()|\s*[—–]|$')
옛판말 = ('옛 판', '종전 판', '종전판', '옛판', '법.db 밖')


def 씻(s):
    s = unicodedata.normalize('NFKC', s)      #: 한자 호환 글자(不 U+F967 ↔ 不 U+4E0D)를 하나로
    s = re.sub(r'<[^<>]*>', '', s.replace('\\<', '<').replace('\\>', '>'))   #: <개정 …> 꼬리표는 있든 없든 같게
    s = s.replace('**', '').replace('\\', '').replace('·', 'ㆍ').replace('・', 'ㆍ')
    return re.sub(r'\s+', '', s)


class 창고:
    def __init__(self):
        self.con = sqlite3.connect('file:%s?mode=ro' % DB길, uri=True)
        self.뭉치 = {}

    def 이름풀기(self, 이름):
        """머리에 적힌 이름 → (갈래, 키).  못 찾으면 None"""
        c = self.con
        for q in ('SELECT 법령키 FROM 법령 WHERE 법령키=?', 'SELECT 법령키 FROM 법령 WHERE 약칭=?',
                  "SELECT 법령키 FROM 법령 WHERE replace(법령키,' ','')=replace(?,' ','')"):
            r = c.execute(q, (이름,)).fetchone()
            if r:
                return ('법령', r[0])
        r = c.execute('SELECT 규칙키 FROM 행정규칙 WHERE 이름=? ORDER BY 시행일자 DESC', (이름,)).fetchone()
        if r:
            return ('행정규칙', r[0])
        return None

    def 글(self, 갈래, 키):
        if (갈래, 키) in self.뭉치:
            return self.뭉치[(갈래, 키)]
        c, 몸 = self.con, []
        if 갈래 == '법령':
            for 조키, 조이름, 조제목, 조내용 in c.execute(
                    'SELECT 조키,조이름,조제목,조내용 FROM 조 WHERE 법령키=? ORDER BY 차례', (키,)).fetchall():
                몸.append(조내용 or '%s(%s)' % (조이름, 조제목 or ''))
                for 항키, 항 in c.execute('SELECT 항키,항내용 FROM 항 WHERE 조키=? ORDER BY 차례', (조키,)).fetchall():
                    몸.append(항 or '')
                    for 호키, 호 in c.execute('SELECT 호키,호내용 FROM 호 WHERE 항키=? ORDER BY 차례', (항키,)).fetchall():
                        몸.append(호 or '')
                        몸 += [m or '' for m, in c.execute('SELECT 목내용 FROM 목 WHERE 호키=? ORDER BY 차례', (호키,))]
                몸.append('\n')
            몸 += [b or '' for b, in c.execute('SELECT 내용 FROM 별표 WHERE 법령키=? ORDER BY 차례', (키,))]
            몸 += [b or '' for b, in c.execute('SELECT 내용 FROM 부칙 WHERE 법령키=? ORDER BY 차례', (키,))]
        else:
            for t in ('행정규칙조문', '행정규칙절', '행정규칙별표'):
                몸 += [b or '' for b, in c.execute('SELECT 내용 FROM %s WHERE 규칙키=? ORDER BY 차례' % t, (키,))]
        self.뭉치[(갈래, 키)] = 씻(''.join(몸))
        return self.뭉치[(갈래, 키)]

    def 옛글(self, 이름):
        """옛 판 — 법.db 옛조 + 받아 둔 XML.  하나도 없으면 None (못 잰다)"""
        몸 = [b or '' for b, in self.con.execute(
            'SELECT o.조내용 FROM 옛조 o JOIN 판본 p ON p.판본키=o.판본키 WHERE p.법령명=?', (이름,))]
        for f in glob.glob(os.path.join(옛판자리, glob.escape(이름), '*.xml')):
            몸.append(re.sub(r'<!\[CDATA\[|\]\]>', '', open(f, encoding='utf-8', errors='ignore').read()))
        return 씻(''.join(몸)) if 몸 else None


def 갈림(조각, 원문):
    """원문과 어디서 갈라지나 — 원문에 있는 가장 긴 앞머리 뒤를 보인다"""
    아래, 위 = 0, len(조각)
    while 아래 < 위:
        k = (아래 + 위 + 1) // 2
        if 조각[:k] in 원문:
            아래 = k
        else:
            위 = k - 1
    if 아래 < 4:
        return ' (첫머리부터 다르다)'
    return ' (「…%s」 다음 「%s…」 부터 다르다)' % (조각[max(0, 아래 - 8):아래], 조각[아래:아래 + 10])


def 머리이름(머리, 앞이름):
    머리 = re.sub(r'\[([^\]]*)\]\([^)]*\)', r'\1', 머리).replace('**', '').lstrip('[ ')
    if 머리.startswith('「') and '」' in 머리:
        return 머리[1:머리.index('」')].strip()
    m = 이름끝.search(머리)
    이름 = 머리[:m.start()].strip(' *「」') if m else 머리.strip()
    if 이름.startswith('같은') and 앞이름:
        if re.fullmatch(r'같은\s*(?:법|규칙|영|고시|기준|조례)', 이름):
            return 앞이름
        m = re.fullmatch(r'같은\s*법\s*(시행령|시행규칙)', 이름)
        if m:
            return re.sub(r'\s*(?:시행령|시행규칙)$', '', 앞이름) + ' ' + m.group(1)
    return 이름


def 원문대조(답):
    """걸린 것들 (⑤ …).  법.db 가 없으면 빈 목록"""
    if not os.path.exists(DB길):
        return []
    try:
        창 = 창고()
    except sqlite3.Error:
        return []
    걸림, 앞이름, 지금 = [], None, None     #: 지금 = (머리 보기, 뭉친 원문 | None=못 잰다 | '?'=이름 못 찾음)
    for 번, 줄 in enumerate(답.split('\n'), 1):
        m = 머리꼴.match(줄)
        if m and not 줄.lstrip().startswith('>'):
            머리 = m.group(2).strip()
            이름 = 머리이름(머리, 앞이름)
            옛 = any(w in 머리 for w in 옛판말)
            if 옛:
                지금 = (머리[:40], 창.옛글(이름))
            else:
                풀 = 창.이름풀기(이름)
                if 풀:
                    지금 = (머리[:40], 창.글(*풀))
                else:          #: 이름을 못 찾았다 — 밑에 인용이 붙을 때만 걸린다 (「Ⓒ 건축조례 — 열지 않았다」 같은 줄은 괜찮다)
                    지금 = (머리[:40], '?', 번, 이름)
            앞이름 = 이름
            continue
        s = 줄.strip()
        if s and not s.startswith(('>', '↳')):
            지금 = None          #: 인용은 머리 바로 밑에 잇달아 온다 — 다른 글이 끼면 그 머리의 인용은 끝났다
            continue
        if not s.startswith('>') or 지금 is None or 지금[1] is None:
            continue
        인용 = s.lstrip('>').strip()
        if 인용.startswith(('↳', '```')):
            continue
        if 지금[1] == '?':
            걸림.append('⑤ %d줄 「%s」 — 법령 이름 「%s」 을 법.db 에서 못 찾아 인용을 잴 수 없다. 머리에 정식 법령명(또는 약칭)을 쓴다'
                      % (지금[2], 지금[0], 지금[3]))
            지금 = None
            continue
        조각들 = [씻(c) for c in re.split(r'…|\.\.\.', 인용)]
        없는 = [c for c in 조각들 if len(c) >= 4 and c not in 지금[1]]
        if 없는:
            걸림.append('⑤ %d줄 「%s」 — 이 인용이 「%s」 원문(법.db)에 글자 그대로 없다%s. 찾기.py 출력에서 그대로 복사한다'
                      % (번, 인용[:30], 지금[0], 갈림(없는[0], 지금[1])))
    return 걸림


if __name__ == '__main__':
    걸림 = 원문대조(sys.stdin.read())
    print('\n'.join(걸림) or '✔ 근거 인용이 모두 법.db 원문과 같다')
    sys.exit(1 if 걸림 else 0)
