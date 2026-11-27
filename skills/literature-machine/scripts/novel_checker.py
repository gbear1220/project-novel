#!/usr/bin/env python3
"""
Literature Machine — Deterministic Self-Audit & Continuity Compiler CLI (v1.0)
Pure Python 3.10 stdlib-only.

Combines:
  1. Hard length gate (7,000 ~ 10,000 chars with spaces)
  2. Korean Humanizer v3 forensics (A~M taxonomy, M-1~M-7 structural metrics)
  3. Cross-episode dynamic corpus banlist builder & violation detector
  4. Deterministic Canon & Past/Present/Future Continuity Compiler (bible/canon.json):
     - Dead / absent character appearance check (outside flashbacks)
     - Future-locked secret premature leak guard (HARD FAIL)
     - Per-character knowledge limits check
     - Anachronism / register trap guard
     - Overdue / referenced promise (foreshadowing) ledger check
     - 5-episode ending hook rotation guard (HARD FAIL on duplicate)
     - Fact-lock checklist output

Usage:
  python novel_checker.py --novel-dir "<dir>" --build-banlist
  python novel_checker.py --novel-dir "<dir>" --episode 4 --target "<draft.txt>" [--hook-type B]
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Import Korean Humanizer v3 engine portably (sibling skill dir or user home)
_CANDIDATE_HUMANIZER_DIRS = [
    Path(__file__).resolve().parents[2] / "korean-humanizer" / "scripts",
    Path.home() / ".agents" / "skills" / "korean-humanizer" / "scripts",
    Path.home() / ".claude" / "skills" / "korean-humanizer" / "scripts",
    Path.home() / ".codex" / "skills" / "korean-humanizer" / "scripts",
]
for _p in _CANDIDATE_HUMANIZER_DIRS:
    if (_p / "audit_korean.py").exists():
        if str(_p) not in sys.path:
            sys.path.insert(0, str(_p))
        break

import audit_korean as ak  # noqa: E402


FLASHBACK_MARKERS = ("기억", "회상", "과거", "떠올", "예전", "전생", "옛날", "그때", "돌아보")


def load_canon(novel_dir: Path) -> dict[str, Any]:
    canon_path = novel_dir / "bible" / "canon.json"
    if not canon_path.exists():
        return {}
    return json.loads(canon_path.read_text(encoding="utf-8"))


def collect_character_names(canon: dict[str, Any]) -> set[str]:
    names: set[str] = set()
    for ch in canon.get("characters", []):
        if ch.get("name"):
            names.add(ch["name"])
        for alias in ch.get("aliases", []):
            if alias:
                names.add(alias)
    return names


def build_dynamic_banlist(novel_dir: Path) -> Path:
    canon = load_canon(novel_dir)
    char_names = collect_character_names(canon) or None
    corpus = ak.corpus_forensics(novel_dir, char_names)

    out_path = novel_dir / "bible" / "dynamic_banlist.md"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    lines = [
        "# 동적 코퍼스 금지 목록 (Dynamic Corpus Banlist)",
        "",
        f"> 자동 생성 기준: `{', '.join(corpus['files'])}` (서술 블록 {corpus['narration_blocks_total']}개 누적 분석)",
        "> 다음 화 집필 및 윤문 시 아래 **과다 누적 동작·부사·문두 패턴**의 재등장을 억제한다.",
        "",
        "## 1. 누적 범용 신체반응 크러치 (Stock Physical Tells — 화당 합산 2회 이하 권장)",
        "",
    ]
    for label, cnt in corpus["stock_tells"]:
        lines.append(f"- `{label}`: 누적 **{cnt}회**")

    lines += [
        "",
        "## 2. 누적 시간·완충 부사 (Crutch Adverbs)",
        "",
    ]
    for adv, cnt in corpus["crutch_adverbs"]:
        lines.append(f"- `{adv}`: 누적 **{cnt}회**")

    lines += [
        "",
        "## 3. 과다 사용된 문두 `[인물명+조사]` 시작어 (20% 이하 억제 대상)",
        "",
    ]
    for op, cnt in corpus["top_name_openers"]:
        lines.append(f"- `{op}`: 누적 **{cnt}회**")

    lines += [
        "",
        "## 4. 서술부 반복 2-gram / 3-gram 구절 (클리셰 고착 경계)",
        "",
    ]
    for gram, cnt in corpus["top_bigrams"][:15]:
        lines.append(f"- `2-gram` \"{gram}\": {cnt}회")
    for gram, cnt in corpus["top_trigrams"][:10]:
        lines.append(f"- `3-gram` \"{gram}\": {cnt}회")

    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return out_path


def find_context_snippet(text: str, keyword: str, window: int = 35) -> list[tuple[int, str]]:
    hits: list[tuple[int, str]] = []
    for idx, line in enumerate(text.splitlines(), 1):
        for m in re.finditer(re.escape(keyword), line):
            s = max(0, m.start() - window)
            e = min(len(line), m.end() + window)
            hits.append((idx, line[s:e].strip()))
    return hits


def run_continuity_checks(
    text: str,
    episode: int,
    canon: dict[str, Any],
    hook_type: str | None,
) -> dict[str, Any]:
    hard_fails: list[str] = []
    warnings: list[str] = []
    notes: list[str] = []

    if not canon:
        warnings.append("[CANON_MISSING] bible/canon.json을 찾지 못해 캐논 정합성 검사를 건너뛰었습니다.")
        return {"hard_fails": hard_fails, "warnings": warnings, "notes": notes}

    lines = text.splitlines()

    # 1. Dead or absent characters
    for ch in canon.get("characters", []):
        cname = ch.get("name", "")
        status = ch.get("status", "alive")
        dead_ep = ch.get("dead_ep")
        absent_from = ch.get("absent_from_ep")
        absent_until = ch.get("absent_until_ep")
        aliases = [cname] + ch.get("aliases", [])
        aliases = [a for a in aliases if a]

        should_be_absent = (
            (status == "dead" and dead_ep is not None and episode > int(dead_ep))
            or (
                absent_from is not None
                and episode >= int(absent_from)
                and (absent_until is None or episode < int(absent_until))
            )
        )
        if should_be_absent:
            for idx, line in enumerate(lines, 1):
                if any(re.search(rf"{re.escape(a)}(?:은|는|이|가|의|을|를|에게|도)?(?:\s|[,.!?\”\"])", line) for a in aliases):
                    if not any(fb in line for fb in FLASHBACK_MARKERS):
                        hard_fails.append(
                            f"[CONTINUITY_PRESENCE] L{idx}: 사망/부재 설정 인물 '{cname}'(status={status})이 회상 표지 없이 등장 -> '{line[:50]}'"
                        )

    # 2. Future-locked secrets premature leak guard (HARD FAIL)
    for sec in canon.get("future_locked_secrets", []):
        unlock_ep = sec.get("unlock_ep")
        if unlock_ep is not None and episode < int(unlock_ep):
            sid = sec.get("id", "secret")
            desc = sec.get("description", "")
            for kw in sec.get("forbidden_keywords", []):
                if not kw:
                    continue
                hits = find_context_snippet(text, kw)
                if hits:
                    sample = f"L{hits[0][0]}: ...{hits[0][1]}..."
                    hard_fails.append(
                        f"[FUTURE_SECRET_LEAK] '{sid}' (해금 {unlock_ep}화 예정) 금지 키워드 '{kw}' 조기 유출 ({len(hits)}건, {sample}) — {desc}"
                    )

    # 3. Character knowledge limits check
    quote_report_cues = ("어쩌고", "뭔지", "무슨 소리", "알아들을 수")
    for kl in canon.get("knowledge_limits", []):
        until_ep = kl.get("until_ep")
        if until_ep is not None and episode <= int(until_ep):
            char_name = kl.get("character", "")
            for kw in kl.get("forbidden_keywords", []):
                if not kw:
                    continue
                for idx, line in enumerate(lines, 1):
                    if kw not in line:
                        continue
                    if any(cue in line for cue in quote_report_cues):
                        continue
                    prev_line = lines[idx - 2] if idx >= 2 else ""
                    next_line = lines[idx] if idx < len(lines) else ""
                    window = f"{prev_line}\n{line}\n{next_line}"
                    if char_name in line or (line.strip().startswith(("“", '"')) and char_name in window and "아이작" not in prev_line and "승민" not in prev_line):
                        warnings.append(
                            f"[KNOWLEDGE_BOUNDARY] L{idx}: '{char_name}'은 {until_ep}화까지 '{kw}'를 모르는 상태입니다 -> '{line[:55]}'"
                        )

    # 4. Anachronism & costume/world-rule traps
    for trap in canon.get("anachronism_traps", []):
        pattern = trap.get("pattern", "")
        if not pattern:
            continue
        scope_chars = trap.get("exclude_if_near", [])
        for idx, line in enumerate(lines, 1):
            if re.search(pattern, line):
                if scope_chars and any(sc in line for sc in scope_chars):
                    continue
                warnings.append(
                    f"[WORLD_TRAP:{trap.get('id','trap')}] L{idx}: {trap.get('reason','설정 충돌 의심')} -> '{line[:55]}'"
                )

    # 5. Promises / Foreshadowing overdue & active tracking
    referenced_promises: list[str] = []
    for pr in canon.get("promises", []):
        if pr.get("paid_ep") is not None:
            continue
        pid = pr.get("id", "promise")
        planted_ep = int(pr.get("planted_ep", 1))
        due_by = pr.get("due_by_ep")
        kws = pr.get("keywords", [])
        matched = any(kw in text for kw in kws if kw)
        if matched:
            referenced_promises.append(f"{pid} ({pr.get('summary', '')})")
        if due_by is not None and episode >= int(due_by) and not matched:
            warnings.append(
                f"[PROMISE_DUE] '{pid}' (설치 {planted_ep}화, 회수/진전 권장 {due_by}화): 미언급 상태 — {pr.get('summary', '')}"
            )
    if referenced_promises:
        notes.append("현 회차에서 언급/진전된 활성 복선: " + "; ".join(referenced_promises))

    # 6. Ending hook rotation guard (last 4 episodes, non-E)
    if hook_type:
        ht = hook_type.strip().upper()
        recent_hooks = [
            (ep.get("episode"), ep.get("hook_type", "").upper())
            for ep in canon.get("episodes", [])
            if ep.get("episode") is not None and int(ep["episode"]) < episode and int(ep["episode"]) >= episode - 4
        ]
        if ht != "E":
            dupes = [f"{e}화({h})" for e, h in recent_hooks if h == ht]
            if dupes:
                hard_fails.append(
                    f"[HOOK_ROTATION] 엔딩 훅 유형 '{ht}'가 최근 4화 이내에 이미 사용됨: {', '.join(dupes)}"
                )
        notes.append(f"엔딩 훅 '{ht}' 검증 완료 (최근 기록: {recent_hooks})")

    # 7. Active fact locks reminder
    prev_facts: list[str] = []
    for ep in canon.get("episodes", []):
        if ep.get("episode") is not None and int(ep["episode"]) <= episode:
            for fl in ep.get("fact_locks", []):
                prev_facts.append(f"[{ep['episode']}화] {fl}")
    if prev_facts:
        notes.append("적용 불변 사실(Fact Locks): " + " | ".join(prev_facts[-6:]))

    return {"hard_fails": hard_fails, "warnings": warnings, "notes": notes}


def check_corpus_banlist_overlap(
    target_path: Path,
    novel_dir: Path,
    char_names: set[str] | None,
) -> dict[str, Any]:
    """Compare target episode's narration 2-grams & stock tells against prior episodes."""
    sibling_files = sorted(
        [p for p in novel_dir.glob("*.txt") if re.match(r"^\d+화", p.name) and p.resolve() != target_path.resolve()],
        key=lambda p: int(re.match(r"^(\d+)", p.name).group(1)),
    )
    prior_bigrams: dict[str, int] = {}
    for p in sibling_files:
        narr, _, _ = ak.classify_blocks(p.read_text(encoding="utf-8").splitlines())
        for g, c in ak.extract_narration_ngrams(narr, 2).items():
            prior_bigrams[g] = prior_bigrams.get(g, 0) + c

    target_narr, _, _ = ak.classify_blocks(target_path.read_text(encoding="utf-8").splitlines())
    target_bg = ak.extract_narration_ngrams(target_narr, 2)

    repeated_crutches = []
    for g, t_cnt in target_bg.most_common():
        p_cnt = prior_bigrams.get(g, 0)
        if p_cnt >= 3 and t_cnt >= 2:
            repeated_crutches.append({"phrase": g, "prior_count": p_cnt, "current_count": t_cnt})

    return {
        "prior_files_checked": [p.name for p in sibling_files],
        "cross_episode_repeats": repeated_crutches[:12],
    }


