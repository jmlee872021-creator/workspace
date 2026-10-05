# -*- coding: utf-8 -*-
"""**법률 문답 — 보내기 전 대조를 기계가 한다** (Stop 훅 · CLAUDE.md 「법률 문답」 3)

    (훅)  Stop 때 마지막 답을 읽는다. 법률 문답 답(맨 끝 `법.db 기준:` 줄)일 때만 잰다
    python3 .claude/hooks/법답대조.py --자가검사      법답케이스.yaml 의 답마다 걸려야 할 것이 걸리나
    python3 .claude/hooks/법답대조.py < 답.md        답 하나를 잰다 (표준입력)

재는 것 — 결론ㆍ단서 자리(첫 `◆` 앞)만:
  ① 「다.」 로 끝나는 문장마다 `← 「원문 글귀」` 가 붙었나
  ② 붙인 글귀가 아래 근거(◆ 부터) 안에 **글자 그대로** 있나 (빈칸ㆍ`…` 로 줄인 자리는 너그럽게)
  ③ 「안전하다」 「타당하다」 「권장」 「바람직」 같은 판단 말이 섞였나 — 그 말은 「실무 조언(법 판단 아님)」 에만
  ④ 근거(◆)가 하나라도 있나

걸리면 Stop 을 막고(exit 2) 걸린 줄을 알린다 — 고쳐서 다시 낸다. 한 번 막은 뒤(stop_hook_active)에는 막지 않고 알리기만 한다.
⚠ 이 잣대는 「글귀가 답 안의 근거에 있나」 까지다. 근거 인용이 법.db 와 글자까지 같은지는 재지 않는다.
"""
import json
import os
import re
import sys

#: 결론ㆍ단서에 있으면 안 되는 판단 말 — 「실무 조언(법 판단 아님)」 줄에서는 괜찮다
판단말 = ('안전하다', '안전합니다', '타당하다', '타당합니다', '권장', '바람직', '보는 것이 맞', '것으로 보인다', '것으로 판단')
#: 결론ㆍ단서가 아닌 줄의 머리 — 여기부터는 ①② 를 재지 않는다
안재는머리 = ('실무 조언', '원문이 정하지 않은', '⏸', '참고', '법.db 기준')
끝줄 = re.compile(r'법\.db 기준\s*[:：]')
글귀꼴 = re.compile(r'←\s*「([^」]+)」')
문장끝 = re.compile(r'다[.。](?:\*\*)?(?=\s|$|[←*])')


def 고르게(s):
    """견줄 때 — 굵게ㆍ빈칸ㆍ가운뎃점 꼴 차이는 무시한다"""
    s = s.replace('**', '').replace('·', 'ㆍ').replace('ㆍ', 'ㆍ')
    return re.sub(r'\s+', '', s)


def 재기(답):
    """걸린 것들을 글월 목록으로 낸다. 법률 문답 답이 아니면 None"""
    if not 끝줄.search(답):
        return None
    걸림 = []
    줄들 = 답.split('\n')
    근거첫 = next((i for i, l in enumerate(줄들) if l.lstrip().lstrip('>').lstrip().startswith('◆')), None)
    if 근거첫 is None:
        return ['④ 근거가 없다 — `◆ <법령> 제N조(제목) — 시행 YYYY-MM-DD` 머리와 법.db 원문 인용이 있어야 한다']
    근거 = 고르게('\n'.join(줄들[근거첫:]))
    for 번, 줄 in enumerate(줄들[:근거첫], 1):
        맨 = 줄.strip().lstrip('#>-* ').strip()
        if not 맨 or any(맨.startswith(h) or 맨.lstrip('*⚠ ').startswith(h) for h in 안재는머리):
            continue
        보기 = 맨[:60] + ('…' if len(맨) > 60 else '')
        for w in 판단말:
            if w in 줄:
                걸림.append('③ %d줄 「%s」 — 결론ㆍ단서에 판단 말 「%s」. 「실무 조언(법 판단 아님)」 으로 옮기거나 지운다' % (번, 보기, w))
                break
        글귀들 = 글귀꼴.findall(줄)
        끝수 = len(문장끝.findall(글귀꼴.sub('', 줄)))
        if 끝수 > len(글귀들):
            걸림.append('① %d줄 「%s」 — 문장 %d개에 원문 글귀 %d개. 문장마다 `← 「원문 글귀」` 를 단다 (없으면 「원문이 정하지 않은 것」 으로)' % (번, 보기, 끝수, len(글귀들)))
        for g in 글귀들:
            조각들 = [고르게(c) for c in re.split(r'…|\.\.\.', g) if 고르게(c)]
            없는 = [c for c in 조각들 if c not in 근거]
            if 없는:
                걸림.append('② %d줄 ← 「%s」 — 이 글귀가 아래 근거 인용에 없다. 근거에 원문을 싣거나 글귀를 근거 그대로 고친다' % (번, g[:50]))
    return 걸림


