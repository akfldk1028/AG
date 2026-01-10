# AutoGen Upstream Synchronization Guide

> **목적**: Microsoft AutoGen 업데이트와 호환성 유지를 위한 수정 사항 추적 및 동기화 가이드

## 1. 수정된 파일 목록

### 1.1 Python Backend (autogen_source/python/packages/)

| 파일 | 수정 유형 | 충돌 위험도 | 설명 |
|------|----------|------------|------|
| `autogen-agentchat/.../agents/_assistant_agent.py` | 확장 | 🟡 중간 | A2A 호환성을 위한 수정 |
| `autogen-studio/autogenstudio/a2a/agent.py` | **신규** | 🟢 낮음 | A2AAgent 구현체 (새 파일) |
| `autogen-studio/autogenstudio/a2a/registry.py` | **신규** | 🟢 낮음 | A2A 레지스트리 (새 파일) |
| `autogen-studio/autogenstudio/gallery/builder.py` | 확장 | 🟡 중간 | Gallery 자동 스캔 로직 추가 |
| `autogen-studio/autogenstudio/teammanager/teammanager.py` | 확장 | 🟡 중간 | A2A 팀 지원 추가 |
| `autogen-studio/autogenstudio/web/routes/a2a.py` | **신규** | 🟢 낮음 | A2A API 라우트 (새 파일) |
| `autogen-studio/autogenstudio/web/routes/gallery.py` | 확장 | 🟡 중간 | Gallery API 확장 |

### 1.2 Frontend (autogen-studio/frontend/src/)

