#!/usr/bin/env python3
"""Read-only baseline continuity / source-integrity checks. Python 3.9+."""
from pathlib import Path
import json, hashlib, datetime, re, sys
ROOT=Path(__file__).resolve().parents[1]
CANON=ROOT/'01_설정'/'세계관_정본.json'
REPORT=ROOT/'reports'/'검사_결과.txt'
BASE=ROOT/'scripts'/'original_sha256.json'
issues=[];notes=[]
def warn(msg): issues.append(msg)
with CANON.open(encoding='utf-8') as f: canon=json.load(f)
if canon['confirmed'].get('present_year')!=2009: warn('세계관 현재 연도가 2009가 아닙니다.')
for i in range(1,4):
 original=ROOT/'00_원본'/f'{i}화_원본.txt'
 revised=ROOT/'03_수정원고'/f'{i}화_2009_정합성보정.txt'
 if not original.exists() or not revised.exists():warn(f'{i}화 원본 또는 수정초고 누락');continue
 raw=original.read_bytes();actual=hashlib.sha256(raw).hexdigest()
 if BASE.exists():
  hashes=json.loads(BASE.read_text(encoding='utf-8'))
  if actual!=hashes.get(original.name):warn(f'절대보존 원본 변경 감지: {original.name}')
 revised_text=revised.read_text(encoding='utf-8')
 if '2007년 11월' in revised_text:warn(f'{i}화 수정 원고에 2007년 11월 표현 발견')
 if i==1 and ('전자발찌' in revised_text or '형사기동대' in revised_text):warn('1화 수정 원고에 전자발찌/현대 조직 명칭이 남았습니다.')
 if i==2 and '아가씨 세 명' in revised_text:warn('2화 여성 인원과 3화가 충돌할 수 있습니다.')
 if i==3 and '모든 조간신문' in revised_text:warn('3화 시신발견 당일 조간신문 발표 시점 의심')
 notes.append(f'{i}화 보정본: {len(revised_text):,}자')
for ds in ['2009-11-16','2009-11-18','2009-11-25']:
 notes.append(f'{ds}: {datetime.date.fromisoformat(ds).strftime("%A")}')
report='연속성 기계 검사 / 소설 원고\n'+'='*35+'\n'+'\n'.join(notes)+'\n\n경고:\n'+ ('\n'.join('- '+v for v in issues) if issues else '기초 검사 통과')+'\n\n※ 이 검사는 과학·법률 고증과 문학적 개연성을 자동 인증하지 않습니다.\n'
REPORT.parent.mkdir(exist_ok=True)
REPORT.write_text(report,encoding='utf-8')
print(report)
sys.exit(1 if issues else 0)
