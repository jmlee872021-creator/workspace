# -*- coding: utf-8 -*-
"""**업무매뉴얼ㆍ지난 문답에서 「이미 정리해 둔 답」 찾기** — 법률 문답의 첫 손

    python3 tools/매뉴얼찾기.py 조경 면적                 낱말이 모두 든 항목ㆍQ (점수 차례)
    python3 tools/매뉴얼찾기.py 정북 일조 --몇 5
    python3 tools/매뉴얼찾기.py 용도변경 --갈래 용도변경    갈래만 (한국건축규정ㆍ용도변경ㆍ요소별ㆍ법률해설ㆍ문답)
    python3 tools/매뉴얼찾기.py --보기 3                    그 번호 항목을 통째로
    python3 tools/매뉴얼찾기.py --짓기                      색인을 새로 짓는다 (정본이 바뀌면 저절로도 짓는다)

⚠ 여기서 나온 글은 **근거가 아니다.** 사무소가 정리해 둔 길잡이다 —
  어느 조문을 볼지(열쇠)와 판단의 순서를 얻고, **근거는 법.db 원문**(10_Ai/1_법DB/찾기.py)으로 다시 본다.
  매뉴얼과 현행 원문이 다르면 답에 「⚠ 매뉴얼과 현행 조문이 다르다」 로 적는다.

낱말은 LIKE 로 찾는다 — 매뉴얼은 20MB 남짓이라 색인 없이도 0.1초대이고, 두 자 낱말(조경ㆍ높이)도 거짓 0건이 없다.
"""
import argparse
import glob
import os
import re
import sqlite3
import sys
import time

import yaml

뿌리 = os.path.expanduser(os.environ.get('JAKIN_DIR', '~/Jakin_workspace'))
색인길 = os.path.join(뿌리, '.매뉴얼색인.db')

#: (갈래, 찾을 자리) — 정본만. html 은 정본에서 뽑은 장이라 넣지 않는다
자리들 = [
    ('한국건축규정', '10_Ai/3_한국건축규정/system_표/체크판/**/*.yaml'),
    ('용도변경', '10_Ai/10_업무매뉴얼/12_용도변경_검토/*.yaml'),
    ('요소별', '10_Ai/10_업무매뉴얼/13_요소별_설계기준/*.yaml'),
    ('법률해설', '10_Ai/10_업무매뉴얼/11_법률검토/*/*.yaml'),
    ('문답', '10_Ai/2_묻고답하기/*.md'),
]
조각한도 = 3000      #: 이보다 긴 덩어리는 아래로 나눈다
제목칸 = ('번호', '이름', '장', '제목', '기준', '체크항목', '머리', '풀이', '글')

#: 열쇠 — `건축법 시행령|제27조|항2|호4` · `건축법 시행령|별표1`
열쇠꼴 = re.compile(r'([가-힣A-Za-z0-9ㆍ·()「」][가-힣A-Za-z0-9ㆍ·()「」 ]*?)\|(제\d+조(?:의\d+)?|별표\s?\d+(?:의\d+)?)((?:\|[항호목][\d가-힣]+(?:의\d+)?)*)')
#: 문답 md 의 근거 고리 — `[건축법 제42조(대지의 조경)]`
고리꼴 = re.compile(r'\[([^\[\]]+?) (제\d+조(?:의\d+)?)\(')


def 글로(x):
    """yaml 덩어리의 글만 줄로 모은다 (열쇠 칸 이름은 뺀다)"""
    if isinstance(x, dict):
        return '\n'.join(s for v in x.values() for s in [글로(v)] if s)
    if isinstance(x, list):
        return '\n'.join(s for v in x for s in [글로(v)] if s)
    return '' if x is None else str(x)


def 제목짓기(d):
    조각 = []
    for k in 제목칸:
        v = d.get(k)
        if isinstance(v, (str, int, float)) and str(v).strip():
            조각.append(str(v).strip().split('\n')[0][:80])
        if len(조각) == 2:
            break
    return ' · '.join(조각)


