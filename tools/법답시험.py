# -*- coding: utf-8 -*-
"""**법률 문답 시험** — 규칙ㆍ훅ㆍ자료를 바꾼 뒤 답이 흐트러지지 않았나 (CLAUDE.md 「법률 문답」 6)

    python3 tools/법답시험.py --목록                       문제 목록
    python3 tools/법답시험.py --물음 T01 T05                그 문제들의 물음만 (풀이 에이전트에게 줄 것)
    python3 tools/법답시험.py T01 < 답.md                   답 하나를 채점
    python3 tools/법답시험.py --모두 <폴더>                 <폴더>/T01.md … 를 모두 채점 (없는 문제는 건너뜀)

채점 — 문제마다 네 가지:
  ㉠ 대조 훅(①~⑤)에 걸리나       .claude/hooks/법답대조.py 의 재기() 그대로
  ㉡ 꼭댈조가 근거 머리에 있나     ◆ Ⓐ … 줄에 「법령명 + 자리」 가 (빈칸 무시) 들어 있나
  ㉢ 결론 말이 결론ㆍ단서에 있나   첫 ◆ 앞
  ㉣ 금지 말이 없나               답 어디에도

⚠ 기계는 「흐트러졌나」 를 본다. 답이 법적으로 맞는지는 사람이 본다 — 어긋나면 그 답을 열어 본다.
⚠ 푸는 데 사용량이 든다(문제 하나에 답 하나). 규칙을 바꿨을 때 그 갈래 문제 몇 개만 고른다.
"""
import glob
import os
import re
import sys

import yaml

여기 = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(여기, '..', '.claude', 'hooks'))
import 법답대조  # noqa: E402

문제길 = os.path.join(여기, '법답시험.yaml')
머리꼴 = re.compile(r'^[\s>*\-]*(?:\*\*)?\s*[◆Ⓐ-Ⓩ]')


def 문제들():
    return {k['번호']: k for k in yaml.safe_load(open(문제길, encoding='utf-8'))}


def 붙여(s):
    return re.sub(r'\s+', '', s.replace('**', '').replace('·', 'ㆍ').replace('[', '').replace(']', ''))


def 채점(k, 답):
    """(맞음, 걸린 줄들)"""
    걸림 = []
    훅 = 법답대조.재기(답)
    if 훅 is None:
        return False, ['㉠ 법률 문답 답이 아니다 (맨 끝 `법.db 기준:` 줄 없음)']
    걸림 += ['㉠ ' + g for g in 훅]
    줄들 = 답.split('\n')
    머리들 = [붙여(re.sub(r'\]\([^)]*\)', '', l)) for l in 줄들 if 머리꼴.match(l) and not l.lstrip().startswith('>')]
    for 조건 in k.get('꼭댈조', []):
        후보 = [붙여(c) for c in str(조건).split(' | ')]
        if not any(c in h for c in 후보 for h in 머리들):
            걸림.append('㉡ 근거 머리에 「%s」 가 없다' % 조건)
    첫 = next((i for i, l in enumerate(줄들) if 머리꼴.match(l) and not l.lstrip().startswith('>')), len(줄들))
    결론자리 = 붙여('\n'.join(줄들[:첫]))
    for 조건 in k.get('결론', []):
        if not any(붙여(c) in 결론자리 for c in str(조건).split(' | ')):
            걸림.append('㉢ 결론ㆍ단서에 「%s」 가 없다' % 조건)
    for w in k.get('금지', []):
        if 붙여(w) in 붙여(답):
            걸림.append('㉣ 금지 말 「%s」 이 있다' % w)
    return not 걸림, 걸림


def 보이기(번호, 맞음, 걸림):
    print('%s %s' % ('✔' if 맞음 else '✗', 번호))
    for g in 걸림:
        print('     ' + g)


def main(a):
    문 = 문제들()
    if not a or a[0] == '--목록':
        for 번호, k in 문.items():
            print('%s  %s  (%s)' % (번호, k['물음'], k['출처']))
        return 0
    if a[0] == '--물음':
        for 번호 in a[1:] or 문:
            print('%s: %s' % (번호, 문[번호]['물음']))
        return 0
    if a[0] == '--모두':
        폴더, 틀림, 본 = a[1], 0, 0
        for 번호, k in 문.items():
            길 = os.path.join(폴더, 번호 + '.md')
            if not os.path.exists(길):
                continue
            맞음, 걸림 = 채점(k, open(길, encoding='utf-8').read())
            보이기(번호, 맞음, 걸림)
            본 += 1
            틀림 += not 맞음
        print('%s %d문제 중 %d개 어긋남' % ('✔' if not 틀림 else '✗', 본, 틀림))
        return 1 if 틀림 or not 본 else 0
    맞음, 걸림 = 채점(문[a[0]], sys.stdin.read())
    보이기(a[0], 맞음, 걸림)
    return 0 if 맞음 else 1


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
