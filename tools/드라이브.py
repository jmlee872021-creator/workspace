# -*- coding: utf-8 -*-
"""**클라우드 세션 ↔ 구글 드라이브 Jakin_workspace** — 받기 · 견주기 · 올리기

    python3 tools/드라이브.py 받기                         뿌리 전체 (큰 파일ㆍ되돌림 사본은 뺀다)
    python3 tools/드라이브.py 받기 02_프로젝트/system_만들기  그 폴더만
    python3 tools/드라이브.py 받기 --큰것 10_Ai/1_법DB/법.db  큰 파일도 이름을 대면 받는다
    python3 tools/드라이브.py 받기 --글만 10_Ai/10_업무매뉴얼  그림ㆍPDFㆍ한글 파일은 빼고 (32분 → 몇 분)
    python3 tools/드라이브.py 받기 10_Ai/2_묻고답하기 --꼴 "*.md"   그 꼴의 파일만
    python3 tools/드라이브.py 견주기                       받은 뒤 바뀐 것ㆍ새로 생긴 것만 보인다 (아무것도 안 올린다)
    python3 tools/드라이브.py 올리기                       올릴 것을 보이기만 한다
    python3 tools/드라이브.py 올리기 --정말                 그때 올린다 (사용자가 「올려」 라고 했을 때만)
    python3 tools/드라이브.py 세기 02_프로젝트              아래 폴더마다 파일 수ㆍ크기를 센다 (아무것도 안 바꾼다)
    python3 tools/드라이브.py 복사 <옛 폴더> <새 폴더>        폴더째 사본을 드라이브 안에서 짓는다 — 보이기만
    python3 tools/드라이브.py 복사 --표 사본표.tsv --정말     표(옛 자리 ⇥ 새 자리)대로 그때 짓는다

열쇠 — 클라우드 환경 「Default」 의 환경변수 GDRIVE_CLIENT_ID · GDRIVE_CLIENT_SECRET · GDRIVE_REFRESH_TOKEN.
(보안 비밀번호를 환경변수 대신 「API 자격 증명」 Basic 머리글로 붙여도 돈다.) 다시 세우는 법: 드라이브 「구글드라이브 api연결 (claude)」 폴더의 클라우드_드라이브연결.md
사용자 본인 계정의 열쇠라 새 파일도 사용자 소유로 생긴다.

⚠ 지우지 않는다 — 드라이브에서도, 이 컴퓨터에서도. 바뀐 파일은 드라이브의 「버전」 에 옛 판이 남는다.
⚠ 받은 뒤 드라이브 쪽이 따로 바뀌었으면 그 파일은 올리지 않고 멈춘다 (덮어쓰기 막음).
"""
import argparse
import concurrent.futures
import fnmatch
import hashlib
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

뿌리ID = os.environ.get('JAKIN_ROOT_ID', '1vqymQihNC5ihmg99mxVmjsy4Y3QpmtLZ')   #: 드라이브 Jakin_workspace
여기 = os.path.expanduser(os.environ.get('JAKIN_DIR', '~/Jakin_workspace'))
목록이름 = '.드라이브목록.json'
폴더꼴 = 'application/vnd.google-apps.folder'
바로가기꼴 = 'application/vnd.google-apps.shortcut'
API = 'https://www.googleapis.com/drive/v3/files'
올림API = 'https://www.googleapis.com/upload/drive/v3/files'
#: `구글드라이브 api연결*` — 열쇠 파일(JSON 등)이 있을 수 있는 폴더라 받지 않는다
뺄것 = ['되돌림_*', '__pycache__', '*.pyc', '.git', 'desktop.ini', '~$*', '구글드라이브 api연결*', 목록이름, 목록이름 + '.*',
       '.매뉴얼색인.db*', '.법준비됨']   #: 이 컴퓨터에서만 쓰는 것 — 올리지 않는다