| 파일 | 수정 유형 | 충돌 위험도 | 설명 |
|------|----------|------------|------|
| `components/footer.tsx` | 수정 | 🟢 낮음 | 버전 표시 수정 |
| `components/sidebar.tsx` | 수정 | 🟡 중간 | A2A 메뉴 추가 |
| **chat/agentflow/** | | | |
| `agentflow.tsx` | 대폭 수정 | 🔴 높음 | 패턴 시각화 시스템 |
| `PatternSelector.tsx` | **신규** | 🟢 낮음 | 패턴 선택 UI |
| **chat/agentflow/patterns/** | **모두 신규** | 🟢 낮음 | 패턴 로직 |
| `pattern-loader.ts` | 신규 | 🟢 | 패턴 JSON 로더 |
| `pattern-schema.ts` | 신규 | 🟢 | 패턴 스키마 정의 |
| `pattern-types.ts` | 신규 | 🟢 | TypeScript 타입 |
| `layout-generator.ts` | 신규 | 🟢 | 시각화 레이아웃 |
| `handoff-pattern.ts` | 신규 | 🟢 | Handoff 패턴 |
| `selector-pattern.ts` | 신규 | 🟢 | Selector 패턴 |
| `sequential-pattern.ts` | 신규 | 🟢 | Sequential 패턴 |
| **chat/team-runtime/** | **모두 신규** | 🟢 낮음 | 팀 런타임 로직 |
| `team-factory.ts` | 신규 | 🟢 | 팀 설정 생성 |
| `pattern-runtime.ts` | 신규 | 🟢 | 패턴 실행 로직 |
| `selector-config.ts` | 신규 | 🟢 | Selector 설정 |
| `swarm-config.ts` | 신규 | 🟢 | Swarm 설정 |
| `roundrobin-config.ts` | 신규 | 🟢 | RoundRobin 설정 |
| **teambuilder/builder/** | | | |
| `a2a-import-modal.tsx` | **신규** | 🟢 낮음 | A2A 에이전트 임포트 |
| `fields/team-fields.tsx` | 수정 | 🟡 중간 | 팀 필드 확장 |
| `fields/pattern-preview.tsx` | **신규** | 🟢 낮음 | 패턴 미리보기 |
| **chat/** | | | |
| `chat.tsx` | 수정 | 🔴 높음 | 채팅 UI 수정 |
| `runview.tsx` | 수정 | 🟡 중간 | 실행 뷰 수정 |

### 1.3 패턴 JSON 파일 (AG_Cohub/patterns/)

| 파일 | A2A 호환 | 설명 |
|------|----------|------|
| `01_sequential.json` | ✅ | RoundRobinGroupChat |
| `02_concurrent.json` | ✅ | 동시 실행 패턴 |
| `03_selector.json` | ✅ | SelectorGroupChat |
| `04_group_chat.json` | ✅ | 기본 그룹 챗 |
| `05_handoff.json` | ❌ | Swarm (tool calling 필요) |
| `06_magentic.json` | ❌ | MagenticOne (tool calling 필요) |
| `07_debate.json` | ✅ | SelectorGroupChat (토론) |
| `08_reflection.json` | ✅ | SelectorGroupChat (리플렉션) |
| `09_hierarchical.json` | ✅ | 계층적 패턴 |

---

## 2. 충돌 위험 분석

### 🔴 높은 위험 파일 (Upstream 업데이트 시 주의!)

```
1. agentflow.tsx
   - 이유: 전체 구조 변경, 패턴 시스템 통합
   - 대응: 수동 머지 필요, upstream 변경사항 우선 검토

2. chat.tsx
   - 이유: UI 로직 변경
   - 대응: diff 비교 후 선별적 머지
```

### 🟡 중간 위험 파일

```
1. teammanager.py - A2A 팀 로직 추가
2. builder.py - Gallery 자동 스캔 로직
3. sidebar.tsx - 메뉴 추가
4. team-fields.tsx - 필드 확장
```

### 🟢 낮은 위험 파일 (신규 생성 파일)

신규 파일은 upstream과 충돌 없음:
- `a2a/` 폴더 전체
- `patterns/` 폴더 전체
- `team-runtime/` 폴더 전체
- `PatternSelector.tsx`
- `a2a-import-modal.tsx`

---

## 3. Upstream 동기화 절차

### 3.1 사전 준비

```bash
# 1. 현재 변경사항 백업
git stash

# 2. upstream 리모트 추가 (최초 1회)
git remote add upstream https://github.com/microsoft/autogen.git

# 3. upstream 최신 정보 가져오기
git fetch upstream
```

### 3.2 동기화 수행

```bash
# 1. upstream 변경사항 확인
git log upstream/main --oneline -20

# 2. 변경된 파일 비교
git diff main..upstream/main --name-only | grep -E "(autogen-studio|autogen-agentchat)"

# 3. 충돌 위험 파일 먼저 확인
git diff main..upstream/main -- autogen_source/python/packages/autogen-studio/frontend/src/components/views/playground/chat/agentflow/agentflow.tsx

# 4. 안전한 파일 먼저 머지
git checkout upstream/main -- autogen_source/python/packages/autogen-core/
git checkout upstream/main -- autogen_source/python/packages/autogen-ext/

# 5. 충돌 파일 수동 머지
git merge upstream/main --no-commit
# 충돌 해결 후
git commit -m "chore: Merge upstream autogen updates"
```

### 3.3 패치 파일 생성 (백업용)

```bash
# 현재 수정사항을 패치로 저장
cd autogen_a2a_kit

# 전체 패치
git diff HEAD~20 > patches/all_changes.diff

# 파일별 패치
git diff HEAD~20 -- autogen_source/.../agentflow.tsx > patches/agentflow.diff
git diff HEAD~20 -- autogen_source/.../teammanager.py > patches/teammanager.diff
```

---

## 4. A2A 확장 아키텍처

### 4.1 핵심 원칙

1. **확장 우선**: 기존 코드 수정 최소화, 새 모듈 추가
2. **격리**: A2A 관련 코드는 `a2a/` 폴더에 집중
3. **플러그인 패턴**: 기존 시스템에 훅으로 연결

### 4.2 디렉토리 구조

```
autogen_a2a_kit/
├── docs/
│   └── UPSTREAM_SYNC.md       # 이 문서
├── patches/
│   ├── README.md              # 패치 사용법
│   └── *.diff                 # 패치 파일들
├── a2a_demo/                  # A2A 에이전트 데모
│   ├── poetry_agent/
│   ├── math_agent/
│   └── ...
├── AG_Cohub/                  # 패턴 정의
│   └── patterns/*.json
└── autogen_source/            # Microsoft AutoGen 포크
    └── python/packages/
        ├── autogen-agentchat/ # 최소 수정
        └── autogen-studio/    # A2A 확장
            └── autogenstudio/
                ├── a2a/       # ★ 신규 A2A 모듈
                └── web/routes/a2a.py
```

### 4.3 A2A Agent 상속 구조

```
BaseChatAgent (AutoGen 원본)
    └── A2AAgent (신규 - a2a/agent.py)
            - 외부 A2A 서버 호출
            - tool calling 없음 (Swarm 비호환)

AssistantAgent (AutoGen 원본)
    - tool calling 지원
    - Swarm/Handoff 호환
```

---

## 5. 체크리스트

### Upstream 업데이트 시

- [ ] `git fetch upstream` 실행
- [ ] 충돌 위험 파일 확인 (agentflow.tsx, chat.tsx)
- [ ] 테스트 실행 (`npm test`, `pytest`)
- [ ] Frontend 재빌드 (`npx gatsby build --prefix-paths`)
- [ ] A2A 에이전트 연동 테스트

### 새 패턴 추가 시

- [ ] `AG_Cohub/patterns/XX_name.json` 생성
- [ ] `patterns/data/`에 복사
- [ ] Frontend 재빌드
- [ ] pattern-loader.ts 자동 스캔 확인

### 새 A2A 에이전트 추가 시

- [ ] `a2a_demo/{name}/agent.py` 생성
- [ ] 포트 번호 할당 (다음 가용: 8010)
- [ ] 서버 실행 테스트
- [ ] Registry 자동 스캔 확인

---

## 6. 참고 링크

- [Microsoft AutoGen GitHub](https://github.com/microsoft/autogen)
- [AutoGen Studio 문서](https://microsoft.github.io/autogen/)
- [A2A Protocol 스펙](https://github.com/google/A2A)

---

*마지막 업데이트: 2026-01-10*
