#!/usr/bin/env python3
"""
Korean Humanizer Quantitative & Deep Structural Forensics Audit Script (v3.0)
Pure Python 3.10 stdlib-only.
Checks:
  - A~K general Korean AI tells + L fiction patterns + M deep structural/convergence patterns
  - Optional length contract (--min-chars / --max-chars)
  - Optional 5-axis baseline comparison gates (token change rate, sentence touch rate,
    formal '하였' injection, cliche injection, epistemic modality preservation)
  - Optional cross-episode corpus n-gram & stock-tell forensics (--corpus-dir)

Usage:
  python audit_korean.py <target_file_or_dir> [baseline_file]
                         [--mode auto|prose|fiction]
                         [--corpus-dir <dir>]
                         [--min-chars 7000] [--max-chars 10000]
                         [--names 아이작,카라,레니아]
                         [--json] [--json-out <path>]
"""

from __future__ import annotations

import argparse
import difflib
import json
import math
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Non-name nouns that look like [2-4 Hangul chars]+(은|는|이|가) at paragraph starts
NON_NAME_NOUNS = {
    "그것", "이것", "저것", "여기", "거기", "저기", "오늘", "어제", "내일", "지금",
    "그때", "이때", "잠시", "한참", "시간", "세월", "순간", "동안", "사이", "마음",
    "생각", "기억", "느낌", "감정", "기분", "표정", "시선", "눈빛", "목소", "소리",
    "분위", "상황", "문제", "이유", "결과", "사실", "결국", "원래", "아직", "이미",
    "대부분", "모두", "누구", "무엇", "어디", "하나", "둘", "사람", "인간", "남자",
    "여자", "사내", "여인", "아이", "노인", "청년", "학자", "사제", "간수", "장로",
    "원로", "대사", "정령", "마나", "마법", "술식", "결계", "코어", "세계", "도시",
    "하늘", "바람", "공기", "햇살", "달빛", "어둠", "그림", "빛", "불꽃", "나무",
    "숲", "땅", "바닥", "하늘", "구름", "물", "불", "소리", "냄새", "온기",
    "종이", "책상", "의자", "창살", "문", "벽", "방", "복도", "공터", "계곡",
    "산길", "수풀", "잎사", "열매", "뿌리", "소금", "수프", "빵", "접시", "그릇",
    "칼", "검", "활", "화살", "지팡", "깃펜", "양피", "마석", "수정", "포탈",
    "몸", "손", "발", "눈", "입", "얼굴", "가슴", "심장", "어깨", "머리", "고개",
    "허리", "무릎", "목", "귀", "코", "턱", "이마", "볼", "입술", "손끝", "발끝",
    "자신", "상대", "그녀", "그들", "우리", "저희", "당신", "선배", "후배", "막내",
    "동기", "교수", "강사", "학생", "직원", "주방", "대신", "오히려", "그저", "다만",
    "게다", "게다가", "또한", "하지", "하지만", "그러", "그러나", "그리고", "따라",
    "마치", "비록", "설령", "물론", "어차", "어쩌", "실제", "사실", "분명", "아마",
    "특히", "결코", "적어", "만약", "만일", "대체", "차라", "오직", "겨우", "서로",
    "사방", "주변", "주위", "바깥", "안쪽", "가운", "중심", "가장", "처음", "마지",
    "나중", "이전", "이후", "이번", "다음", "이내", "곧", "다시", "아까", "방금",
    "최근", "요즘", "당시", "이곳", "그곳", "저곳", "어느", "무슨", "어떤", "모든",
    "전체", "절반", "나머", "일부", "대강", "대충", "거의", "전혀", "전부", "모조",
    "어머", "아무", "누군", "무언", "어딘", "뭔가", "누가", "뭐가", "질문", "대답",
    "말", "글", "뜻", "이름", "제목", "내용", "원리", "구조", "비율", "수치", "오차",
    "공식", "수식", "계산", "결과", "조건", "규칙", "법칙", "이론", "가설", "검증",
    "실험", "데이터", "파동", "진동", "위상", "대역", "밀도", "저항", "압력", "온도",
    "열량", "전분", "단백", "소화", "혈당", "체내", "독성", "피로", "허기", "통증",
    "진실", "거짓", "비밀", "약속", "맹세", "대가", "희망", "절망", "분노", "공포",
    "천계", "지구", "이세", "판타", "대삼", "실바", "암브", "작품", "연구", "과제",
    "보고", "메일", "영상", "댓글", "찬사", "평가", "공채", "명함", "논문", "마감",
    "목표", "장면", "회차", "이야", "서사", "대사", "지문", "문장", "단락", "표현",
    "목소리", "발걸음", "눈동자", "손바닥", "입꼬리", "그림자", "정승민", "이세계",
    "대삼림", "실바니아", "목숨", "생명", "인생", "운명", "과거", "현재", "미래",
}

