# 프로젝트별 AIRS 적용 가이드

AIRS에는 두 층이 있습니다. 설치된 `airs` 명령은 작업을 계획·실행·검토하고, **각 프로젝트 저장소**의 `AGENTS.md`·`tasks/CURRENT.md` 등은 해당 프로젝트의 사실과 규칙을 전달합니다. 프로젝트 문서를 AIRS 저장소에 몰아넣지 않습니다. AIRS는 주 에이전트에게 프로젝트 루트의 `AGENTS.md`와 필요한 경우 `tasks/CURRENT.md`를 읽도록 안내합니다. 교차 검토자는 변경 파일 범위만 받으며 전체 프로젝트 문서를 자동으로 훑지 않습니다.

## 파일의 역할

| 파일 | 내용 | 필수 여부 |
|---|---|---|
| `AGENTS.md` | 프로젝트 목적, 안정적인 규칙, 관련 문서로 가는 길잡이 | AIRS v0.1 표준 적용 시 필수 |
| `tasks/CURRENT.md` | 지금의 목표, 진행 상태, 검증 결과, 다음 단계 | AIRS v0.1 표준 적용 시 필수 |
| `docs/ARCHITECTURE.md` | 오래 유지되는 구조와 경계 | 구조 설명이 필요할 때 |
| `docs/adr/`·`specs/active/` | 설계 결정과 중간 이상 작업의 명세 | 해당 작업이 있을 때 |
| `.agents/skills/` | 반복되는 작업 방식 | 실제 사용하는 스킬만 |
| `airs.project.yaml` | AIRS 표준의 프로젝트 메타데이터 | 선택 사항 |
| `airs.yaml` | 이 프로젝트에서 실행할 AIRS CLI 설정의 덮어쓰기 | 선택 사항 |

`airs.project.yaml`과 `airs.yaml`은 용도가 다릅니다. 이전 템플릿의 `templates/repository/airs.yaml`은 프로젝트 메타데이터였지만 CLI 설정과 이름이 겹쳐, 지금은 `airs.project.yaml`로 변경했습니다. 이미 복사한 프로젝트에서는 내용을 확인한 뒤 **메타데이터 파일만** 이름을 바꾸세요. 라우팅·모델·시간 제한 설정이 들어 있는 실제 CLI `airs.yaml`은 그대로 둡니다.

## 한 프로젝트에 적용하기

1. 대상 저장소의 기존 `AGENTS.md`, 문서, `.gitignore`, 작업 중인 변경 사항을 확인합니다. 기존 파일을 템플릿으로 덮어쓰지 마세요.
2. AIRS 저장소의 `templates/repository/`에서 필요한 파일만 복사하거나 기존 문서에 병합합니다. 모든 빈 폴더와 예제를 복사할 필요는 없습니다.
3. `AGENTS.md`의 `{{PLACEHOLDER}}`를 해당 프로젝트의 실제 목적, 명령, 경계로 교체합니다. 긴 아키텍처나 현재 작업 로그를 여기에 붙이지 않고 각각의 문서로 연결합니다.
4. `tasks/CURRENT.md`에 실제 현재 상태를 기록합니다. 진행 중인 일이 없다면 `Status: none`과 다음에 확인할 항목만 남깁니다.
5. 필요한 프로필(예: `profiles/python-fastapi/PROFILE.md`)이나 스킬만 가져옵니다. 원본을 참조하는 방식이라면 대상 프로젝트에서 접근 가능한 경로와 버전을 명시합니다.
6. `.gitignore`에 `.airs/`와 `.env`를 추가합니다. Jev 키 값은 기존 사용자 설정 `~/.config/airs/.env`에 두고 프로젝트 문서나 Git에 넣지 않습니다.
7. `airs plan -p "작은 작업"`으로 경로를 확인한 뒤, `airs run -p "작은 작업" --verify-cmd "..."`로 한 번 실행합니다. `airs status`에서 기록을 확인하고, 필요하면 `airs review --run-id RUN_ID --provider antigravity`로 검토만 재시도합니다.

## FastAPI 프로젝트 예시

프로젝트 구조가 `app/`, `tests/`, `pyproject.toml`인 경우 다음처럼 시작할 수 있습니다.

```text
my-api/
├── AGENTS.md
├── tasks/CURRENT.md
├── docs/ARCHITECTURE.md
├── .gitignore
├── app/
├── tests/
└── pyproject.toml
```

`AGENTS.md`에는 이 정도의 길잡이면 충분합니다.

```markdown
# My API

FastAPI 기반 주문 API입니다. `app/`이 서비스 코드, `tests/`가 검증 코드입니다.

- 진행 상태: `tasks/CURRENT.md`
- 구조·외부 연동 경계: `docs/ARCHITECTURE.md`
- API 변경 시 요청·응답 호환성과 인증 경계를 확인합니다.
- 기본 검증: `uv run pytest tests/` 및 `git diff --check`
- 생성 파일은 직접 수정하지 않고, 관련 소스와 테스트만 먼저 살핍니다.
```

`tasks/CURRENT.md`에는 작업 중인 목표와 실제 검사 상태를 적습니다. 예: `Goal: 주문 취소 오류 수정`, `Passed: uv run pytest tests/test_orders.py`, `Next action: 실패한 통합 테스트 재확인`. 비밀 값이나 채팅 전문은 적지 않습니다.

대상 프로젝트에서 실행합니다.

```bash
cd /path/to/my-api
airs doctor
airs plan -p "주문 취소 오류에 대한 회귀 테스트를 추가해줘"
airs run -p "주문 취소 오류에 대한 회귀 테스트를 추가해줘" \
  --verify-cmd "uv run pytest tests/test_orders.py" \
  --verify-cmd "git diff --check"
airs status
```

매번 `task.yaml`을 만들 필요는 없습니다. 수용 기준·제약·여러 검증 단계가 필요한 중간 이상 작업에서는 `examples/task.yaml`을 바탕으로 작업 계약을 작성합니다.

## 프로젝트별 검토 시간 조정

기본 Antigravity 검토 제한은 600초(10분)입니다. 주 에이전트 실행과 Codex 검토에는 AIRS 자체의 시간 제한이 없습니다. 프로젝트마다 다르게 설정하려면 [예제 설정](examples/project-airs.yaml)을 대상 저장소의 `airs.yaml`로 복사해 값을 조정합니다. 시간 외에 도구 호출 20회와 입력 토큰 120,000개 제한이 남아 있으므로 먼저 실제 실행 기록을 보고 조정하세요. 기본 설정만으로 충분하면 프로젝트 `airs.yaml`은 만들지 않아도 됩니다.

CLI는 현재 디렉터리의 `airs.yaml`을 읽습니다. 다른 위치에서 실행하거나 설정을 명시하려면 `airs --config /path/to/my-api/airs.yaml run -p "..." --root /path/to/my-api`처럼 지정하세요. 설정 값이 없는 항목은 AIRS 기본값을 사용합니다. 프로젝트의 `airs.yaml`에는 키의 **값**을 넣지 않습니다.