큰것MB = 300
#: `받기 --글만` 이 빼는 꼴 — 도구ㆍ매뉴얼 글(html·js·json·yaml·md·py·csv·db …)만 받으면 파일 수가 1/4 로 준다
글아닌것 = {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tif', '.tiff', '.webp', '.heic', '.pdf', '.hwp', '.hwpx',
          '.dwg', '.dxf', '.zip', '.7z', '.rar', '.mp4', '.mov', '.psd', '.ai', '.pptx', '.ppt', '.rvt', '.rfa', '.$$$'}


def 열쇠():
    """refresh token → 한 시간짜리 access token.

    보안 비밀번호는 두 길로 받는다 —
      ① 환경변수 GDRIVE_CLIENT_ID + GDRIVE_CLIENT_SECRET (몸에 싣는다)
      ② 환경의 「API 자격 증명」 이 oauth2.googleapis.com 에 Basic(클라이언트 ID : 보안 비밀번호) 머리글을
         붙여 준다 — 이 세션은 값을 못 본다. 이때는 몸에 refresh token 만 싣는다.
    """
    if not os.environ.get('GDRIVE_REFRESH_TOKEN'):
        raise SystemExit('✗ 드라이브 열쇠가 없다 — 환경변수 GDRIVE_REFRESH_TOKEN 을 넣어야 한다')
    몸 = {'refresh_token': os.environ['GDRIVE_REFRESH_TOKEN'], 'grant_type': 'refresh_token'}
    if os.environ.get('GDRIVE_CLIENT_SECRET'):
        몸.update(client_id=os.environ.get('GDRIVE_CLIENT_ID', ''), client_secret=os.environ['GDRIVE_CLIENT_SECRET'])
    try:
        with urllib.request.urlopen('https://oauth2.googleapis.com/token', urllib.parse.urlencode(몸).encode(), timeout=60) as r:
            return json.load(r)['access_token']
    except urllib.error.HTTPError as e:
        글 = e.read()[:300].decode('utf-8', 'replace')
        if 'invalid_grant' in 글:
            raise SystemExit('✗ 열쇠가 끊겼다(7일 지남 또는 취소됨) — OAuth Playground 에서 Refresh token 을 다시 받아야 한다\n  ' + 글)
        if 'invalid_client' in 글 or 'client_secret' in 글:
            raise SystemExit('✗ 보안 비밀번호가 안 실렸다 — 「API 자격 증명」(oauth2.googleapis.com, Basic) 을 확인\n  ' + 글)
        raise