DIALOGUE_OPENERS = ("“", '"', "‘", "—", "―")

STOCK_TELL_PATTERNS: list[tuple[str, str]] = [
    ("고개 동작(들/끄덕/돌/숙/갸웃)", r"고개를\s*(?:들|끄덕|돌|숙|갸웃|저|젖)[가-힣]*"),
    ("입 열기/다물기", r"입을\s*(?:열|다물|뻐끔|다물었)[가-힣]*"),
    ("눈 커짐/깜빡임", r"눈(?:이\s*커|을\s*깜빡|살을\s*찌푸)[가-힣]*"),
    ("주먹 쥐기", r"주먹을\s*(?:꽉\s*)?쥐[가-힣]*"),
    ("침/숨 삼키기", r"(?:침을\s*삼|숨을\s*(?:삼|들이|내쉬|고르))[가-힣]*"),
]

CRUTCH_ADVERBS = [
    "순간", "조금", "잠시", "한참", "천천히", "문득", "이윽고", "슬그머니", "말없이"
]

D_HYPE_PATTERN = re.compile(
    r"(결론적으로|시사하는\s*바가|주목할\s*만하|본질적으로|핵심적으로|궁극적으로|"
    r"다채로운|독보적인|압도적인|획기적인|자리매김|방증하|새로운\s*지평|중요한\s*이정표|"
    r"기록적인\s*성과|괄목할\s*만한)"
)

MODALITY_PATTERN = re.compile(
    r"(?:수\s*(?:있다|있었|있을|없다|없었)|듯(?:하다|했다|싶|보)|"
    r"가능성[이도은을에]?|것으로\s*(?:보인|판단|추정|전망)|(?:아닐까|일지도|모른다|모르겠))"
)


def char_counts(text: str) -> tuple[int, int]:
    total = len(text)
    no_ws = len(re.sub(r"\s+", "", text))
    return total, no_ws


def word_diff_ratio(orig: str, rev: str) -> float:
    orig_tokens = orig.split()
    rev_tokens = rev.split()
    if not orig_tokens:
        return 0.0
    matcher = difflib.SequenceMatcher(None, orig_tokens, rev_tokens)
    unchanged = sum(block.size for block in matcher.get_matching_blocks())
    denom = max(len(orig_tokens), len(rev_tokens))
    return round((1.0 - unchanged / denom) * 100.0, 1)


def split_sentences(text: str) -> list[str]:
    clean = re.sub(r"\s+", " ", text).strip()
    if not clean:
        return []
    return [s.strip() for s in re.split(r"(?<=[.!?…])\s+", clean) if s.strip()]


def sentence_touch_rate(orig: str, rev: str) -> tuple[float, int, int]:
    b_sents = [re.sub(r"\s+", " ", s).strip() for s in split_sentences(orig)]
    b_sents = [s for s in b_sents if s]
    if not b_sents:
        return 0.0, 0, 0
    a_set = {re.sub(r"\s+", " ", s).strip() for s in split_sentences(rev)}
    touched = sum(1 for s in b_sents if s not in a_set)
    return round(touched / len(b_sents) * 100.0, 1), touched, len(b_sents)


def detect_mode(text: str, explicit_mode: str) -> str:
    if explicit_mode in ("prose", "fiction"):
        return explicit_mode
    quote_lines = len(re.findall(r"(?m)^[“\"—―]", text))
    if quote_lines >= 8 or re.search(r"(?m)^\d+화[\.\s-]", text):
        return "fiction"
    return "prose"


def classify_blocks(lines: list[str]) -> tuple[list[str], list[str], list[str]]:
    """Split non-empty lines into (narration_blocks, dialogue_blocks, thought_blocks)."""
    narr: list[str] = []
    dial: list[str] = []
    thought: list[str] = []
    for idx, raw in enumerate(lines):
        s = raw.strip()
        if not s or s == "---" or s.startswith("["):
            continue
        if idx == 0 and re.match(r"^\d+화[\.\s-]", s):
            continue
        if s.startswith(("“", '"', "—", "―")):
            dial.append(s)
        elif s.startswith("‘") and s.endswith("’"):
            thought.append(s)
        else:
            narr.append(s)
    return narr, dial, thought


def is_likely_name_subject(block: str, explicit_names: set[str] | None = None) -> str | None:
    m = re.match(r"^([가-힣]{2,5})(?:은|는|이|가)\s", block)
    if not m:
        return None
    stem = m.group(1)
    if explicit_names:
        if stem in explicit_names:
            return m.group(0).strip()
        # Allow unknown proper names only if not in NON_NAME_NOUNS and not ending with adverbial stems
    if stem in NON_NAME_NOUNS:
        return None
    if stem.endswith(("하", "되", "있", "없", "같", "많", "적", "크", "작", "높", "낮", "길", "짧", "들")):
        return None
    return m.group(0).strip()


