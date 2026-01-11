# AG-CLI Logging Module
"""
실시간 로그 스트리밍 시스템

사용법:
    from utils.logging import log_line, get_logs

    log_line("task123", "작업 시작", "START")
    logs = get_logs("task123")
"""
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import config


# 로그 저장소 (task_id -> log_lines)
LOG_STORE: Dict[str, list] = {}
CURRENT_TASK_ID: Optional[str] = None


def log_line(task_id: str, line: str, level: str = "INFO"):
    """로그 라인 추가 (메모리 + 파일)

    Args:
        task_id: 작업 ID
        line: 로그 메시지
        level: 로그 레벨 (INFO, START, END, ERROR, TOOL, CODE, RESULT, OUT, CMD, ERR)
    """
    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    log_entry = f"[{timestamp}] [{level}] {line}"

    # 메모리에 저장
    if task_id not in LOG_STORE:
        LOG_STORE[task_id] = []
    LOG_STORE[task_id].append(log_entry)

    # 파일에도 저장
    log_file = config.LOG_DIR / f"{task_id}.log"
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(log_entry + "\n")

    # 콘솔 출력
    print(log_entry)


def get_logs(task_id: str, from_line: int = 0) -> list:
    """로그 조회

    Args:
        task_id: 작업 ID
        from_line: 시작 라인 번호 (기본값: 0)

    Returns:
        로그 라인 리스트
    """
    if task_id not in LOG_STORE:
        return []
    return LOG_STORE[task_id][from_line:]


def get_latest_task_id() -> Optional[str]:
    """가장 최근 task_id 반환"""
    return CURRENT_TASK_ID


def set_current_task_id(task_id: str):
    """현재 task_id 설정"""
    global CURRENT_TASK_ID
    CURRENT_TASK_ID = task_id


def generate_execution_summary(task_id: str, tool_uses: list) -> str:
    """도구 실행 요약 생성 (AutoGen Studio 채팅에 표시)

    Args:
        task_id: 작업 ID
        tool_uses: 도구 사용 목록

    Returns:
        실행 요약 문자열
    """
    if not tool_uses:
        return ""

    lines = ["", "--- Execution Log ---"]

    for tool in tool_uses:
        tool_name = tool.get("tool", "Unknown")
        tool_input = tool.get("input", {})

        if tool_name == "Write":
            file_path = tool_input.get("file_path", "unknown")
            content = tool_input.get("content", "")
            lines.append(f"  [WRITE] {file_path}")
            # 내용 미리보기 (최대 3줄)
            if content:
                preview_lines = content.split("\n")[:3]
                for pl in preview_lines:
                    lines.append(f"    | {pl[:60]}")
                if len(content.split("\n")) > 3:
                    lines.append(f"    | ... ({len(content)} chars total)")
        elif tool_name == "Edit":
            file_path = tool_input.get("file_path", "unknown")
            lines.append(f"  [EDIT] {file_path}")
        elif tool_name == "Read":
            file_path = tool_input.get("file_path", "unknown")
            lines.append(f"  [READ] {file_path}")
        elif tool_name == "Bash":
            cmd = tool_input.get("command", "")[:50]
            lines.append(f"  [BASH] {cmd}")
        elif tool_name == "Glob":
            pattern = tool_input.get("pattern", "")
            lines.append(f"  [GLOB] {pattern}")
        elif tool_name == "Grep":
            pattern = tool_input.get("pattern", "")
            lines.append(f"  [GREP] {pattern}")

    # 로그 파일 경로 추가
    lines.append(f"  [LOG] logs/{task_id}.log")
    lines.append("---")

    return "\n".join(lines)


def log_tool_use(task_id: str, tool_name: str, tool_input: dict):
    """도구 사용 로그 기록

    Args:
        task_id: 작업 ID
        tool_name: 도구 이름
        tool_input: 도구 입력 파라미터
    """
    if tool_name == "Write":
        file_path = tool_input.get("file_path", "unknown")
        content = tool_input.get("content", "")
        log_line(task_id, f"[WRITE] Creating: {file_path}", "TOOL")
        # 파일 내용도 로그에 표시 (최대 500자)
        if content:
            content_preview = content[:500]
            if len(content) > 500:
                content_preview += f"\n... ({len(content)} chars total)"
            log_line(task_id, f"[CONTENT]\n{content_preview}", "CODE")
    elif tool_name == "Edit":
        file_path = tool_input.get("file_path", "unknown")
        old_str = tool_input.get("old_string", "")[:100]
        new_str = tool_input.get("new_string", "")[:100]
        log_line(task_id, f"[EDIT] Modifying: {file_path}", "TOOL")
        log_line(task_id, f"[OLD] {old_str}...", "CODE")
        log_line(task_id, f"[NEW] {new_str}...", "CODE")
    elif tool_name == "Read":
        file_path = tool_input.get("file_path", "unknown")
        log_line(task_id, f"[READ] Reading: {file_path}", "TOOL")
    elif tool_name == "Bash":
        cmd = tool_input.get("command", "")[:100]
        log_line(task_id, f"[BASH] {cmd}", "TOOL")
    elif tool_name == "Glob":
        pattern = tool_input.get("pattern", "")
        log_line(task_id, f"[GLOB] Pattern: {pattern}", "TOOL")
    elif tool_name == "Grep":
        pattern = tool_input.get("pattern", "")
        log_line(task_id, f"[GREP] Search: {pattern}", "TOOL")
    else:
        log_line(task_id, f"[TOOL] {tool_name}", "TOOL")