def 마지막답(입력):
    if 입력.get('last_assistant_message'):
        return 입력['last_assistant_message']
    길 = 입력.get('transcript_path')
    if not 길 or not os.path.exists(길):
        return ''
    글 = []
    for l in open(길, encoding='utf-8'):
        try:
            d = json.loads(l)
        except ValueError:
            continue
        m = d.get('message') or {}
        if d.get('type') == 'user':
            c = m.get('content')
            if isinstance(c, str) or (isinstance(c, list) and any(b.get('type') == 'text' for b in c if isinstance(b, dict))):
                글 = []      #: 사람의 새 물음 — 그 뒤 답만 본다
        elif d.get('type') == 'assistant' and isinstance(m.get('content'), list):
            글 += [b.get('text', '') for b in m['content'] if isinstance(b, dict) and b.get('type') == 'text']
    return '\n'.join(글)


def 훅(입력):
    걸림 = 재기(마지막답(입력))
    if not 걸림:
        return 0
    글 = '법률 문답 대조에 걸렸다 (CLAUDE.md 「법률 문답」 3) —\n' + '\n'.join('  ' + g for g in 걸림)
    if 입력.get('stop_hook_active'):
        print(글 + '\n  (한 번 막았으므로 이번엔 보낸다 — 사용자에게 걸린 줄을 알린다)', file=sys.stderr)
        return 0
    print(글, file=sys.stderr)
    return 2


def 자가검사():
    import yaml
    길 = os.path.join(os.path.dirname(os.path.abspath(__file__)), '법답케이스.yaml')
    케이스 = yaml.safe_load(open(길, encoding='utf-8'))
    틀림 = 0
    for k in 케이스:
        걸림 = 재기(k['답']) or []
        걸린갈래 = sorted({g[0] for g in 걸림})
        바람 = sorted(k.get('걸릴것', []))
        맞음 = 걸린갈래 == 바람 and all(any(w in g for g in 걸림) for w in k.get('글월', []))
        틀림 += not 맞음
        print('%s %s — 걸림 %s (바람 %s)' % ('✔' if 맞음 else '✗', k['이름'], ''.join(걸린갈래) or '없음', ''.join(바람) or '없음'))
        if not 맞음:
            for g in 걸림:
                print('     ' + g)
    print('%s 케이스 %d개 중 %d개 어긋남' % ('✔' if not 틀림 else '✗', len(케이스), 틀림))
    return 1 if 틀림 else 0


if __name__ == '__main__':
    if '--자가검사' in sys.argv:
        sys.exit(자가검사())
    데이터 = sys.stdin.read()
    try:
        입력 = json.loads(데이터)
    except ValueError:
        입력 = None
    if isinstance(입력, dict):
        sys.exit(훅(입력))
    걸림 = 재기(데이터)       #: 표준입력이 답 글 그대로
    print('법률 문답 답이 아니다 (맨 끝 `법.db 기준:` 줄 없음)' if 걸림 is None else
          ('\n'.join(걸림) or '✔ 걸린 것 없음'))
    sys.exit(1 if 걸림 else 0)