def shannon_entropy(items: list[str]) -> float:
    if not items:
        return 0.0
    counts = Counter(items)
    n = len(items)
    ent = 0.0
    for c in counts.values():
        p = c / n
        ent -= p * math.log2(p)
    return round(ent, 3)


def longest_same_bucket_streak(narr_blocks: list[str]) -> int:
    def bucket(n: int) -> str:
        if n < 45:
            return "S"
        if n <= 130:
            return "M"
        return "L"

    streak = 0
    best = 0
    prev = None
    for b in narr_blocks:
        bk = bucket(len(b))
        if bk == prev:
            streak += 1
        else:
            streak = 1
            prev = bk
        if streak > best:
            best = streak
    return best


def max_consecutive_narration_sentences(lines: list[str]) -> int:
    streak = 0
    best = 0
    for raw in lines:
        s = raw.strip()
        if not s or s == "---" or re.match(r"^\d+화[\.\s-]", s):
            continue
        if s.startswith(DIALOGUE_OPENERS):
            streak = 0
            continue
        streak += len(split_sentences(s))
        if streak > best:
            best = streak
    return best


def extract_narration_ngrams(narr_blocks: list[str], n: int = 2) -> Counter[str]:
    counts: Counter[str] = Counter()
    for blk in narr_blocks:
        tokens = re.findall(r"[가-힣]{2,}", blk)
        if len(tokens) < n:
            continue
        for i in range(len(tokens) - n + 1):
            gram = " ".join(tokens[i : i + n])
            counts[gram] += 1
    return counts


