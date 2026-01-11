# AG-CLI File Operations Tools
"""
파일 작업 도구

사용법:
    from tools.file_ops import list_files, read_file

    files = list_files()
    content = read_file("src/main.py")
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import config


def list_files() -> dict:
    """작업 폴더의 파일 목록을 조회합니다.

    Returns:
        파일 목록을 담은 딕셔너리
    """
    work_dir = Path(config.WORK_FOLDER)
    if not work_dir.exists():
        return {"files": [], "error": f"{config.WORK_FOLDER}/ 폴더가 없습니다", "count": 0}

    files = []
    for f in work_dir.rglob("*"):
        if f.is_file():
            # node_modules 등 제외
            if "node_modules" in str(f) or ".git" in str(f):
                continue
            files.append(str(f.relative_to(work_dir)))

    return {
        "files": files[:100],  # 최대 100개
        "count": len(files),
        "folder": config.WORK_FOLDER
    }


def read_file(file_path: str) -> dict:
    """작업 폴더 내의 파일 내용을 읽습니다.

    Args:
        file_path: 읽을 파일 경로 (작업 폴더 기준 상대 경로)

    Returns:
        파일 내용을 담은 딕셔너리
    """
    work_dir = Path(config.WORK_FOLDER)
    target = work_dir / file_path

    # 보안: 작업 폴더 외부 접근 방지
    try:
        target.resolve().relative_to(work_dir.resolve())
    except ValueError:
        return {"error": "작업 폴더 외부 접근 불가", "file": file_path}

    if not target.exists():
        return {"error": f"파일을 찾을 수 없습니다: {file_path}", "file": file_path}

    try:
        content = target.read_text(encoding="utf-8")
        return {
            "file": file_path,
            "content": content[:10000],  # 최대 10000자
            "size": len(content)
        }
    except Exception as e:
        return {"error": str(e), "file": file_path}
