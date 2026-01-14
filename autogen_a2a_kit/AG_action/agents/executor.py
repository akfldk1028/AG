"""
AG_action Executor
===================

Action 실행 엔진.

Production 원칙 (arXiv 2512.08769):
- #2: Direct Function Calls - 비추론 작업은 LLM 없이 직접 실행
- #9: KISS - 단순함 유지
"""

import os
import asyncio
import subprocess
import shutil
from pathlib import Path
from dataclasses import dataclass
from typing import Optional, Dict, Any, List
from enum import Enum

from ..registry import ActionRegistry, Action, ExecutionType


class ResultStatus(Enum):
    SUCCESS = "success"
    FAILURE = "failure"
    SKIPPED = "skipped"
    TIMEOUT = "timeout"


@dataclass
class ExecutionResult:
    """Action 실행 결과"""
    status: ResultStatus
    action_name: str
    stdout: str = ""
    stderr: str = ""
    return_code: int = 0
    duration: float = 0.0
    outputs: Dict[str, Any] = None

    def __post_init__(self):
        if self.outputs is None:
            self.outputs = {}

    @property
    def success(self) -> bool:
        return self.status == ResultStatus.SUCCESS

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status.value,
            "action_name": self.action_name,
            "success": self.success,
            "stdout": self.stdout[:2000] if self.stdout else "",  # 출력 제한
            "stderr": self.stderr[:500] if self.stderr else "",
            "return_code": self.return_code,
            "duration": round(self.duration, 2),
            "outputs": self.outputs,
        }


