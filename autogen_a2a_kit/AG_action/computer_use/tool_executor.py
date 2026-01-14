"""
Tool Executor
==============

Computer Use tool_use 블록 실행.

지원 Tools:
- computer: screenshot, click, type, key, etc.
- bash: 명령어 실행
- text_editor: 파일 편집
"""

import os
import subprocess
from typing import Dict, Any, Optional
from dataclasses import dataclass

# primitives 사용 (상대 import)
from ..primitives import ComputerUseExecutor


@dataclass
class ToolResult:
    """Tool 실행 결과"""
    success: bool
    output: str = ""
    error: Optional[str] = None
    base64_data: Optional[str] = None  # 스크린샷용

    def to_dict(self) -> Dict[str, Any]:
        result = {
            "success": self.success,
            "output": self.output,
            "error": self.error,
        }
        if self.base64_data:
            result["base64_data"] = self.base64_data
        return result


class ToolExecutor:
    """
    Tool Executor

    Claude의 tool_use 블록을 실행.

    Supports:
    - computer: Computer Use actions (computer_20250124)
    - bash: Shell commands (bash_20250124)
    - text_editor / str_replace_based_edit_tool: File editing (text_editor_20250728)

    Note:
        Claude 4 모델은 str_replace_based_edit_tool 이름을 사용
        Claude 3.7은 text_editor 이름을 사용 (deprecated)
    """

    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run
        self.computer = ComputerUseExecutor(dry_run)

    def execute(self, tool_name: str, tool_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Tool 실행

        Args:
            tool_name: 도구 이름 (computer, bash, text_editor)
            tool_input: 도구 입력

        Returns:
            실행 결과 (dict)
        """
        if tool_name == "computer":
            return self._execute_computer(tool_input)
        elif tool_name == "bash":
            return self._execute_bash(tool_input)
        elif tool_name in ("text_editor", "str_replace_based_edit_tool"):
            # NOTE: str_replace_based_edit_tool = Claude 4용 text_editor
            return self._execute_text_editor(tool_input)
        else:
            return {
                "success": False,
                "error": f"Unknown tool: {tool_name}",
            }

    def _execute_computer(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Computer Use 실행

        Actions: screenshot, left_click, type, key, mouse_move, scroll, etc.
        """
        action = input_data.get("action")
        if not action:
            return {"success": False, "error": "Missing 'action'"}

        # ComputerUseExecutor 사용
        result = self.computer.execute(action, **input_data)
        return result.to_dict()

    def _execute_bash(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Bash 명령 실행

        Input:
            command: 실행할 명령
            restart: shell 재시작 여부
        """
        command = input_data.get("command", "")
        restart = input_data.get("restart", False)

        if self.dry_run:
            print(f"[DRY_RUN] bash: {command}")
            return {
                "success": True,
                "output": f"[DRY_RUN] Would execute: {command}",
            }

        if not command and not restart:
            return {"success": False, "error": "Missing 'command'"}

        try:
            # 안전하지 않은 명령 차단
            dangerous = ["rm -rf /", ":(){ :|:& };:", "mkfs", "dd if="]
            if any(d in command for d in dangerous):
                return {
                    "success": False,
                    "error": "Dangerous command blocked",
                }

            # 실행
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=60,  # 1분 타임아웃
                cwd=os.getcwd(),
            )

            return {
                "success": result.returncode == 0,
                "output": result.stdout or result.stderr,
                "error": result.stderr if result.returncode != 0 else None,
            }

        except subprocess.TimeoutExpired:
            return {"success": False, "error": "Command timed out (60s)"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _execute_text_editor(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Text Editor 실행 (str_replace_based_edit_tool 호환)

        Commands:
        - view: 파일 내용 보기
        - create: 파일 생성
        - str_replace: 문자열 치환
        - insert: 라인 삽입

        Note:
            undo_edit은 text_editor_20250728 (Claude 4)에서 제거됨
        """
        command = input_data.get("command")
        path = input_data.get("path", "")

        if self.dry_run:
            print(f"[DRY_RUN] text_editor: {command} {path}")
            return {
                "success": True,
                "output": f"[DRY_RUN] Would {command}: {path}",
            }

        if not command:
            return {"success": False, "error": "Missing 'command'"}

        try:
            if command == "view":
                return self._view_file(path, input_data.get("view_range"))

            elif command == "create":
                return self._create_file(path, input_data.get("file_text", ""))

            elif command == "str_replace":
                return self._str_replace(
                    path,
                    input_data.get("old_str", ""),
                    input_data.get("new_str", ""),
                )

            elif command == "insert":
                return self._insert_line(
                    path,
                    input_data.get("insert_line", 0),
                    input_data.get("new_str", ""),
                )

            else:
                return {"success": False, "error": f"Unknown command: {command}"}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def _view_file(self, path: str, view_range: list = None) -> Dict[str, Any]:
        """파일 보기"""
        if not os.path.exists(path):
            return {"success": False, "error": f"File not found: {path}"}

        with open(path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        if view_range:
            start = max(0, view_range[0] - 1)
            end = min(len(lines), view_range[1])
            lines = lines[start:end]

        return {
            "success": True,
            "output": "".join(lines),
        }

    def _create_file(self, path: str, content: str) -> Dict[str, Any]:
        """파일 생성"""
        # 디렉토리 생성
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)

        with open(path, "w", encoding="utf-8") as f:
            f.write(content)

        return {
            "success": True,
            "output": f"Created: {path}",
        }

    def _str_replace(self, path: str, old_str: str, new_str: str) -> Dict[str, Any]:
        """문자열 치환"""
        if not os.path.exists(path):
            return {"success": False, "error": f"File not found: {path}"}

        with open(path, "r", encoding="utf-8") as f:
            content = f.read()

        if old_str not in content:
            return {"success": False, "error": "String not found in file"}

        new_content = content.replace(old_str, new_str, 1)

        with open(path, "w", encoding="utf-8") as f:
            f.write(new_content)

        return {
            "success": True,
            "output": f"Replaced in: {path}",
        }

    def _insert_line(self, path: str, line_num: int, text: str) -> Dict[str, Any]:
        """라인 삽입"""
        if not os.path.exists(path):
            return {"success": False, "error": f"File not found: {path}"}

        with open(path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        if line_num < 0 or line_num > len(lines):
            return {"success": False, "error": f"Invalid line number: {line_num}"}

        lines.insert(line_num, text + "\n")

        with open(path, "w", encoding="utf-8") as f:
            f.writelines(lines)

        return {
            "success": True,
            "output": f"Inserted at line {line_num}: {path}",
        }

    # 편의 메서드
    def screenshot(self) -> Dict[str, Any]:
        """스크린샷"""
        return self._execute_computer({"action": "screenshot"})

    def click(self, x: int, y: int) -> Dict[str, Any]:
        """클릭"""
        return self._execute_computer({
            "action": "left_click",
            "coordinate": [x, y],
        })

    def type_text(self, text: str) -> Dict[str, Any]:
        """텍스트 입력"""
        return self._execute_computer({
            "action": "type",
            "text": text,
        })

    def press_key(self, key: str) -> Dict[str, Any]:
        """키 입력"""
        return self._execute_computer({
            "action": "key",
            "key": key,
        })

    def run_command(self, command: str) -> Dict[str, Any]:
        """명령어 실행"""
        return self._execute_bash({"command": command})
