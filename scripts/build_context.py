#!/usr/bin/env python3
"""Combine selected story context into a single Markdown file for copy/reference."""
from pathlib import Path
import argparse
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser()
p.add_argument('--output',default='reports/집필_컨텍스트.md')
p.add_argument('--include-chapters',action='store_true',help='also include corrected episodes 1-3 (larger context)')
a=p.parse_args()
paths=['AGENTS.md','01_설정/정본_세계관.md','01_설정/인물설정.md','01_설정/미래안_규칙.md','01_설정/사건연대표_2009.md','01_설정/장편_서사설계.md','02_편집/문체_규칙.md','02_편집/미해결_쟁점.md','04_집필/03_제4화_설계.md']
if a.include_chapters:
 paths+= [f'03_수정원고/{i}화_2009_정합성보정.txt' for i in (1,2,3)]
parts=['# Codex 집필 컨텍스트\n> 자동 결합 파일이며 정본은 각 원본 경로에 있다.\n']
for rel in paths:
 s=(ROOT/rel).read_text(encoding='utf-8')
 parts.append(f'\n---\n\n## FILE: {rel}\n\n````text\n{s}\n````\n')
out=ROOT/a.output;out.parent.mkdir(parents=True,exist_ok=True);out.write_text('\n'.join(parts),encoding='utf-8')
print(f'{out} : {len(out.read_text(encoding="utf-8")):,} characters / {len(paths)} source files')
