# Project Novel — 10단계 문학 머신 & 연재 작업공간 (Private)

> **보안 안내**: 비배포(Private) 개인 창작·자동화 저장소입니다. GitHub 저장소 설정(`Settings > General > Danger Zone`)에서 **Visibility: Private** 상태를 유지하세요.

---

## 폴더 구조

```text
project-novel/
├── skills/                         # 이식 가능한 문학 머신 3종 스킬
│   ├── literature-machine/         # 10단계 총괄 오케스트레이터 + 자가검진 체커 (novel_checker.py)
│   ├── narrative-forge/            # 외부 레퍼런스 그랩 + 3트랙 발산 사건 조합기
│   └── korean-humanizer/           # v3.0 심층 포렌식 + 가산형 인간 질감 + 코퍼스 n-gram 감사
├── novel/                          # 소설 본편 + 바이블 + 작업 아티팩트
│   ├── 1화 - 경계.txt
│   ├── 2화 - 섭동.txt
│   ├── 3화 - 파동.txt
│   ├── bible/                      # world, characters, voice, ledger, future_arc, canon.json, dynamic_banlist
│   └── work/                       # briefs/, drafts/, audits/
├── setup.ps1                       # Windows용 스킬 설치 / 역동기화 스크립트
└── setup.sh                        # macOS / Linux용 스킬 설치 / 역동기화 스크립트
```

---

## 다른 컴퓨터에서 바로 작업 시작하기 (3줄 세팅)

사전 요구사항: `git`, `Python 3.10+`

### Windows (PowerShell)
```powershell
git clone https://github.com/gbear1220/project-novel.git
cd project-novel
.\setup.ps1
```
*(Claude Code / Codex 폴더에도 함께 복사하려면 `.\setup.ps1 -AllAgents`)*

### macOS / Linux
```bash
git clone https://github.com/gbear1220/project-novel.git
cd project-novel
bash ./setup.sh
```
*(Claude Code / Codex 폴더에도 함께 복사하려면 `bash ./setup.sh --all-agents`)*

---

## 여러 컴퓨터 오가며 집필하는 일상 워크플로우

1. **작업 시작 전 (최신 본문·스킬 당겨오기)**
   ```powershell
   git pull
   .\setup.ps1        # macOS/Linux는 bash ./setup.sh
   ```
2. **집필 & 자가 검진 실행**
   - 에이전트에게 `./novel` 폴더 기준으로 4화 서사 흐름을 던지고 `literature-machine` 파이프라인 실행.
   - 또는 터미널에서 직접 결정적 체커 실행:
     ```powershell
     python ~/.agents/skills/literature-machine/scripts/novel_checker.py `
       --novel-dir ./novel --episode 4 --target ./novel/work/drafts/ep04_draft.txt --hook-type B
     ```
3. **작업 종료 후 (스킬을 수정했다면 역동기화 포함해 푸시)**
   ```powershell
   .\setup.ps1 -PushBack   # ~/.agents/skills 수정분을 ./skills로 반영 (macOS/Linux: bash ./setup.sh --push-back)
   git add -A
   git commit -m "feat: add episode 4 and update canon"
   git push
   ```
