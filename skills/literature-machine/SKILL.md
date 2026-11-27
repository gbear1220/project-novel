---
name: literature-machine
description: >-
  작가의 10단계 창작 파이프라인을 총괄하는 마스터 문학 머신 스킬.
  원시 서사 흐름 접수 → 외부 그랩·사건 조합(narrative-forge) → 7,000~10,000자 비수렴 집필 및 심층 휴머나이징(korean-humanizer v3)
  → 2계층 자가 검진 머신(결정적 체커 novel_checker.py + 4중 적대적·연속성·독자패널 감사) → 총괄 편집장 직접 최종 교열 및 캐논 갱신까지 완결한다.
  "문학 머신", "다음 화 써줘", "서사 가공해줘", "자가 검진 돌려줘", "원고 체크해줘" 요청에 사용.
license: MIT
metadata:
  category: writing
  locale: ko-KR
  version: 1.0.0
  companions: narrative-forge, korean-humanizer
---

# Literature Machine (v1.0 — 10단계 완결형 창작 · 비수렴 · 자가검진 파이프라인)

작가의 서사 아이디어를 받아 외부 현실·문학 레퍼런스와 결합해 날카로운 재미를 불어넣고, AI 특유의 수렴 문체와 슬롭을 소거하며, **과거·현재·미래 전개와 세계관 정합성까지 자가 검진 머신으로 통과시킨 뒤** 최종 원고를 납품하는 마스터 오케스트레이터다.

## 10단계 파이프라인 지도 (사용자 워크플로우 1:1 매칭)

| 단계 | 작업 | 실행 주체 / 도구 | 산출물 / 통과 조건 |
|---|---|---|---|
| **1. 원시 흐름 접수** | 작가가 던진 거친 줄거리·장면 메모·대사 아이디어 접수 | 메인 에이전트 + `bible/*` 로드 | 현재 좌표 및 목표 회차 `N` 확정 |
| **2. 외부 그랩 & 사건 조합** | `narrative-forge` Stage B~C 가동: `search_web`으로 과학사·현실 제도·웹소설·인간 심리 기제 수집 + 3트랙 발산 조합 | `narrative-forge` (`search_web`) | 세계관 토착화된 비수렴 사건 구조 |
| **3. 명확한 방향성 가공** | `narrative-forge` Stage D: `Yes, but/No, and` 비율, 엇박자, 서브텍스트, 훅, 미래 비밀 잠금까지 박은 브리프 생성 | `work/briefs/epNN_brief.md` | 7,500~9,200자 장면별 예산 확정 |
| **4. AI 슬롭 최소화 초고** | `bible/voice.md` 원문 앵커(Exemplar) + `characters.md` 8차원 보이스 + `dynamic_banlist.md` 주입 하에 초고 집필 | `work/drafts/epNN_draft.txt` | **절대 7,000~10,000자(공백 포함)** |
| **5. 분량·리듬 조율** | 7,000자 미만이면 사건 마찰·서브텍스트 대화로 보강(패딩 금지), 10,000자 초과 시 중복 해설 적출 | `korean-humanizer` v3 | **목표 7,500~9,200자 (허용 7,000~10,000)** |
| **6. 단일 수렴 소거 + 인간 질감** | `M-1~M-8` 수렴 지문 제거 + `N-1~N-4`(서브텍스트·불완전 구어·전용 버릇·통사 비대칭) 주입 | `korean-humanizer` v3 + `fiction-humanizer.md` | 문두 `[이름]+조사` ≤20%, `-다.` 편중 해소 |
| **7. 자가 검진 머신 설계·로드** | **Layer 1(결정적 코드 체커)** + **Layer 2(4인 적대적/연속성/독자패널/목소리 감사)** 동시 준비 | `novel_checker.py` + `self-audit-protocol.md` | 과거·현재·미래·세계관·AI지문 동시 표적화 |
| **8. 체커 전수 가동** | ① `novel_checker.py` 실행 ② `invoke_subagent` 4병렬(또는 `cross_model_review.py` 이종 모델) 감사 실행 | `work/audits/epNN_*` | Exit Code 0 목표, 4대 시맨틱 리포트 수합 |
| **9. 직접 재검증 (총괄 편집장)** | 메인 에이전트가 원문·체커 결과·서브에이전트 지적을 직접 대조 검증해 수술적 수정 후 체커 재실행 | 최종 검수 + `canon.json`/`ledger.md`/`dynamic_banlist.md` 갱신 | **Hard Fail 0건** + 문학적 하이라이트 무손상 확인 |
| **10. 최종본 납품** | 완결 원고를 작품 루트에 저장하고 간결한 검수 영수증 보고 | `<작품_폴더>/<N>화 - <제목>.txt` (예: `./novel/<N>화 - <제목>.txt`) | 분량·체커·전후방 정합성·수정 내역 보고 |

---

## Step 7~8: 2계층 자가 검진 머신 실행 상세

