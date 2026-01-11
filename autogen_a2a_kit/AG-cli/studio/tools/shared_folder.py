# AG-CLI Shared Folder Tools
"""
공유 폴더 도구 - 에이전트 간 파일 공유

사용법:
    from tools.shared_folder import list_shared_files, read_shared_file, write_to_shared

    files = list_shared_files()
    content = read_shared_file("api_spec.json")
    result = write_to_shared("schema.sql", "CREATE TABLE ...")
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import config


def list_shared_files() -> dict:
    """공유 폴더의 파일 목록을 조회합니다.

    다른 에이전트가 공유한 파일들을 확인할 수 있습니다.

    Returns:
        공유 폴더 파일 목록
    """
    shared_dir = Path(config.SHARED_FOLDER)
    if not shared_dir.exists():
        shared_dir.mkdir(parents=True, exist_ok=True)
        return {"files": [], "count": 0, "folder": config.SHARED_FOLDER}

    files = []
    for f in shared_dir.rglob("*"):
        if f.is_file():
            files.append(str(f.relative_to(shared_dir)))

    return {
        "files": files[:100],
        "count": len(files),
        "folder": config.SHARED_FOLDER
    }


def read_shared_file(file_path: str) -> dict:
    """공유 폴더의 파일 내용을 읽습니다.

    다른 에이전트가 공유한 파일을 읽을 수 있습니다.

    Args:
        file_path: 읽을 파일 경로 (shared/ 폴더 기준 상대 경로)

    Returns:
        파일 내용
    """
    shared_dir = Path(config.SHARED_FOLDER)
    target = shared_dir / file_path

    # 보안: shared 폴더 외부 접근 방지
    try:
        target.resolve().relative_to(shared_dir.resolve())
    except ValueError:
        return {"error": "공유 폴더 외부 접근 불가", "file": file_path}

    if not target.exists():
        return {"error": f"파일을 찾을 수 없습니다: {file_path}", "file": file_path}

    try:
        content = target.read_text(encoding="utf-8")
        return {
            "file": file_path,
            "content": content[:10000],
            "size": len(content),
            "folder": config.SHARED_FOLDER
        }
    except Exception as e:
        return {"error": str(e), "file": file_path}


def write_to_shared(filename: str, content: str) -> dict:
    """공유 폴더에 파일을 작성합니다.

    다른 에이전트와 공유할 파일을 저장합니다.
    API 스펙, 스키마, 공통 설정 등을 공유할 때 사용하세요.

    Args:
        filename: 저장할 파일명 (예: "api_spec.json", "schema.sql")
        content: 파일 내용

    Returns:
        저장 결과
    """
    shared_dir = Path(config.SHARED_FOLDER)
    shared_dir.mkdir(parents=True, exist_ok=True)

    target = shared_dir / filename

    # 보안: shared 폴더 외부 접근 방지
    try:
        target.resolve().relative_to(shared_dir.resolve())
    except ValueError:
        return {"error": "공유 폴더 외부 접근 불가", "filename": filename}

    try:
        # 중간 디렉토리 생성
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        return {
            "success": True,
            "filename": filename,
            "folder": config.SHARED_FOLDER,
            "path": str(target),
            "size": len(content)
        }
    except Exception as e:
        return {"error": str(e), "filename": filename}