def 열쇠뽑기(글):
    본 = []
    for 법, 조, 끝 in 열쇠꼴.findall(글):
        k = '%s|%s%s' % (법.strip(), 조.replace(' ', ''), 끝)
        if k not in 본:
            본.append(k)
    for 법, 조 in 고리꼴.findall(글):
        k = '%s|%s' % (법.strip(), 조)
        if k not in 본:
            본.append(k)
    return 본


def yaml조각(x, 자리, 위제목):
    """한도 안이면 한 조각, 넘으면 아래로 나눈다 — 나눈 덩어리의 맨 글 칸들은 머리 조각으로 남긴다"""
    if isinstance(x, list):
        for i, v in enumerate(x):
            yield from yaml조각(v, '%s[%d]' % (자리, i), 위제목)
        return
    if not isinstance(x, dict):
        return
    제목 = 제목짓기(x) or 위제목
    글 = 글로(x)
    if len(글) <= 조각한도:
        if 글.strip():
            yield 자리, 제목, 글
        return
    머리 = '\n'.join(str(v) for v in x.values() if isinstance(v, (str, int, float)))
    if 머리.strip():
        yield 자리, 제목, 머리
    for k, v in x.items():
        if isinstance(v, (dict, list)):
            yield from yaml조각(v, '%s.%s' % (자리, k), 제목)


def md조각(글):
    """문답 md — Q 하나가 한 조각 (`### <a id="q-001"></a> Q-001 · 물음`)"""
    마디 = re.split(r'(?m)^> ### <a id="(q-[\w-]+)"></a> ', 글)
    for i in range(1, len(마디) - 1, 2):
        몸 = 마디[i + 1].split('\n---\n')[0]
        첫줄 = 몸.split('\n', 1)[0].strip()
        yield 마디[i], 첫줄[:120], 몸


def 정본들():
    for 갈래, 꼴 in 자리들:
        for 길 in sorted(glob.glob(os.path.join(뿌리, 꼴), recursive=True)):
            yield 갈래, 길


def 짓기():
    t = time.time()
    #: 짓는 이마다 따로 — 법준비.sh 가 짓는 중에 물음이 와 둘이 함께 지으면 한 이름을 서로 지워 `disk I/O error` 가 났다 (2026-10-05)
    임 = '%s.짓는중%d' % (색인길, os.getpid())
    c = sqlite3.connect(임)
    c.execute('create table 조각(번 integer primary key, 갈래, 파일, 자리, 제목, 본문, 열쇠, 장)')
    c.execute('create table 판(파일 primary key, 때)')
    n = 0
    for 갈래, 길 in 정본들():
        상대 = os.path.relpath(길, 뿌리)
        글 = open(길, encoding='utf-8').read()
        if 길.endswith('.md'):
            조각들 = md조각(글)
            장 = 상대
        else:
            try:
                d = yaml.load(글, Loader=getattr(yaml, 'CSafeLoader', yaml.SafeLoader))
            except yaml.YAMLError as e:
                print('  · yaml 을 못 읽음 — 건너뜀: %s (%s)' % (상대, str(e).split('\n')[0]))
                continue
            조각들 = yaml조각(d, '', os.path.splitext(os.path.basename(길))[0])
            html = os.path.splitext(길)[0] + '.html'
            장 = os.path.relpath(html, 뿌리) if os.path.exists(html) else 상대
        for 자리, 제목, 몸 in 조각들:
            c.execute('insert into 조각(갈래,파일,자리,제목,본문,열쇠,장) values (?,?,?,?,?,?,?)',
                      (갈래, 상대, 자리, 제목, 몸, '\n'.join(열쇠뽑기(몸)), 장))
            n += 1
        c.execute('insert into 판 values (?,?)', (상대, os.path.getmtime(길)))
    c.commit()
    c.close()
    os.replace(임, 색인길)
    print('✔ 매뉴얼 색인 — 조각 %d개 · %.1f초 · %s' % (n, time.time() - t, 색인길), file=sys.stderr)


