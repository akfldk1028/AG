# Patches 디렉토리

> 이 폴더는 AutoGen 원본 대비 수정사항을 패치 파일로 보관합니다.

## 패치 파일 목록

| 파일명 | 설명 | 적용 대상 |
|--------|------|-----------|
| `a2a_module.diff` | A2A 모듈 전체 | autogenstudio/a2a/ |
| `agentflow.diff` | 패턴 시각화 시스템 | agentflow/agentflow.tsx |
| `teammanager.diff` | 팀 매니저 A2A 지원 | teammanager.py |
| `frontend_patterns.diff` | 프론트엔드 패턴 시스템 | patterns/, team-runtime/ |

## 패치 생성 방법

```bash
cd D:\Data\22_AG\autogen_a2a_kit

# 전체 변경사항 패치
git diff HEAD~20 -- autogen_source/ > patches/all_changes.diff

# 특정 파일 패치
git diff HEAD~20 -- "autogen_source/**/agentflow.tsx" > patches/agentflow.diff
git diff HEAD~20 -- "autogen_source/**/teammanager.py" > patches/teammanager.diff

# A2A 모듈 (신규 파일)
git diff HEAD~20 -- "autogen_source/**/a2a/**" > patches/a2a_module.diff

# Frontend 패턴 시스템
git diff HEAD~20 -- "autogen_source/**/patterns/**" > patches/frontend_patterns.diff
```

## 패치 적용 방법

```bash
# 패치 적용 (dry-run 먼저)
git apply --check patches/agentflow.diff

# 실제 적용
git apply patches/agentflow.diff

# 충돌 시 3-way 머지 시도
git apply --3way patches/agentflow.diff
```

## 주의사항

1. **패치 생성 시점 기록**: 패치 파일에 생성 날짜와 기준 커밋 해시 주석 추가
2. **충돌 해결**: upstream 업데이트 후 패치가 실패할 수 있음
3. **신규 파일**: `a2a/` 폴더 등 신규 파일은 패치보다 직접 복사가 효율적

## 자동 패치 생성 스크립트

```powershell
# generate_patches.ps1
cd D:\Data\22_AG\autogen_a2a_kit

$date = Get-Date -Format "yyyy-MM-dd"
$commit = git rev-parse --short HEAD

# 헤더 추가하며 패치 생성
$header = "# Generated: $date, Commit: $commit`n"

# 핵심 패치들 생성
$files = @(
    @{name="agentflow"; path="**/agentflow.tsx"},
    @{name="teammanager"; path="**/teammanager.py"},
    @{name="chat"; path="**/chat.tsx"}
)

foreach ($f in $files) {
    $content = git diff HEAD~20 -- $f.path
    if ($content) {
        $header + $content | Out-File -FilePath "patches/$($f.name).diff" -Encoding utf8
    }
}
```

---

*패치 관리 가이드 - docs/UPSTREAM_SYNC.md 참조*