class 드라이브:
    def __init__(self):
        self.표 = 열쇠()

    def 부름(self, 주소, 방법='GET', 몸=None, 머리=None, 길이=None):
        h = {'Authorization': 'Bearer ' + self.표}
        h.update(머리 or {})
        if 길이 is not None:
            h['Content-Length'] = str(길이)
        for 번 in range(8):
            q = urllib.request.Request(주소, data=몸, method=방법, headers=h)
            try:
                return urllib.request.urlopen(q, timeout=600)
            except urllib.error.HTTPError as e:
                글 = e.read()
                e.read = lambda *_: 글
                #: 구글은 1분에 부를 수 있는 횟수를 막는다(403 Quota exceeded · rateLimitExceeded · 429) — 기다렸다 다시 부른다
                if 번 < 7 and (e.code in (429, 500, 502, 503, 504)
                              or (e.code == 403 and any(x in 글 for x in (b'Quota exceeded', b'ateLimitExceeded')))):
                    time.sleep(min(60, 2 ** 번 * 2))
                    continue
                raise

    def 목록(self, 부모):
        파일, 쪽 = [], None
        while True:
            물음 = {'q': "'%s' in parents and trashed=false" % 부모, 'pageSize': 1000,
                  'fields': 'nextPageToken,files(id,name,mimeType,md5Checksum,size,modifiedTime,shortcutDetails(targetId))'}
            if 쪽:
                물음['pageToken'] = 쪽
            with self.부름(API + '?' + urllib.parse.urlencode(물음)) as r:
                d = json.load(r)
            파일 += d.get('files', [])
            쪽 = d.get('nextPageToken')
            if not 쪽:
                return 파일

    def 받기(self, fid, 길, 크기=None, 지문=None):
        """끊기면 받은 데까지 이어 받는다 (Range).  크기ㆍmd5 가 드라이브와 맞아야 제자리에 놓는다.

        연결이 중간에 끊겨도 read() 가 빈 값을 주며 조용히 끝날 수 있다 —
        그래서 「다 받았다」 는 크기와 md5 로만 판단한다.
        """
        os.makedirs(os.path.dirname(길), exist_ok=True)
        임 = 길 + '.받는중'
        if os.path.exists(임):
            os.remove(임)
        for 번 in range(6):
            있음 = os.path.getsize(임) if os.path.exists(임) else 0
            if 크기 and 있음 >= 크기:
                break
            try:
                머리 = {'Range': 'bytes=%d-' % 있음} if 있음 else None
                with self.부름('%s/%s?alt=media' % (API, fid), 머리=머리) as r:
                    #: 서버가 Range 를 무시하고 처음부터 주면(200) 덮어쓴다
                    with open(임, 'ab' if 있음 and r.status == 206 else 'wb') as f:
                        while True:
                            b = r.read(1 << 20)
                            if not b:
                                break
                            f.write(b)
            except (urllib.error.URLError, OSError) as e:
                print('  · 끊김 (%s) — 이어 받는다: %s' % (e, 길), flush=True)
                time.sleep(2 ** 번)   #: 드라이브 「분당 요청 한도」 에 걸렸을 때도 숨을 고른다
            if not 크기:
                break
        받음 = os.path.getsize(임) if os.path.exists(임) else 0
        if 크기 and 받음 != 크기:
            raise SystemExit('✗ 다 못 받음 (%d / %d 바이트): %s' % (받음, 크기, 길))
        if 지문 and md5(임) != 지문:
            os.remove(임)
            raise SystemExit('✗ md5 가 드라이브와 다르다 — 받은 것을 버렸다: %s' % 길)
        os.replace(임, 길)

    def 정보(self, fid):
        with self.부름('%s/%s?fields=id,md5Checksum,modifiedTime,size' % (API, fid)) as r:
            return json.load(r)

    def 올리기(self, 길, fid=None, 부모=None):
        """fid 가 있으면 그 파일의 새 판, 없으면 부모 폴더에 새 파일 — 이어올리기(큰 파일도 된다)"""
        메타 = {} if fid else {'name': os.path.basename(길), 'parents': [부모]}
        주소 = ('%s/%s' % (올림API, fid) if fid else 올림API) + '?uploadType=resumable&fields=id,md5Checksum,modifiedTime'
        with self.부름(주소, 'PATCH' if fid else 'POST', json.dumps(메타).encode(),
                      {'Content-Type': 'application/json; charset=UTF-8'}) as r:
            갈곳 = r.headers['Location']
        with open(길, 'rb') as f:
            q = urllib.request.Request(갈곳, data=f, method='PUT',
                                       headers={'Content-Length': str(os.path.getsize(길))})
            with urllib.request.urlopen(q, timeout=3600) as r:
                return json.load(r)

    def 폴더짓기(self, 이름, 부모):
        몸 = json.dumps({'name': 이름, 'mimeType': 폴더꼴, 'parents': [부모]}).encode()
        with self.부름(API + '?fields=id', 'POST', 몸, {'Content-Type': 'application/json; charset=UTF-8'}) as r:
            return json.load(r)['id']

    def 사본(self, x, 부모):
        """드라이브 서버 안에서 복사한다 (내려받지 않는다).  바로가기는 같은 곳을 가리키는 새 바로가기를 짓는다"""
        if x['mimeType'] == 바로가기꼴:
            몸 = {'name': x['name'], 'mimeType': 바로가기꼴, 'parents': [부모],
                 'shortcutDetails': {'targetId': x.get('shortcutDetails', {}).get('targetId')}}
            주소 = API + '?fields=id,md5Checksum'
        else:
            몸 = {'name': x['name'], 'parents': [부모]}
            주소 = '%s/%s/copy?fields=id,md5Checksum' % (API, x['id'])
        with self.부름(주소, 'POST', json.dumps(몸).encode(), {'Content-Type': 'application/json; charset=UTF-8'}) as r:
            return json.load(r)