def audit_text(
    text: str,
    name: str,
    baseline_text: str | None = None,
    mode: str = "auto",
    min_chars: int | None = None,
    max_chars: int | None = None,
    explicit_names: set[str] | None = None,
) -> dict[str, Any]:
    lines = text.splitlines()
    resolved_mode = detect_mode(text, mode)
    total_chars, no_ws_chars = char_counts(text)

    s1_issues: list[dict[str, str]] = []
    s2_warnings: list[dict[str, str]] = []
    infos: list[str] = []

    def add_s1(code: str, msg: str) -> None:
        s1_issues.append({"code": code, "msg": msg})

    def add_s2(code: str, msg: str) -> None:
        s2_warnings.append({"code": code, "msg": msg})

    # 0. Length contract check
    length_status = "UNCHECKED"
    if min_chars is not None or max_chars is not None:
        lo = min_chars or 0
        hi = max_chars or 10**9
        if total_chars < lo or total_chars > hi:
            length_status = "FAIL"
            add_s1(
                "LENGTH",
                f"분량 계약 위반: {total_chars:,}자 (허용 {lo:,}~{hi:,}자)",
            )
        elif (min_chars and total_chars - lo < 200) or (max_chars and hi - total_chars < 200):
            length_status = "WARN_BOUNDARY"
            add_s2(
                "LENGTH_MARGIN",
                f"분량 경계 근접: {total_chars:,}자 (허용 {lo:,}~{hi:,}자)",
            )
        else:
            length_status = "PASS"

    # Baseline 5-axis comparison gates
    baseline_info: dict[str, Any] = {}
    if baseline_text is not None:
        b_total, b_no_ws = char_counts(baseline_text)
        delta_pct = round(((total_chars - b_total) / b_total * 100.0), 1) if b_total else 0.0
        chg_pct = word_diff_ratio(baseline_text, text)
        touch_pct, touched_cnt, base_sent_cnt = sentence_touch_rate(baseline_text, text)

        a_hayeot = len(re.findall(r"하였", baseline_text))
        b_hayeot = len(re.findall(r"하였", text))
        a_haess = len(re.findall(r"했", baseline_text))
        pure_hayeot = a_hayeot > 0 and a_haess == 0
        hayeot_injected = (not pure_hayeot) and (b_hayeot > a_hayeot)
        if hayeot_injected:
            add_s1("GATE_HAYEOT", f"'하였' 격식 역주행 ({a_hayeot}회 -> {b_hayeot}회)")

        a_hype = len(D_HYPE_PATTERN.findall(baseline_text))
        b_hype = len(D_HYPE_PATTERN.findall(text))
        if b_hype > a_hype:
            add_s1("GATE_CLICHE", f"D계열 상투구 역주입 ({a_hype}회 -> {b_hype}회)")

        a_mod = len(MODALITY_PATTERN.findall(baseline_text))
        b_mod = len(MODALITY_PATTERN.findall(text))

        guard = "OK"
        if chg_pct > 50:
            guard = "STOP (>50%)"
            add_s1("GATE_DIFF_50", f"어절 변경률 50% 초과 ({chg_pct}%)")
        elif chg_pct > 30:
            guard = "WARN (>30%)"
            add_s2("GATE_DIFF_30", f"어절 변경률 30% 초과 ({chg_pct}%)")

        baseline_info = {
            "baseline_chars": b_total,
            "baseline_no_ws": b_no_ws,
            "length_delta_pct": delta_pct,
            "token_change_pct": chg_pct,
            "diff_guard": guard,
            "sentence_touch_pct": touch_pct,
            "sentence_touched": f"{touched_cnt}/{base_sent_cnt}",
            "hayeot_before_after": [a_hayeot, b_hayeot],
            "modality_before_after": [a_mod, b_mod],
        }

    # 1. A-1~A-3, A-7, A-8 Translation-ese
    s1_trans_patterns = [
        ("A-8 이중피동", r"[가-힣]+(?:되어|보여|여겨)[지진졌질][가-힣]*"),
        ("A-1 ~에 대해", r"에\s*대해(서)?|에\s*대한"),
        ("A-2 ~를 통해", r"(을|를)\s*통해(서)?|(을|를)\s*통하여"),
        ("A-3 ~에 있어", r"에\s*있어(서)?"),
        ("A-7 가지고 있다/가진다", r"가지고\s*있|가진다|가졌"),
    ]
    for label, pat in s1_trans_patterns:
        hits = []
        for idx, line in enumerate(lines, 1):
            for m in re.finditer(pat, line):
                hits.append(f"L{idx}({m.group(0)})")
        if hits:
            if "A-8" in label or len(hits) >= 2:
                add_s1(label.split()[0], f"{label}: {len(hits)}건 -> {', '.join(hits[:8])}")
            else:
                add_s2(label.split()[0], f"{label}: {len(hits)}건 -> {', '.join(hits[:8])}")

    # 2. A-16 Pronouns
    para_pronoun_s1 = []
    she_hits = []
    for idx, line in enumerate(lines, 1):
        if not line.strip():
            continue
        p_matches = re.findall(
            r"(?<![가-힣])(그녀|그들|그것)(는|가|은|이|의|을|를|에게|도|만)|(?<![가-힣])그(는|가|의|를|에게)(?=\s)",
            line,
        )
        if len(p_matches) >= 3:
            para_pronoun_s1.append(f"L{idx}({len(p_matches)}회)")
        for m in re.finditer(r"(?<![가-힣])그녀(는|가|의|를|에게|도|만|와|과)", line):
            she_hits.append(f"L{idx}({m.group(0)})")
    if para_pronoun_s1:
        add_s1("A-16", f"한 단락 대명사 3회+ 강박: {', '.join(para_pronoun_s1)}")
    if len(she_hits) >= 3:
        add_s2("A-16", f"번역투 3인칭 '그녀*' 누적(3회+): {len(she_hits)}건 -> {', '.join(she_hits[:8])}")

    # 3. A-17 & A-19
    quant_plural = []
    dbl_particle = []
    for idx, line in enumerate(lines, 1):
        for m in re.finditer(r"(많은|여러|다양한|수많은|모든|각종)\s+[가-힣]+들", line):
            quant_plural.append(f"L{idx}({m.group(0)})")
        for m in re.finditer(r"[가-힣]+(에서의|으로의|로써의|에의|으로부터의)", line):
            dbl_particle.append(f"L{idx}({m.group(0)})")
    if quant_plural:
        add_s2("A-17", f"수량어+복수 '~들' 중복: {len(quant_plural)}건 -> {', '.join(quant_plural[:8])}")
    if dbl_particle:
        add_s2("A-19", f"이중 조사: {len(dbl_particle)}건 -> {', '.join(dbl_particle[:8])}")

    # 4. B-1 / L-9 Parenthetical Hanja / English
    paren_hits = []
    for idx, line in enumerate(lines, 1):
        for m in re.finditer(r"[가-힣]+\([一-龥A-Za-z0-9\s.,-]+\)", line):
            paren_hits.append(f"L{idx}({m.group(0)})")
    if paren_hits:
        if resolved_mode == "fiction":
            add_s1("B-1/L-9", f"괄호 한자·영문 병기: {len(paren_hits)}건 -> {', '.join(paren_hits[:8])}")
        else:
            add_s2("B-1", f"괄호 한자·영문 병기: {len(paren_hits)}건 -> {', '.join(paren_hits[:8])}")

    # 5. C-11 Comma after connective endings
    c11_hits = []
    for idx, line in enumerate(lines, 1):
        for m in re.finditer(r"[가-힣]{2,}(고|며|지만|면서|아서|어서|여서|으나|더니),\s", line):
            word = m.group(0).rstrip(", ")
            if word in ("그리고", "하지만", "그러나", "그렇지만", "아니면", "그러자", "그러더니"):
                continue
            c11_hits.append(f"L{idx}({word},)")
    if len(c11_hits) >= 10:
        add_s1("C-11", f"연결어미 뒤 쉼표 과다(10회+): {len(c11_hits)}건 -> {', '.join(c11_hits[:10])}")
    elif len(c11_hits) >= 6:
        add_s2("C-11", f"연결어미 뒤 쉼표 누적(6~9회): {len(c11_hits)}건 -> {', '.join(c11_hits[:8])}")
    elif c11_hits:
        infos.append(f"C-11 연결어미 뒤 쉼표 {len(c11_hits)}건 [정상 범위]")

    # 6. D / H-1 / I-1
    d_hits, i1_hits, h1_hits = [], [], []
    for idx, line in enumerate(lines, 1):
        for m in D_HYPE_PATTERN.finditer(line):
            d_hits.append(f"L{idx}({m.group(0)})")
        for m in re.finditer(r"[가-힣]+\s*(인|한|는|던)\s*것이다\.", line):
            i1_hits.append(f"L{idx}({m.group(0)})")
        m_h = re.match(r"^\s*(또한|게다가|더불어|아울러|나아가|따라서|즉)[,\s]", line)
        if m_h:
            h1_hits.append(f"L{idx}({m_h.group(1)})")
    if d_hits:
        add_s1("D-HYPE", f"AI 상투어/Hype: {len(d_hits)}건 -> {', '.join(d_hits[:8])}")
    if len(h1_hits) >= 5:
        add_s1("H-1", f"문두 접속사 5회+: {len(h1_hits)}건 -> {', '.join(h1_hits)}")
    elif len(h1_hits) >= 2:
        add_s2("H-1", f"문두 접속사: {len(h1_hits)}건 -> {', '.join(h1_hits)}")
    if i1_hits:
        add_s2("I-1", f"'~것이다.' 결말: {len(i1_hits)}건 -> {', '.join(i1_hits)}")

    # 7. J-2 Em-dash / En-dash
    prose_dashes, dial_dashes = [], []
    for idx, line in enumerate(lines, 1):
        if not re.search(r"[—–―]", line):
            continue
        stripped = line.strip()
        if stripped.startswith(("—", "―")) or stripped.startswith("[") or re.search(r"[—―][!.?\"”]*$", stripped):
            dial_dashes.append(f"L{idx}")
        else:
            prose_dashes.append(f"L{idx}({stripped[:32]}...)")
    if prose_dashes:
        add_s1("J-2", f"본문 삽입 줄표(—/–/―): {len(prose_dashes)}건 -> {', '.join(prose_dashes)}")
    if dial_dashes and resolved_mode == "prose":
        add_s1("J-2", f"줄표 사용: {len(dial_dashes)}건 -> {', '.join(dial_dashes)}")
    elif dial_dashes:
        infos.append(f"전음/의성어 줄표 {len(dial_dashes)}건 [서사 표기 허용]")

    # 8. E-1 / E-2 & Deep Structural Forensics (M-1 ~ M-7)
    narr_blocks, dial_blocks, thought_blocks = classify_blocks(lines)
    narr_text = "\n".join(narr_blocks)
    all_sents = split_sentences("\n".join(narr_blocks + dial_blocks + thought_blocks))
    narr_sents = split_sentences(narr_text)

    mean_l = std_l = cv_l = 0.0
    iss_cnt = go_cnt = 0
    if all_sents:
        lens = [len(s) for s in all_sents]
        mean_l = sum(lens) / len(lens)
        std_l = math.sqrt(sum((x - mean_l) ** 2 for x in lens) / len(lens))
        cv_l = std_l / mean_l if mean_l else 0.0
        iss_cnt = sum(1 for s in all_sents if s.endswith("있었다."))
        go_cnt = len(re.findall(r"고\s*있(?:다|었다|는)", text))
        if std_l < 8.0:
            add_s2("E-1", f"문장 길이 표준편차 낮음 ({std_l:.1f} < 8.0)")

    # M-1: Name-subject paragraph openers
    name_openers: list[str] = []
    for blk in narr_blocks:
        hit = is_likely_name_subject(blk, explicit_names)
        if hit:
            name_openers.append(hit)
    m1_pct = round(len(name_openers) / len(narr_blocks) * 100.0, 1) if narr_blocks else 0.0
    top_openers = Counter(name_openers).most_common(5)
    if resolved_mode == "fiction" and len(narr_blocks) >= 10:
        if m1_pct > 28.0:
            add_s1("M-1", f"문두 [인물명+조사] 편중 심각: {len(name_openers)}/{len(narr_blocks)} ({m1_pct}% > 28%) -> {top_openers}")
        elif m1_pct > 20.0:
            add_s2("M-1", f"문두 [인물명+조사] 편중 경고: {len(name_openers)}/{len(narr_blocks)} ({m1_pct}% > 20%) -> {top_openers}")

    # M-2: Narration terminal monotony (-다. ratio & ending entropy)
    da_cnt = sum(1 for s in narr_sents if s.endswith("다."))
    da_pct = round(da_cnt / len(narr_sents) * 100.0, 1) if narr_sents else 0.0
    end_3grams = [s[-4:] for s in narr_sents if len(s) >= 4]
    end_entropy = shannon_entropy(end_3grams)
    top_terminals = Counter(re.findall(r"([가-힣]+[.!?])$", s)[0] for s in narr_sents if re.search(r"[가-힣]+[.!?]$", s)).most_common(5)
    if resolved_mode == "fiction" and len(narr_sents) >= 25 and da_pct > 93.0 and end_entropy < 3.6:
        add_s2("M-2", f"지문 '-다.' 종결 단조 ({da_pct}%, 엔트로피 {end_entropy}) -> 상위 종결: {top_terminals[:3]}")

    # M-3: Stock physical tells
    stock_counts: dict[str, int] = {}
    stock_total = 0
    for label, pat in STOCK_TELL_PATTERNS:
        cnt = len(re.findall(pat, narr_text))
        if cnt:
            stock_counts[label] = cnt
            stock_total += cnt
    if resolved_mode == "fiction":
        if stock_total >= 8:
            add_s1("M-3", f"범용 신체반응 크러치 과다(8회+): 총 {stock_total}회 -> {stock_counts}")
        elif stock_total >= 5:
            add_s2("M-3", f"범용 신체반응 크러치 누적(5~7회): 총 {stock_total}회 -> {stock_counts}")

    # M-4: Crutch adverbs
    adverb_counts = {adv: len(re.findall(rf"(?<![가-힣]){adv}(?![가-힣])", narr_text)) for adv in CRUTCH_ADVERBS}
    adverb_counts = {k: v for k, v in adverb_counts.items() if v > 0}
    adverb_total = sum(adverb_counts.values())
    if resolved_mode == "fiction" and adverb_total >= 10:
        add_s2("M-4", f"시간·완충 부사 클러스터(10회+): 총 {adverb_total}회 -> {adverb_counts}")

    # M-5: Dialogue ratio & consecutive narration streak
    dial_no_ws = len(re.sub(r"\s+", "", "".join(dial_blocks)))
    dial_ratio = round(dial_no_ws / max(1, no_ws_chars) * 100.0, 1)
    max_narr_streak = max_consecutive_narration_sentences(lines)
    if resolved_mode == "fiction" and no_ws_chars >= 1500:
        if dial_ratio < 18.0:
            add_s2("M-5", f"대사 비중 매우 낮음(서술 편중): {dial_ratio}% (< 18%)")
        elif dial_ratio < 22.0:
            infos.append(f"대사 비중 다소 낮음({dial_ratio}% — 22~45% 권장)")
        if max_narr_streak >= 14:
            infos.append(f"최대 연속 서술 {max_narr_streak}문장 (물리 연산 독백 제외 시 장면화 검토)")

    # M-6: Paragraph length uniformity streak
    para_streak = longest_same_bucket_streak(narr_blocks)
    if resolved_mode == "fiction" and para_streak >= 8:
        add_s2("M-6", f"유사 길이 서술 문단 {para_streak}연속 (리듬 변주 부족)")

    # 9. L-series fiction checks & M-7 negation pairs
    if resolved_mode == "fiction":
        l4_hits, l6_hits, l3_hits, simile_hits, neg_pair_hits = [], [], [], [], []
        for idx, line in enumerate(lines, 1):
            for m in re.finditer(r"(말\s*못\s*할\s*감정|알\s*수\s*없는\s*(감정|빛)|묘한\s*여운|스치는\s*듯했|담겨\s*있는\s*듯했)", line):
                l4_hits.append(f"L{idx}({m.group(0)})")
            for m in re.finditer(r"[^.\r\n,“\"]+도,\s*[^.\r\n,“\"]+도\s*(없었|아니었|보이지|사라졌|떠오르지)", line):
                l6_hits.append(f"L{idx}({m.group(0).strip()})")
            for m in re.finditer(r"의\s*(눈동자|시선|입술|입꼬리|어깨|손끝|미간|구두코|목구멍)(이|가)\s+", line):
                l3_hits.append(f"L{idx}({m.group(0).strip()})")
            for m in re.finditer(r"(처럼|듯한|듯이)", line):
                simile_hits.append(f"L{idx}({m.group(0)})")
            for m in re.finditer(r"(?:아니었다|없었다)\.\s*[^.!?]{2,35}(?:였다|이었다|뿐이었다)\.", line):
                neg_pair_hits.append(f"L{idx}({m.group(0)})")
        if l4_hits:
            add_s1("L-4", f"추상적 감정 포장: {len(l4_hits)}건 -> {', '.join(l4_hits)}")
        if len(l6_hits) >= 2:
            add_s2("L-6", f"대칭 부정 구문 2회+: {len(l6_hits)}건 -> {', '.join(l6_hits)}")
        elif len(l6_hits) == 1:
            infos.append(f"L-6 대칭 부정 1건 ({l6_hits[0]}) [단독 극적 낙차용 허용]")
        if len(l3_hits) >= 6:
            add_s2("L-3", f"신체 부위 대리 주어 과다: {len(l3_hits)}건 -> {', '.join(l3_hits[:8])}")
        if len(simile_hits) >= 9:
            add_s2("L-5", f"직유(처럼/듯한/듯이) 과다: {len(simile_hits)}건 -> {', '.join(simile_hits[:8])}")
        if len(neg_pair_hits) >= 2:
            add_s2("M-7", f"부정-재정의 대구(아니었다. Y였다.) {len(neg_pair_hits)}건 -> {', '.join(neg_pair_hits[:5])}")

    grade = "A" if (len(s1_issues) == 0 and len(s2_warnings) <= 2) else ("B" if len(s1_issues) == 0 else ("C" if len(s1_issues) <= 2 else "D"))

    return {
        "file": name,
        "mode": resolved_mode,
        "chars_with_spaces": total_chars,
        "chars_no_ws": no_ws_chars,
        "length_status": length_status,
        "baseline": baseline_info,
        "rhythm": {
            "narration_blocks": len(narr_blocks),
            "dialogue_blocks": len(dial_blocks),
            "thought_blocks": len(thought_blocks),
            "sentences": len(all_sents),
            "mean_sent_len": round(mean_l, 1),
            "std_sent_len": round(std_l, 1),
            "cv": round(cv_l, 3),
            "iss_ratio_pct": round(iss_cnt / len(all_sents) * 100.0, 1) if all_sents else 0.0,
            "go_it_count": go_cnt,
            "dialogue_ratio_pct": dial_ratio,
            "max_narr_streak": max_narr_streak,
            "para_bucket_streak": para_streak,
        },
        "deep_forensics": {
            "m1_name_opener_pct": m1_pct,
            "m1_name_opener_count": f"{len(name_openers)}/{len(narr_blocks)}",
            "m1_top_openers": top_openers,
            "m2_da_ending_pct": da_pct,
            "m2_ending_entropy": end_entropy,
            "m2_top_terminals": top_terminals,
            "m3_stock_tells_total": stock_total,
            "m3_stock_tells": stock_counts,
            "m4_crutch_adverbs_total": adverb_total,
            "m4_crutch_adverbs": adverb_counts,
        },
        "s1_issues": s1_issues,
        "s2_warnings": s2_warnings,
        "infos": infos,
        "grade": grade,
    }