class ActionExecutor:
    """
    Action Executor

    Production 원칙을 따르는 Action 실행 엔진:
    - Direct: subprocess로 직접 실행 (LLM 없음)
    - Hybrid: Claude CLI로 일부 처리 후 직접 실행
    """

    def __init__(
        self,
        project_root: Optional[str] = None,
        registry: Optional[ActionRegistry] = None,
    ):
        self.project_root = Path(project_root or os.getcwd())
        self.registry = registry or ActionRegistry.get_instance()

    async def execute(
        self,
        action_name: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> ExecutionResult:
        """
        Action 실행

        Args:
            action_name: 실행할 Action 이름
            params: 파라미터 (옵션)

        Returns:
            ExecutionResult
        """
        import time
        start_time = time.time()

        # Action 조회 (Layer 2 로드)
        action = self.registry.get(action_name, layer=2)
        if not action:
            return ExecutionResult(
                status=ResultStatus.FAILURE,
                action_name=action_name,
                stderr=f"Action not found: {action_name}",
            )

        if not action.execution:
            return ExecutionResult(
                status=ResultStatus.FAILURE,
                action_name=action_name,
                stderr="Action has no execution config",
            )

        # 파라미터 병합 (기본값 + 입력값)
        merged_params = self._merge_params(action, params or {})

        try:
            # 실행 타입에 따라 분기
            if action.execution.type == ExecutionType.DIRECT:
                result = await self._execute_direct(action, merged_params)
            elif action.execution.type == ExecutionType.HYBRID:
                result = await self._execute_hybrid(action, merged_params)
            elif action.execution.type == ExecutionType.CLAUDE_CLI:
                result = await self._execute_claude_cli(action, merged_params)
            else:
                result = ExecutionResult(
                    status=ResultStatus.FAILURE,
                    action_name=action_name,
                    stderr=f"Unknown execution type: {action.execution.type}",
                )

            result.duration = time.time() - start_time
            return result

        except asyncio.TimeoutError:
            return ExecutionResult(
                status=ResultStatus.TIMEOUT,
                action_name=action_name,
                stderr=f"Timeout after {action.execution.timeout}s",
                duration=time.time() - start_time,
            )
        except Exception as e:
            return ExecutionResult(
                status=ResultStatus.FAILURE,
                action_name=action_name,
                stderr=str(e),
                duration=time.time() - start_time,
            )

    def _merge_params(self, action: Action, input_params: Dict[str, Any]) -> Dict[str, Any]:
        """기본값과 입력 파라미터 병합"""
        merged = {}
        for param in action.params:
            if param.name in input_params:
                merged[param.name] = input_params[param.name]
            elif param.default is not None:
                merged[param.name] = param.default
            elif param.required:
                raise ValueError(f"Required param missing: {param.name}")
        return merged

    def _substitute_vars(self, text: str, params: Dict[str, Any]) -> str:
        """변수 치환 (${var})"""
        result = text
        for key, value in params.items():
            result = result.replace(f"${{{key}}}", str(value))

        # 환경변수 치환
        for match in set(
            m for m in result.split("${") if "}" in m
        ):
            var_name = match.split("}")[0]
            env_value = os.environ.get(var_name, "")
            result = result.replace(f"${{{var_name}}}", env_value)

        return result

    def _detect_package_manager(self, working_dir: Path) -> str:
        """패키지 매니저 자동 감지"""
        if (working_dir / "pnpm-lock.yaml").exists():
            return "pnpm"
        elif (working_dir / "yarn.lock").exists():
            return "yarn"
        elif (working_dir / "bun.lockb").exists():
            return "bun"
        return "npm"

    async def _execute_direct(
        self,
        action: Action,
        params: Dict[str, Any],
    ) -> ExecutionResult:
        """
        Direct 실행 (LLM 없이)

        Production 원칙 #2: 비추론 작업은 직접 실행
        """
        working_dir = self.project_root / action.execution.working_dir

        # 패키지 매니저 감지 (${PM} 치환용)
        if "${PM}" in str(action.execution.commands):
            params["PM"] = self._detect_package_manager(working_dir)

        # 명령어 목록
        commands = action.execution.commands or [action.execution.command]
        commands = [c for c in commands if c]  # None 제거

        all_stdout = []
        all_stderr = []

        for cmd in commands:
            # 변수 치환
            cmd = self._substitute_vars(cmd, params)

            # 실행
            try:
                proc = await asyncio.wait_for(
                    asyncio.create_subprocess_shell(
                        cmd,
                        cwd=str(working_dir),
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE,
                        env={**os.environ, **action.execution.env},
                    ),
                    timeout=action.execution.timeout,
                )

                stdout, stderr = await proc.communicate()
                all_stdout.append(stdout.decode("utf-8", errors="replace"))
                all_stderr.append(stderr.decode("utf-8", errors="replace"))

                if proc.returncode != 0:
                    return ExecutionResult(
                        status=ResultStatus.FAILURE,
                        action_name=action.name,
                        stdout="\n".join(all_stdout),
                        stderr="\n".join(all_stderr),
                        return_code=proc.returncode,
                    )

            except asyncio.TimeoutError:
                raise

        return ExecutionResult(
            status=ResultStatus.SUCCESS,
            action_name=action.name,
            stdout="\n".join(all_stdout),
            stderr="\n".join(all_stderr),
            return_code=0,
        )

    async def _execute_hybrid(
        self,
        action: Action,
        params: Dict[str, Any],
    ) -> ExecutionResult:
        """
        Hybrid 실행: Claude CLI로 처리 후 직접 실행

        예: 커밋 메시지 자동 생성 → git commit
        """
        # TODO: Claude CLI 연동
        # 현재는 direct로 fallback
        return await self._execute_direct(action, params)

    async def _execute_claude_cli(
        self,
        action: Action,
        params: Dict[str, Any],
    ) -> ExecutionResult:
        """
        Claude CLI 실행

        코드 생성, 분석 등 추론이 필요한 작업용
        """
        # TODO: Claude CLI 연동
        return ExecutionResult(
            status=ResultStatus.SKIPPED,
            action_name=action.name,
            stderr="Claude CLI execution not implemented yet",
        )

    # 편의 메서드
    async def build_frontend(self, **params) -> ExecutionResult:
        """프론트엔드 빌드"""
        return await self.execute("frontend_build", params)

    async def build_backend(self, **params) -> ExecutionResult:
        """백엔드 빌드"""
        return await self.execute("backend_build", params)

    async def run_tests(self, **params) -> ExecutionResult:
        """테스트 실행"""
        return await self.execute("unit_test", params)

    async def lint(self, **params) -> ExecutionResult:
        """린트 실행"""
        return await self.execute("eslint", params)

    async def commit(self, message: str = None, **params) -> ExecutionResult:
        """Git 커밋"""
        if message:
            params["message"] = message
        return await self.execute("git_commit", params)


# CLI 테스트용
async def main():
    """테스트 실행"""
    executor = ActionExecutor()

    # 레지스트리 통계
    print("=== Registry Stats ===")
    print(executor.registry.stats())

    # Action 목록
    print("\n=== Actions ===")
    for action in executor.registry.list():
        print(f"  - {action['name']}: {action['description']}")


if __name__ == "__main__":
    asyncio.run(main())