def 빼나(이름):
    return any(fnmatch.fnmatch(이름, p) for p in 뺄것)


def md5(길):
    h = hashlib.md5()
    with open(길, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def 목록읽기():
    길 = os.path.join(여기, 목록이름)
    if os.path.exists(길):
        with open(길, encoding='utf-8') as f:
            return json.load(f)
    return {'파일': {}, '폴더': {'': 뿌리ID}}


def 목록쓰기(m):
    """받기 둘이 함께 돌아도 서로의 줄을 지우지 않게 — 잠그고, 그새 쓰인 목록과 합쳐 쓴다"""
    import fcntl
    os.makedirs(여기, exist_ok=True)
    길 = os.path.join(여기, 목록이름)
    with open(길 + '.잠금', 'w') as 잠금:
        fcntl.flock(잠금, fcntl.LOCK_EX)
        지금 = 목록읽기()
        for 칸 in ('파일', '폴더'):
            지금[칸].update(m[칸])
        with open(길 + '.쓰는중', 'w', encoding='utf-8') as f:
            json.dump(지금, f, ensure_ascii=False, indent=0)
        os.replace(길 + '.쓰는중', 길)


def 경로id(d, m, 상대):
    """`a/b/c` → 드라이브 id. 목록에 없으면 위에서부터 이름으로 찾는다"""
    if 상대 in m['폴더'] or 상대 in m['파일']:
        return m['폴더'].get(상대) or m['파일'][상대]['id'], 상대 in m['폴더']
    부모, 지금 = 뿌리ID, ''
    조각 = [x for x in 상대.split('/') if x]
    for i, 이름 in enumerate(조각):
        맞음 = [x for x in d.목록(부모) if x['name'] == 이름]
        if not 맞음:
            raise SystemExit('✗ 드라이브에 없다: %s' % '/'.join(조각[:i + 1]))
        지금 = (지금 + '/' + 이름).lstrip('/')
        if 맞음[0]['mimeType'] == 폴더꼴:
            m['폴더'][지금] = 부모 = 맞음[0]['id']
        else:
            return 맞음[0], False
    return 부모, True


def 받기(args):
    d, m = 드라이브(), 목록읽기()
    할일, 큰것뺌, 글만뺌 = [], [], [0]

    def 훑기(fid, 상대):
        """폴더 한 층씩 — 한 층의 폴더들은 여럿이 한꺼번에 훑는다 (폴더가 천 개 넘으면 한 줄로는 10분 걸린다)"""
        층 = [(fid, 상대)]
        with concurrent.futures.ThreadPoolExecutor(8) as 일꾼:
            while 층:
                다음 = []
                for (_, 위), 안 in zip(층, 일꾼.map(lambda 칸: d.목록(칸[0]), 층)):
                    for x in 안:
                        이름 = x['name'].replace('/', '_')
                        길 = (위 + '/' + 이름).lstrip('/')
                        if 빼나(이름) and not args.전부:
                            continue
                        if x['mimeType'] == 폴더꼴:
                            m['폴더'][길] = x['id']
                            다음.append((x['id'], 길))
                        elif x['mimeType'].startswith('application/vnd.google-apps'):
                            continue          #: 구글 문서ㆍ시트ㆍ바로가기는 파일이 아니다
                        else:
                            넣기(x, 길)
                층 = 다음

    def 넣기(x, 길):
        if args.꼴 and not any(fnmatch.fnmatch(os.path.basename(길), p) for p in args.꼴):
            return
        크기 = int(x.get('size') or 0)
        if args.글만 and os.path.splitext(길)[1].lower() in 글아닌것:
            글만뺌[0] += 1
            return
        if 크기 > 큰것MB * 2 ** 20 and not args.큰것:
            큰것뺌.append((길, 크기))
            return
        로컬 = os.path.join(여기, 길)
        if os.path.exists(로컬) and x.get('md5Checksum') and md5(로컬) == x['md5Checksum']:
            m['파일'][길] = {'id': x['id'], 'md5': x['md5Checksum'], '때': x['modifiedTime']}
            return
        할일.append((x, 길))

    for 상대 in (args.경로 or ['']):
        상대 = 상대.strip('/')
        if not 상대:
            훑기(뿌리ID, '')
            continue
        x, 폴더인가 = 경로id(d, m, 상대)
        if 폴더인가:
            훑기(x, 상대)
        else:
            if isinstance(x, str):
                x = dict(d.정보(x), id=x, name=os.path.basename(상대))
            넣기(x, 상대)

    print('받을 것 %d개 …' % len(할일), flush=True)

    def 하나(일):
        x, 길 = 일
        d.받기(x['id'], os.path.join(여기, 길), int(x.get('size') or 0) or None, x.get('md5Checksum'))
        return 길, {'id': x['id'], 'md5': x.get('md5Checksum'), '때': x['modifiedTime']}

    with concurrent.futures.ThreadPoolExecutor(8) as 일꾼:
        for i, (길, 값) in enumerate(일꾼.map(하나, 할일), 1):
            m['파일'][길] = 값
            if i % 200 == 0:
                print('  %d / %d' % (i, len(할일)), flush=True)
    with open(os.path.join(여기, '.뿌리'), 'a'):
        pass
    목록쓰기(m)
    print('✔ 받음 — %s (파일 %d개 목록에 있음)' % (여기, len(m['파일'])))
    if 글만뺌[0]:
        print('  · --글만 — 그림ㆍPDFㆍ한글ㆍ캐드ㆍ압축 %d개는 안 받음' % 글만뺌[0])
    for 길, 크기 in 큰것뺌:
        print('  · 큰 파일이라 안 받음 (%.0f MB): %s — 필요하면 `받기 --큰것 %s`' % (크기 / 2 ** 20, 길, 길))


def 바뀐것(m):
    바뀜, 새것 = [], []
    for 위, 폴더들, 파일들 in os.walk(여기):
        폴더들[:] = [x for x in 폴더들 if not 빼나(x)]
        for 이름 in 파일들:
            if 빼나(이름) or 이름 == '.뿌리' or 이름.endswith('.받는중'):
                continue
            길 = os.path.relpath(os.path.join(위, 이름), 여기).replace(os.sep, '/')
            있던 = m['파일'].get(길)
            if not 있던:
                새것.append(길)
            elif md5(os.path.join(위, 이름)) != 있던['md5']:
                바뀜.append(길)
    return sorted(바뀜), sorted(새것)


def 견주기(args):
    바뀜, 새것 = 바뀐것(목록읽기())
    for 길 in 바뀜:
        print('  바뀜  ', 길)
    for 길 in 새것:
        print('  새것  ', 길)
    print('바뀜 %d · 새것 %d' % (len(바뀜), len(새것)))
    return 바뀜, 새것


def 올리기(args):
    m = 목록읽기()
    바뀜, 새것 = 견주기(args)
    if not args.정말:
        print('\n(보이기만 했다 — 올리려면 --정말)')
        return
    d, 막힘 = 드라이브(), []
    for 길 in 바뀜:
        있던 = m['파일'][길]
        지금 = d.정보(있던['id'])
        if 지금.get('md5Checksum') != 있던['md5']:
            막힘.append(길)          #: 받은 뒤 드라이브 쪽이 바뀌었다 — 덮지 않는다
            continue
        r = d.올리기(os.path.join(여기, 길), fid=있던['id'])
        m['파일'][길] = {'id': r['id'], 'md5': r['md5Checksum'], '때': r['modifiedTime']}
        print('  ✔ 새 판', 길)
    본것 = {}          #: 부모 id → 드라이브의 그 폴더 안 목록 (이번 올리기 동안만)

    def 안에(부모, 이름, 폴더인가):
        """드라이브의 부모 아래 같은 이름(폴더 또는 파일)이 이미 있으면 그 id — 일부만 받은 뒤 올려도 겹쳐 짓지 않는다"""
        if 부모 not in 본것:
            본것[부모] = d.목록(부모)
        for x in 본것[부모]:
            if x['name'].replace('/', '_') == 이름 and (x['mimeType'] == 폴더꼴) == 폴더인가:
                return x['id']

    for 길 in 새것:
        위 = os.path.dirname(길)
        조각, 지금 = [x for x in 위.split('/') if x], ''
        for 이름 in 조각:
            다음 = (지금 + '/' + 이름).lstrip('/')
            if 다음 not in m['폴더']:
                있는것 = 안에(m['폴더'][지금], 이름, True)
                m['폴더'][다음] = 있는것 or d.폴더짓기(이름, m['폴더'][지금])
                if not 있는것:
                    본것[m['폴더'][다음]] = []
            지금 = 다음
        if 안에(m['폴더'][지금], os.path.basename(길), False):
            막힘.append(길)          #: 드라이브엔 이미 있는데 받지 않은 파일 — 새로 지으면 겹치고, 덮으면 그쪽 판을 잃는다
            continue
        r = d.올리기(os.path.join(여기, 길), 부모=m['폴더'][지금])
        m['파일'][길] = {'id': r['id'], 'md5': r['md5Checksum'], '때': r['modifiedTime']}
        print('  ✔ 새 파일', 길)
    목록쓰기(m)
    for 길 in 막힘:
        if 길 in m['파일']:
            print('  ✘ 안 올림 — 받은 뒤 드라이브에서 따로 바뀌었다:', 길)
        else:
            print('  ✘ 안 올림 — 드라이브에 같은 이름 파일이 이미 있다 (받지 않은 파일, 먼저 `받기 %s` 로 받아 견준다): %s' % (길, 길))
    if 막힘:
        sys.exit(1)


def 다훑기(d, fid, 상대=''):
    """폴더 아래를 끝까지 — (폴더 상대경로 목록, [(파일, 상대경로)]).  한 층의 폴더들은 8 이 한꺼번에 훑는다"""
    폴더들, 파일들, 층 = [], [], [(fid, 상대)]
    with concurrent.futures.ThreadPoolExecutor(8) as 일꾼:
        while 층:
            다음 = []
            for (_, 위), 안 in zip(층, 일꾼.map(lambda 칸: d.목록(칸[0]), 층)):
                for x in 안:
                    길 = (위 + '/' + x['name'].replace('/', '_')).lstrip('/')
                    if x['mimeType'] == 폴더꼴:
                        폴더들.append(길)
                        다음.append((x['id'], 길))
                    else:
                        파일들.append((x, 길))
            층 = 다음
    return 폴더들, 파일들


def 크기글(b):
    for 단위 in ('B', 'KB', 'MB', 'GB'):
        if b < 1024 or 단위 == 'GB':
            return ('%.0f %s' if 단위 in ('B', 'KB') else '%.1f %s') % (b, 단위)
        b /= 1024


def 세기(args):
    """폴더마다 바로 아래 칸의 파일 수ㆍ크기 — 사본 만들기 표의 밑감"""
    d, m = 드라이브(), 목록읽기()
    for 상대 in (args.경로 or ['']):
        상대 = 상대.strip('/')
        fid, 폴더인가 = 경로id(d, m, 상대) if 상대 else (뿌리ID, True)
        if not 폴더인가:
            raise SystemExit('✗ 폴더가 아니다: %s' % 상대)
        _, 파일들 = 다훑기(d, fid)
        칸 = {}
        for x, 길 in 파일들:
            머리 = 길.split('/')[0] if '/' in 길 else '(맨 위 낱 파일)'
            n, b = 칸.get(머리, (0, 0))
            칸[머리] = (n + 1, b + int(x.get('size') or 0))
        print('\n## %s — 파일 %d개 · %s' % (상대 or 'Jakin_workspace', len(파일들),
                                        크기글(sum(int(x.get('size') or 0) for x, _ in 파일들))))
        print('칸\t파일 수\t크기')
        for 머리 in sorted(칸):
            print('%s\t%d\t%s' % (머리, 칸[머리][0], 크기글(칸[머리][1])))


def 폴더보장(d, m, 상대, 지음):
    """`a/b/c` 폴더 id — 없는 층은 짓는다(지음=True 일 때만, 아니면 None)"""
    부모, 지금 = 뿌리ID, ''
    for 이름 in [x for x in 상대.split('/') if x]:
        지금 = (지금 + '/' + 이름).lstrip('/')
        if 지금 not in m['폴더']:
            있음 = [x for x in d.목록(부모) if x['name'] == 이름 and x['mimeType'] == 폴더꼴]
            if 있음:
                m['폴더'][지금] = 있음[0]['id']
            elif 지음:
                m['폴더'][지금] = d.폴더짓기(이름, 부모)
            else:
                return None
        부모 = m['폴더'][지금]
    return 부모


def 복사(args):
    """옛 폴더를 새 자리에 그대로 사본으로 짓는다 — 원본은 건드리지 않는다.

    드라이브엔 폴더째 복사가 없다: 폴더는 새로 짓고, 파일은 하나씩 서버 안에서 복사한다(하나에 약 4초 → 8 이 함께).
    새 자리에 같은 이름이 이미 있으면 건너뛴다 — 끊겼을 때 같은 줄을 다시 돌리면 이어서 한다.
    """
    if args.표:
        쌍 = []
        with open(args.표, encoding='utf-8') as f:
            for 줄 in f:
                칸 = [x.strip() for x in 줄.rstrip('\n').split('\t')]
                if not 줄.strip() or 줄.lstrip().startswith('#') or len(칸) < 2 or not 칸[0] or not 칸[1]:
                    continue
                쌍.append((칸[0].strip('/'), 칸[1].strip('/')))
    elif len(args.경로) == 2:
        쌍 = [(args.경로[0].strip('/'), args.경로[1].strip('/'))]
    else:
        raise SystemExit('✗ `복사 <옛 자리> <새 자리>` 또는 `복사 --표 사본표.tsv`')
    d, m = 드라이브(), {'파일': {}, '폴더': {'': 뿌리ID}}
    일, 모두수, 모두크기 = [], 0, 0
    for 옛, 새 in 쌍:
        x, 폴더인가 = 경로id(d, m, 옛)
        if 폴더인가:
            폴더들, 파일들 = 다훑기(d, x)
        else:
            if isinstance(x, str):
                x = dict(d.정보(x), id=x, name=os.path.basename(옛))
            폴더들, 파일들 = [], [(dict(x, name=os.path.basename(새)), '')]
        크기 = sum(int(f.get('size') or 0) for f, _ in 파일들)
        모두수, 모두크기 = 모두수 + len(파일들), 모두크기 + 크기
        print('%s → %s\t폴더 %d · 파일 %d · %s' % (옛, 새, len(폴더들), len(파일들), 크기글(크기)), flush=True)
        일.append((옛, 새, 폴더인가, 폴더들, 파일들))
    print('모두 파일 %d개 · %s · 어림 %.0f분 (파일 하나 4초, 8 이 함께)' % (모두수, 크기글(모두크기), 모두수 * 4 / 8 / 60))
    if not args.정말:
        print('\n(보이기만 했다 — 지으려면 --정말)')
        return

    본것, 됨, 건넘, 틀림 = {}, [0], [0], []

    def 안의이름(부모):
        if 부모 not in 본것:
            본것[부모] = {x['name'] for x in d.목록(부모)}
        return 본것[부모]

    할일 = []
    for 옛, 새, 폴더인가, 폴더들, 파일들 in 일:
        뿌리 = 폴더보장(d, m, 새 if 폴더인가 else os.path.dirname(새), True)
        자리 = {'': 뿌리}
        for 길 in 폴더들:          #: 위층부터 나온다 (다훑기가 층 차례로 모은다)
            위, 이름 = os.path.dirname(길), os.path.basename(길)
            있음 = [x for x in d.목록(자리[위]) if x['name'].replace('/', '_') == 이름 and x['mimeType'] == 폴더꼴]
            자리[길] = 있음[0]['id'] if 있음 else d.폴더짓기(이름, 자리[위])
        for f, 길 in 파일들:
            부모 = 자리[os.path.dirname(길)] if 폴더인가 else 뿌리
            할일.append((f, 부모, (새 + '/' + 길) if 길 else 새))

    for 부모 in {부모 for _, 부모, _ in 할일}:
        안의이름(부모)

    def 하나(칸):
        f, 부모, 길 = 칸
        if f['name'] in 본것[부모]:
            건넘[0] += 1
            return
        try:
            d.사본(f, 부모)
            됨[0] += 1
        except urllib.error.HTTPError as e:
            틀림.append((길, '%s %s' % (e.code, e.read()[:200].decode('utf-8', 'replace'))))

    시작 = time.time()
    with concurrent.futures.ThreadPoolExecutor(args.일꾼) as 일꾼:
        for i, _ in enumerate(일꾼.map(하나, 할일), 1):
            if i % 100 == 0:
                print('  %d / %d (%.0f초)' % (i, len(할일), time.time() - 시작), flush=True)
    print('✔ 사본 — 지음 %d · 이미 있어 건넘 %d · 못함 %d · %.0f초' % (됨[0], 건넘[0], len(틀림), time.time() - 시작))
    for 길, 왜 in 틀림:
        print('  ✘', 길, '—', 왜)
    if 틀림:
        sys.exit(1)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest='일', required=True)
    b = sp.add_parser('받기')
    b.add_argument('경로', nargs='*')
    b.add_argument('--큰것', action='store_true', help='%dMB 넘는 파일도 받는다' % 큰것MB)
    b.add_argument('--전부', action='store_true', help='되돌림 사본 등 빼던 것도 받는다')
    b.add_argument('--글만', action='store_true', help='그림ㆍPDFㆍ한글ㆍ캐드ㆍ압축 파일은 빼고 받는다 (훨씬 빠르다)')
    b.add_argument('--꼴', nargs='+', metavar='꼴', help='이 꼴의 파일만 받는다 (보기: --꼴 "*.yaml" "*.md")')
    sp.add_parser('견주기')
    o = sp.add_parser('올리기')
    o.add_argument('--정말', action='store_true')
    s = sp.add_parser('세기')
    s.add_argument('경로', nargs='*')
    c = sp.add_parser('복사')
    c.add_argument('경로', nargs='*', help='<옛 자리> <새 자리> (드라이브 뿌리 기준)')
    c.add_argument('--표', help='옛 자리 ⇥ 새 자리 를 한 줄에 하나씩 적은 tsv (# 줄은 건너뛴다)')
    c.add_argument('--정말', action='store_true')
    c.add_argument('--일꾼', type=int, default=8, help='한꺼번에 복사할 수 (기본 8)')
    args = ap.parse_args()
    {'받기': 받기, '견주기': 견주기, '올리기': 올리기, '세기': 세기, '복사': 복사}[args.일](args)


if __name__ == '__main__':
    try:
        main()
    except urllib.error.HTTPError as e:
        raise SystemExit('✗ 드라이브가 거절했다 (%s): %s' % (e.code, e.read()[:300].decode('utf-8', 'replace')))