def 낡았나():
    if not os.path.exists(색인길):
        return True
    c = sqlite3.connect(색인길)
    판 = dict(c.execute('select 파일, 때 from 판'))
    c.close()
    지금 = {os.path.relpath(길, 뿌리): os.path.getmtime(길) for _, 길 in 정본들()}
    return 지금 != 판


def 줄이기(본문, 낱말들, 폭=90):
    """낱말 둘레만 보인다"""
    본문 = re.sub(r'\s+', ' ', 본문)
    자리 = min((i for i in (본문.find(w) for w in 낱말들) if i >= 0), default=0)
    시작 = max(0, 자리 - 폭 // 3)
    return ('…' if 시작 else '') + 본문[시작:시작 + 폭 * 2] + ('…' if 시작 + 폭 * 2 < len(본문) else '')


def 찾기(낱말들, 몇, 갈래=None):
    c = sqlite3.connect(색인길)
    조건 = ' and '.join(['instr(제목||char(10)||본문, ?) > 0'] * len(낱말들))
    인자 = list(낱말들)
    if 갈래:
        조건 += ' and 갈래 = ?'
        인자.append(갈래)
    줄들 = c.execute('select 번, 갈래, 장, 자리, 제목, 본문, 열쇠 from 조각 where ' + 조건, 인자).fetchall()

    def 점수(r):
        제목, 본문 = r[4], r[5]
        #: 제목에 든 낱말은 무겁게 · 짧은 조각일수록 그 낱말이 중심이다
        return sum(5 * 제목.count(w) + min(본문.count(w), 5) for w in 낱말들) / (1 + len(본문) / 3000)
    줄들.sort(key=점수, reverse=True)
    print('「%s」 — 매뉴얼ㆍ문답 %d곳%s' % (' '.join(낱말들), len(줄들), ' (위 %d곳)' % 몇 if len(줄들) > 몇 else ''))
    for 번, 갈래, 장, 자리, 제목, 본문, 열쇠 in 줄들[:몇]:
        print('\n[%d] %s · %s' % (번, 갈래, 제목))
        print('    장: %s%s' % (장, '  ' + 자리 if 자리 and 갈래 == '문답' else ''))
        if 열쇠:
            k = 열쇠.split('\n')
            print('    조문: %s%s' % (' · '.join(k[:8]), ' 외 %d' % (len(k) - 8) if len(k) > 8 else ''))
        print('    %s' % 줄이기(본문, 낱말들))
    if not 줄들:
        print('  없음 — 매뉴얼에 정리된 답이 없다는 뜻일 뿐이다. 법.db 를 `찾기.py --두루` 로 본다')


def 보기(번):
    c = sqlite3.connect(색인길)
    r = c.execute('select 갈래, 장, 자리, 제목, 본문, 열쇠 from 조각 where 번=?', (번,)).fetchone()
    if not r:
        raise SystemExit('✗ %d 번 조각이 없다' % 번)
    print('[%d] %s · %s\n    장: %s %s\n    조문: %s\n' % (번, r[0], r[3], r[1], r[2], ' · '.join(r[5].split('\n'))))
    print(r[4])


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('낱말', nargs='*')
    p.add_argument('--몇', type=int, default=8)
    p.add_argument('--갈래', choices=[g for g, _ in 자리들])
    p.add_argument('--보기', type=int, metavar='번')
    p.add_argument('--짓기', action='store_true')
    a = p.parse_args()
    if a.짓기 or 낡았나():
        짓기()
    if a.보기 is not None:
        보기(a.보기)
    elif a.낱말:
        찾기(a.낱말, a.몇, a.갈래)
    elif not a.짓기:
        p.print_help()


if __name__ == '__main__':
    main()