def corpus_forensics(corpus_dir: Path, explicit_names: set[str] | None = None) -> dict[str, Any]:
    files = sorted(
        [p for p in corpus_dir.glob("*.txt") if re.match(r"^\d+화", p.name)],
        key=lambda p: int(re.match(r"^(\d+)", p.name).group(1)),
    )
    if not files:
        files = sorted(corpus_dir.glob("*.txt"))

    all_narr_blocks: list[str] = []
    stock_totals: Counter[str] = Counter()
    adverb_totals: Counter[str] = Counter()
    opener_totals: Counter[str] = Counter()
    bigram_counts: Counter[str] = Counter()
    trigram_counts: Counter[str] = Counter()

    for p in files:
        lines = p.read_text(encoding="utf-8").splitlines()
        narr, _, _ = classify_blocks(lines)
        all_narr_blocks.extend(narr)
        narr_text = "\n".join(narr)
        for label, pat in STOCK_TELL_PATTERNS:
            c = len(re.findall(pat, narr_text))
            if c:
                stock_totals[label] += c
        for adv in CRUTCH_ADVERBS:
            c = len(re.findall(rf"(?<![가-힣]){adv}(?![가-힣])", narr_text))
            if c:
                adverb_totals[adv] += c
        for blk in narr:
            hit = is_likely_name_subject(blk, explicit_names)
            if hit:
                opener_totals[hit] += 1
        bigram_counts.update(extract_narration_ngrams(narr, 2))
        trigram_counts.update(extract_narration_ngrams(narr, 3))

    return {
        "files": [p.name for p in files],
        "narration_blocks_total": len(all_narr_blocks),
        "stock_tells": stock_totals.most_common(10),
        "crutch_adverbs": adverb_totals.most_common(10),
        "top_name_openers": opener_totals.most_common(10),
        "top_bigrams": [(g, c) for g, c in bigram_counts.most_common(20) if c >= 3],
        "top_trigrams": [(g, c) for g, c in trigram_counts.most_common(15) if c >= 2],
    }