def render_markdown_report(
    audit_res: dict[str, Any],
    cont_res: dict[str, Any],
    overlap_res: dict[str, Any],
    episode: int,
    exit_code: int,
) -> str:
    verdict = {0: "PASS", 1: "PASS_WITH_WARNINGS", 2: "HARD_FAIL"}[exit_code]
    r = audit_res["rhythm"]
    d = audit_res["deep_forensics"]
    lines = [
        f"# 제{episode}화 자가 검진 기계 리포트 (`{verdict}`)",
        "",
        f"- **대상 파일**: `{audit_res['file']}`",
        f"- **분량(공백 포함 / 제외)**: **{audit_res['chars_with_spaces']:,}자** / {audit_res['chars_no_ws']:,}자 (`{audit_res['length_status']}`)",
        f"- **리듬 & 대사**: 대사 비중 `{r['dialogue_ratio_pct']}%` | 평균 문장 `{r['mean_sent_len']}자` (Std `{r['std_sent_len']}`, CV `{r['cv']}`) | 최대 연속 서술 `{r['max_narr_streak']}문장`",
        f"- **심층 포렌식(M)**: 문두 `[이름]+조사` `{d['m1_name_opener_count']}` (`{d['m1_name_opener_pct']}%`) | `-다.` 종결 `{d['m2_da_ending_pct']}%` (Ent `{d['m2_ending_entropy']}`) | 범용 신체반응 `{d['m3_stock_tells_total']}회` | 완충 부사 `{d['m4_crutch_adverbs_total']}회`",
        f"- **문체 감사 등급**: `{audit_res['grade']}` (S1={len(audit_res['s1_issues'])}, S2={len(audit_res['s2_warnings'])})",
        "",
        "## 1. HARD FAIL 항목 (납품 차단)",
    ]
    all_fails = [f"[STYLE:{x['code']}] {x['msg']}" for x in audit_res["s1_issues"]] + cont_res["hard_fails"]
    if not all_fails:
        lines.append("- 없음 (CLEAN)")
    else:
        for item in all_fails:
            lines.append(f"- **FAIL**: {item}")

    lines += ["", "## 2. WARNING 항목 (총괄 편집장 확인 필요)"]
    all_warns = [f"[STYLE:{x['code']}] {x['msg']}" for x in audit_res["s2_warnings"]] + cont_res["warnings"]
    if not all_warns:
        lines.append("- 없음")
    else:
        for item in all_warns:
            lines.append(f"- **WARN**: {item}")

    lines += ["", "## 3. 회차 간 교차 반복 어구 (이전 화 + 현 화 누적)"]
    if not overlap_res["cross_episode_repeats"]:
        lines.append("- 특이 누적 반복 없음")
    else:
        for item in overlap_res["cross_episode_repeats"]:
            lines.append(
                f"- `{item['phrase']}`: 이전 화 {item['prior_count']}회 + 현 화 {item['current_count']}회"
            )

    lines += ["", "## 4. 캐논 & 복선 메모"]
    for note in cont_res["notes"]:
        lines.append(f"- {note}")
    for info in audit_res["infos"]:
        lines.append(f"- {info}")

    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Literature Machine Deterministic Checker v1.0")
    parser.add_argument("--novel-dir", required=True, help="Root folder containing episodes and bible/canon.json")
    parser.add_argument("--target", default=None, help="Target draft/episode file to audit")
    parser.add_argument("--episode", type=int, default=1, help="Episode number being audited")
    parser.add_argument("--hook-type", default=None, help="Ending hook code A/B/C/D/E")
    parser.add_argument("--min-chars", type=int, default=7000)
    parser.add_argument("--max-chars", type=int, default=10000)
    parser.add_argument("--build-banlist", action="store_true", help="Rebuild bible/dynamic_banlist.md from corpus")
    parser.add_argument("--report-out", default=None, help="Optional path for markdown audit report")
    args = parser.parse_args()

    novel_dir = Path(args.novel_dir)
    if args.build_banlist:
        ban_path = build_dynamic_banlist(novel_dir)
        print(f"Dynamic banlist rebuilt: {ban_path}")
        if not args.target:
            sys.exit(0)

    if not args.target:
        parser.error("--target is required unless --build-banlist is used alone.")

    target_path = Path(args.target)
    text = target_path.read_text(encoding="utf-8")
    canon = load_canon(novel_dir)
    char_names = collect_character_names(canon) or None

    audit_res = ak.audit_text(
        text=text,
        name=target_path.name,
        baseline_text=None,
        mode="fiction",
        min_chars=args.min_chars,
        max_chars=args.max_chars,
        explicit_names=char_names,
    )
    cont_res = run_continuity_checks(text, args.episode, canon, args.hook_type)
    overlap_res = check_corpus_banlist_overlap(target_path, novel_dir, char_names)

    hard_fail_count = len(audit_res["s1_issues"]) + len(cont_res["hard_fails"])
    warn_count = len(audit_res["s2_warnings"]) + len(cont_res["warnings"])

    if hard_fail_count > 0:
        exit_code = 2
    elif warn_count > 3:
        exit_code = 1
    else:
        exit_code = 0

    md_report = render_markdown_report(audit_res, cont_res, overlap_res, args.episode, exit_code)

    if args.report_out:
        out_path = Path(args.report_out)
    elif (novel_dir / "work" / "audits").exists():
        out_path = novel_dir / "work" / "audits" / f"ep{args.episode:02d}_mechanical_audit.md"
    else:
        out_path = None

    if out_path:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(md_report, encoding="utf-8")
        print(f"Audit report saved: {out_path}")

    print(md_report)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
