# AIRS v0.4.0

[English README](README.md)

AIRS(AI-native Repository Standard)는 에이전트에 종속되지 않는 저장소 운영 규칙과 로컬 CLI를 결합합니다. CLI는 ChatGPT 구독으로 로그인한 Codex, Google 구독으로 로그인한 Antigravity를 실행합니다. OpenAI·Gemini 개발자 API는 호출하지 않습니다. 단, 선택적으로 사용하는 Jev 라우터는 TypeSafe API 키가 필요합니다.

핵심 원칙은 **문맥을 소유하는 가장 좁은 범위에 둔다**는 것입니다. 저장소가 지속적인 사실의 원본이며 채팅 기록은 프로젝트 기억을 대신하지 않습니다. v0.1 표준은 계속 호환성 기준이고, v0.4.0은 제한된 범위의 검토와 운영 점검을 추가합니다.

## 동작 구조

```text
작업 계약(Task Contract)
  → 명백한 작업은 규칙으로 분류
  → 애매한 작업만 Jev로 평가
  → 정책 엔진이 provider·tier·검토 여부 최종 결정
  → Codex CLI 또는 agy CLI 실행
  → 변경 파일만 다른 모델로 검토(필요할 때)
  → 검증 명령 실행 및 .airs/history/에 기록
```

Jev는 `task_type`, `complexity`, `risk`, `reasoning_need`, `review_need`를 평가하는 신호일 뿐입니다. Jev가 에이전트를 실행하거나 정책의 최소 안전 수준을 낮출 수는 없습니다. `light`·`medium`·`high`·`ultra`는 추상적인 모델 단계이며 실제 모델과 추론 수준은 `airs.yaml`에서 매핑합니다.

| 단계 | Codex 기본값 | Antigravity 기본값 |
|---|---|---|
| light | `gpt-5.6-luna` / low | `gemini-3.8-flash-low` |
| medium | `gpt-5.6-terra` / medium | `gemini-3.8-flash-medium` |
| high | `gpt-5.6-sol` / high | `gemini-3.8-flash-high` |
| ultra | `gpt-6-astra` / xhigh | `gemini-3.8-flash-high` |

사용 가능한 모델은 구독 계정과 CLI 버전에 따라 다릅니다. Codex의 `/model` 메뉴와 `agy models`를 확인하고 필요하면 YAML 매핑을 조정하세요.

## 설치와 비밀 키

Python 3.11+, `uv`, 구독 계정으로 로그인된 `codex`와 `agy`가 필요합니다. 저장소에서 다음을 실행합니다.

```bash
uv sync --extra dev
mkdir -p ~/.config/airs
chmod 700 ~/.config/airs
cp .env.example ~/.config/airs/.env
chmod 600 ~/.config/airs/.env
# ~/.config/airs/.env의 JEV_API_KEY= 값을 본인의 TypeSafe 키로 수정
uv tool install .
```

`routing.jev.api_key_env: JEV_API_KEY`는 키 값이 아닌 환경변수 이름입니다. 실제 키는 Git 저장소 밖의 `~/.config/airs/.env`에 넣으세요. AIRS가 실행할 때마다 파일을 읽으므로 새 터미널에서 다시 입력할 필요가 없습니다. 프로세스 환경변수, 대상 프로젝트의 `.env`, 사용자 설정 `.env` 순으로 찾습니다. 프로젝트 `.env`를 쓸 경우 반드시 그 프로젝트의 `.gitignore`에 추가하세요. 작업 내용을 에이전트에 전달할 때 키 변수를 제거하지만, 작업 공간의 파일 자체는 에이전트가 볼 수 있으므로 사용자 설정 경로가 더 안전합니다.

기본 Jev 엔드포인트는 TypeSafe의 `https://api.typesafe.ai/v1/systemone`이며 모델은 `jev-latest`입니다. 애매한 작업의 제목·목표·제약 등은 Jev로 전송되므로 해당 항목에 비밀 값을 넣지 마세요. API 키 값은 `airs.yaml`, 예제 파일, Git 추적 파일에 넣지 않습니다.

기존 설치를 이 체크아웃의 새 버전으로 교체할 때는 다음을 실행합니다.

```bash
uv tool install --force --reinstall .
```

## 일상적인 사용

대상 프로젝트 디렉터리에서 요청 한 줄로 시작할 수 있습니다. 매번 `task.yaml`을 만들 필요는 없습니다.

```bash
cd /path/to/target-repository
airs plan -p "로그인 오류에 대한 회귀 테스트를 추가해줘"
airs run -p "로그인 오류에 대한 회귀 테스트를 추가해줘" --verify-cmd "git diff --check"
airs status
```

`plan`은 실행 없이 경로를 보여주고, `run`은 주 에이전트·필요한 교차 검토·검증을 순서대로 실행합니다. `--provider codex|antigravity`, `--tier light|medium|high|ultra`, `--no-review`를 사용할 수 있지만 위험도가 높은 작업의 정책 최소값은 약화할 수 없습니다. `run`, `review`, `verify`에는 `--dry-run`이 있습니다. 상세 제약이나 재현 가능한 검증이 필요할 때만 `examples/task.yaml`과 `schemas/task-contract.schema.json`을 참고해 작업 계약을 작성하세요.