def print_report(res: dict[str, Any]) -> None:
    r = res["rhythm"]
    d = res["deep_forensics"]
    print("=" * 64)
    print(f"FILE: {res['file']}  [mode={res['mode']}]  [length={res['length_status']}]")
    print(f"Chars (with spaces / no ws): {res['chars_with_spaces']:,} / {res['chars_no_ws']:,}")
    if res["baseline"]:
        b = res["baseline"]
        print(
            f"Baseline: {b['baseline_chars']:,} -> Delta {b['length_delta_pct']:+.1f}% | "
            f"TokenChg={b['token_change_pct']}% [{b['diff_guard']}] | "
            f"Touch={b['sentence_touch_pct']}% ({b['sentence_touched']}) | "
            f"하였={b['hayeot_before_after'][0]}->{b['hayeot_before_after'][1]} | "
            f"서법={b['modality_before_after'][0]}->{b['modality_before_after'][1]}"
        )
    print(
        f"Rhythm: Narr={r['narration_blocks']} Dial={r['dialogue_blocks']} Thought={r['thought_blocks']} | "
        f"Sents={r['sentences']} Mean={r['mean_sent_len']}자 Std={r['std_sent_len']}자 CV={r['cv']} | "
        f"대사비중={r['dialogue_ratio_pct']}% | '~있었다.'={r['iss_ratio_pct']}% | '~고 있*'={r['go_it_count']}"
    )
    print(
        f"Deep(M): M-1 문두이름={d['m1_name_opener_count']} ({d['m1_name_opener_pct']}%) | "
        f"M-2 '-다.'={d['m2_da_ending_pct']}% (Ent={d['m2_ending_entropy']}) | "
        f"M-3 범용신체={d['m3_stock_tells_total']}회 | M-4 완충부사={d['m4_crutch_adverbs_total']}회 | "
        f"연속서술최대={r['max_narr_streak']}문장"
    )
    for info in res["infos"]:
        print(f"  Info: {info}")
    print("--- Audit Findings ---")
    if not res["s1_issues"] and not res["s2_warnings"]:
        print(f"CLEAN: S1=0, S2=0  (Grade: {res['grade']})")
    else:
        for item in res["s1_issues"]:
            print(f"  [S1:{item['code']}] {item['msg']}")
        for item in res["s2_warnings"]:
            print(f"  [S2:{item['code']}] {item['msg']}")
        print(f"Estimated Grade: {res['grade']} (S1={len(res['s1_issues'])}, S2={len(res['s2_warnings'])})")