### Layer 1: 결정적 기계 체커 (`scripts/novel_checker.py`)
항상 **Step 4/6 직후**와 **Step 9 최종 수정 후** 최소 2회 실행한다:

```powershell
python ~/.agents/skills/literature-machine/scripts/novel_checker.py `
  --novel-dir "<작품_폴더>" `
  --episode <N> `
  --target "<초고_파일_경로>" `
  --hook-type <A|B|C|D|E> `
  --min-chars 7000 --max-chars 10000
```

이 체커가 자동 판정하는 항목:
1. **분량 계약**: 공백 포함 `7,000 ~ 10,000자` (이탈 시 Exit Code 2 HARD FAIL).
2. **한국어 AI 지문 & 심층 구조 (`A~M`)**: 번역투, 괄호 병기, 연결어미 쉼표, 문두 `[이름]+조사` 비율(`M-1`), `-다.` 편중·엔트로피(`M-2`), 범용 신체반응 크러치(`M-3`), 완충 부사(`M-4`), 대사 비중(`M-5`), 문단 균일성(`M-6`), 부정 대구(`M-7`).
3. **동적 코퍼스 금지어 충돌**: 기존 완결 화들(`1화~N-1화`)에서 이미 포화된 어구·동작이 다시 누적되지 않는지 교차 검사.
4. **과거·현재·미래 캐논 컴파일러 (`bible/canon.json`)**:
   - 사망/이탈 인물의 부적절한 현현 검사
   - **미래 비밀 조기 유출(`future_locked_secrets`)** 및 인물별 **지식 한계(`knowledge_limits`)** 위반 시 HARD FAIL
   - **시대·세계관 어긋남(`anachronism_traps`)** 탐지 (예: 복식·소품·타 인물 어휘 수준 불일치)
   - **기한 도래 미회수 복선(`promises`)** 경보
   - **최근 4화 엔딩 훅 중복(`ending_hooks`)** 차단 (중복 시 HARD FAIL)

*(신규 화가 확정될 때마다 `--build-banlist`로 `bible/dynamic_banlist.md`를 즉시 재생성한다.)*

### Layer 2: 4중 시맨틱 감사 (멀티 에이전트 + 선택적 이종 모델)
Layer 1을 통과한 초고는 단일 모델/단일 컨텍스트의 맹점을 깨기 위해 [references/self-audit-protocol.md](./references/self-audit-protocol.md)의 프롬프트로 **`invoke_subagent` 4개를 병렬 실행**한다 (`research` 또는 격리된 `self` 서브에이전트 활용):
1. **연속성·세계관·미래정합성 감사관**: 1~(N-1)화 요약, `canon.json`, `future_arc.md`, `world.md`를 대조해 인과 구멍·인식론 오류(`L-9`)·복선 균열을 색출.
2. **무자비한 적대적 편집자 (Adversarial Editor)**: 무조건 500~800자 삭감 대상을 지목해 `OVER-EXPLAIN / REDUNDANT / STOCK-TELL / PURPLE-PROSE / GENERIC / FAT`로 분류.
3. **4인 독자 패널 (Reader Panel)**: 상업 웹소설 독자 / 문예지 편집자 / 동료 판타지 작가 / 일반 감성 독자 4명의 시선에서 **지루한 구간·개그 타율·하차 위험**을 판정 (의견 충돌 지점이 핵심 수정 포인트).
4. **비수렴 · 대사 표지 지우기 감사관**: 대사만 떼어놓고 누가 말했는지 가려지는지(8차원 분화), `Yes, but/No, and` 및 엇박자가 살았는지 점검.

*(추가로 이종 모델 교차 검증이 가능할 때는 `scripts/cross_model_review.py --probe`로 `codex` / `claude` CLI 가용 여부를 확인한 뒤 보조 비평을 받을 수 있다.)*

---

## Step 9: 총괄 편집장(메인 에이전트) 직접 최종 검증 수칙

기계와 서브에이전트 지적을 **맹목적으로 전부 반영하지 않는다.** 메인 에이전트가 직접 원문을 정독하며 아래 3가지 원칙으로 최종 수정을 집도한다:
1. **퍼플 프로즈 반동 경계**: AI 흔적 지적을 고치려다 모든 동작을 화려하게 비틀지 말 것. 평범한 동작은 평범하게 둔다.
2. **개그·서정·이과 추론의 톤 분리**: 아이작의 물리 연산 근거(`관측→가설→검증 한계→유보`)와 3단 코미디 낙차, 엘프·용의 서정/위압감을 기계적 다이어트로 훼손하지 않는다.
3. **종료 조건(Stopping Condition)**: `novel_checker.py` **Hard Fail = 0건**이면서, 시맨틱 감사에서 치명적 결함(인과 오류·설교조·지루한 중반)이 0건에 수렴하면 과잉 수정을 멈추고 즉시 납품한다.