```bash
airs run TASK.yaml
airs verify TASK.yaml
airs status --run-id RUN_ID
```

## v0.4.0의 변경 파일 검토

`run`은 실행 전에 이미 수정돼 있던 파일의 상태를 기억하고, 주 에이전트가 새로 변경한 파일만 다른 모델에 전달합니다. 검토 실패 후에도 독립적으로 실행 가능한 검증 명령은 계속 실행합니다. 검토 대상이 없거나 기본 한도인 12개 파일을 초과하면 저장소 전체를 무작정 훑지 않고 실패로 알려줍니다.

기존 실행을 다시 검토할 때는 실행 ID를 지정하세요. 주 에이전트와 Jev를 다시 실행하지 않습니다. 새 실행 기록에는 검토 파일의 해시도 저장해 이후 파일이 바뀌면 조용히 다른 내용을 검토하지 않도록 막습니다. 직접 검토할 때는 `--file`을 반복해 범위를 지정할 수 있습니다. 파일을 지정하지 않으면 현재 Git 변경 파일만 대상으로 삼습니다.

```bash
airs review --run-id RUN_ID --provider antigravity
airs review -p "프로젝트 개요 문서의 변경을 검토해줘" \
  --file docs/PROJECT_OVERVIEW.md --file README.md --provider antigravity
```

Antigravity 검토는 계획 모드와 터미널 샌드박스를 사용하고, 파일 읽기 도구로 지정된 파일을 확인하도록 요청합니다. 기본 제한은 120초, 도구 호출 20회, 입력 토큰 120,000개입니다. 실행 중 파일 읽기 횟수와 입력 토큰을 표시합니다. 권한 거부·시간 초과·빈 답변은 `agy` 종료 코드가 0이어도 실패로 처리합니다. 전역 `permissions.allow` 설정은 다른 프로젝트에도 적용되므로 필요한 명령만 신중하게 허용하고 `--dangerously-skip-permissions`를 일상적인 검토에 사용하지 마세요.

현재 파일 전용 검토 흐름은 삭제된 파일의 diff를 검토하지 못합니다. 이 경우 별도로 검토 범위를 준비해야 합니다.

## 점검과 실행 기록

```bash
airs doctor
airs doctor --offline
airs history prune                    # 기본 30일보다 오래된 기록 미리보기
airs history prune --older-than 60 --apply
airs history scrub RUN_ID             # 민감 내용 제거 미리보기
airs history scrub RUN_ID --apply
```

`doctor`는 Jev 키의 존재 여부만 표시하고 값은 출력하지 않습니다. Codex·Antigravity CLI와 로그인을 확인하며, `agy models` 목록에서 설정된 모델을 찾습니다. `--offline`은 로그인·모델 목록 호출을 생략합니다. Codex 모델 가용성은 자동으로 확정하지 못하므로 실제 `/model` 메뉴를 확인하세요.

실행 기록은 대상 프로젝트의 `.airs/history/`에 저장됩니다. 이 경로를 대상 저장소의 `.gitignore`에 추가하세요. 기록에는 작업 문구와 에이전트 출력이 포함될 수 있습니다. AIRS는 기록 파일을 소유자 전용 권한으로 원자적으로 저장합니다. `prune`과 `scrub`은 기본적으로 미리보기이며 `--apply`를 붙여야 실제 변경합니다. `scrub`한 기록은 `review --run-id`에 다시 사용할 수 없습니다.

## 저장소 표준과 개발

이 저장소에는 v0.1의 규범 문서(`standards/`), 스택 프로필(`profiles/`), 정식 스킬(`.agents/skills/`), 복사 가능한 템플릿(`templates/`)이 함께 있습니다. 대상 저장소에는 필요한 규칙과 스킬만 가져오고, `AGENTS.md`는 긴 규칙집 대신 관련 문서로 안내하는 역할을 맡깁니다. 활성 작업은 `tasks/CURRENT.md`에 재개 가능한 상태로 남깁니다. 위험하거나 큰 작업일수록 Spec·Plan·Tasks·ADR을 적정 수준으로 작성합니다. 다른 저장소의 문맥은 필요할 때만 읽습니다.

개발 검증은 다음과 같습니다.

```bash
uv run --extra dev pytest
uv run python -m compileall -q src tests
```

테스트는 Jev 전송을 모의 처리하고 에이전트 실행은 드라이런/모의 결과를 사용하므로 구독 사용량을 소모하지 않습니다. AIRS v0.4.0은 로컬 우선 참조 구현입니다. 앞으로는 라우팅 평가 데이터, 재시도 정책, 모델 가용성 확인, 삭제 파일 diff 검토를 고도화할 수 있습니다.