def main() -> None:
    parser = argparse.ArgumentParser(description="Korean Humanizer v3.0 Quantitative & Forensic Audit")
    parser.add_argument("target", help="Target file or directory path")
    parser.add_argument("baseline", nargs="?", default=None, help="Optional baseline file for 5-axis gates")
    parser.add_argument("--mode", choices=["auto", "prose", "fiction"], default="auto")
    parser.add_argument("--corpus-dir", default=None, help="Directory of sibling episodes for n-gram forensics")
    parser.add_argument("--min-chars", type=int, default=None, help="Minimum chars (with spaces)")
    parser.add_argument("--max-chars", type=int, default=None, help="Maximum chars (with spaces)")
    parser.add_argument("--names", default=None, help="Comma-separated character names for M-1 check")
    parser.add_argument("--json", action="store_true", help="Print JSON output")
    parser.add_argument("--json-out", default=None, help="Write JSON output to file")
    args = parser.parse_args()

    explicit_names = {n.strip() for n in args.names.split(",") if n.strip()} if args.names else None
    target = Path(args.target)
    baseline = Path(args.baseline) if args.baseline else None

    results: list[dict[str, Any]] = []
    if target.is_dir():
        files = sorted(
            [p for p in target.glob("*.txt") if re.match(r"^\d+화", p.name)]
        ) or sorted(list(target.glob("*.txt")) + list(target.glob("*.md")))
        for f in files:
            results.append(
                audit_text(
                    f.read_text(encoding="utf-8"),
                    f.name,
                    None,
                    args.mode,
                    args.min_chars,
                    args.max_chars,
                    explicit_names,
                )
            )
    else:
        b_text = baseline.read_text(encoding="utf-8") if baseline and baseline.exists() else None
        results.append(
            audit_text(
                target.read_text(encoding="utf-8"),
                target.name,
                b_text,
                args.mode,
                args.min_chars,
                args.max_chars,
                explicit_names,
            )
        )

    corpus_data = None
    if args.corpus_dir:
        corpus_data = corpus_forensics(Path(args.corpus_dir), explicit_names)

    payload = {"audits": results, "corpus_forensics": corpus_data}
    if args.json_out:
        Path(args.json_out).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        for r in results:
            print_report(r)
        if corpus_data:
            print("=" * 64)
            print(f"CORPUS FORENSICS ({len(corpus_data['files'])} files, {corpus_data['narration_blocks_total']} narr blocks)")
            print(f"  Stock Tells : {corpus_data['stock_tells']}")
            print(f"  Crutch Advs : {corpus_data['crutch_adverbs']}")
            print(f"  Name Openers: {corpus_data['top_name_openers'][:8]}")
            print(f"  Top 2-grams : {corpus_data['top_bigrams'][:12]}")
            print(f"  Top 3-grams : {corpus_data['top_trigrams'][:10]}")


if __name__ == "__main__":
    main()
