"""
AG_action Schemas
==================

JSON Schema 정의 및 검증.

Usage:
    from AG_action.schemas import validate_action

    # YAML 파일 검증
    is_valid, errors = validate_action(yaml_data)
"""

import json
from pathlib import Path
from typing import Dict, Any, Tuple, List, Optional

# jsonschema가 없으면 검증 건너뜀
try:
    import jsonschema
    HAS_JSONSCHEMA = True
except ImportError:
    HAS_JSONSCHEMA = False


def get_schema_path(name: str = "action") -> Path:
    """스키마 파일 경로"""
    return Path(__file__).parent / f"{name}.schema.json"


def load_schema(name: str = "action") -> Optional[Dict[str, Any]]:
    """스키마 로드"""
    path = get_schema_path(name)
    if not path.exists():
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def validate_action(data: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Action 데이터 검증

    Args:
        data: YAML에서 파싱된 Action 데이터

    Returns:
        (is_valid, errors) - 유효 여부와 에러 목록
    """
    if not HAS_JSONSCHEMA:
        # jsonschema 없으면 항상 통과
        return (True, [])

    schema = load_schema("action")
    if not schema:
        return (True, ["Schema not found"])

    try:
        jsonschema.validate(data, schema)
        return (True, [])
    except jsonschema.ValidationError as e:
        return (False, [str(e.message)])
    except jsonschema.SchemaError as e:
        return (False, [f"Schema error: {e.message}"])


__all__ = ["validate_action", "load_schema", "get_schema_path"]
