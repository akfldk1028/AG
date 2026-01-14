"""
AG_action Registry
===================

Action YAML 파일을 스캔하고 관리하는 레지스트리.

Production 원칙:
- Single Responsibility: 레지스트리는 등록/조회만 담당
- Progressive Disclosure: Layer별 로딩으로 토큰 효율화
"""

import yaml
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Tuple
from enum import Enum

# Schema 검증 (선택)
try:
    from ..schemas import validate_action
    HAS_SCHEMA = True
except ImportError:
    HAS_SCHEMA = False
    def validate_action(data): return (True, [])


class ExecutionType(Enum):
    DIRECT = "direct"
    CLAUDE_CLI = "claude_cli"
    HYBRID = "hybrid"


@dataclass
class ActionParam:
    """Action 파라미터 정의"""
    name: str
    type: str
    required: bool = False
    default: Any = None
    description: str = ""
    options: List[str] = field(default_factory=list)


@dataclass
class ActionExecution:
    """Action 실행 정보 (Layer 2)"""
    type: ExecutionType
    working_dir: str = "."
    commands: List[str] = field(default_factory=list)
    command: Optional[str] = None
    timeout: int = 300
    retry: int = 0
    env: Dict[str, str] = field(default_factory=dict)


@dataclass
class Action:
    """
    Action 정의

    3-Layer Progressive Disclosure:
    - Layer 1: 메타데이터 (name, category, description, triggers)
    - Layer 2: 실행 정보 (execution, params)
    - Layer 3: 상세 설정 (advanced)
    """
    # Layer 1: 메타데이터 (항상 로드)
    name: str
    category: str
    description: str
    triggers: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)

    # Layer 2: 실행 정보 (활성화 시 로드)
    execution: Optional[ActionExecution] = None
    params: List[ActionParam] = field(default_factory=list)

    # Layer 3: 상세 설정 (필요시 로드)
    advanced: Dict[str, Any] = field(default_factory=dict)
    outputs: List[Dict[str, Any]] = field(default_factory=list)

    # 메타
    file_path: Optional[str] = None
    _loaded_layer: int = 1  # 현재 로드된 레이어

    def to_dict(self, layer: int = 1) -> Dict[str, Any]:
        """지정된 레이어까지의 정보를 딕셔너리로 반환"""
        result = {
            "name": self.name,
            "category": self.category,
            "description": self.description,
            "triggers": self.triggers,
            "tags": self.tags,
        }

        if layer >= 2 and self.execution:
            result["execution"] = {
                "type": self.execution.type.value,
                "working_dir": self.execution.working_dir,
                "commands": self.execution.commands or [self.execution.command],
                "timeout": self.execution.timeout,
            }
            result["params"] = [
                {"name": p.name, "type": p.type, "default": p.default}
                for p in self.params
            ]

        if layer >= 3:
            result["advanced"] = self.advanced
            result["outputs"] = self.outputs

        return result


class ActionRegistry:
    """
    Action Registry

    YAML 파일을 스캔하고 Action을 등록/조회합니다.
    """

    _instance: Optional["ActionRegistry"] = None

    def __init__(self, actions_dir: Optional[str] = None):
        self.actions_dir = Path(actions_dir or self._default_actions_dir())
        self._actions: Dict[str, Action] = {}
        self._by_category: Dict[str, List[str]] = {}
        self._triggers_index: Dict[str, str] = {}  # trigger -> action_name

    @classmethod
    def get_instance(cls, actions_dir: Optional[str] = None) -> "ActionRegistry":
        """싱글톤 인스턴스 반환"""
        if cls._instance is None:
            cls._instance = cls(actions_dir)
            cls._instance.scan()
        return cls._instance

    @staticmethod
    def _default_actions_dir() -> str:
        """기본 actions 디렉토리 경로"""
        return str(Path(__file__).parent.parent / "actions")

    def scan(self) -> int:
        """
        actions 디렉토리를 스캔하여 모든 Action 등록

        Returns:
            등록된 Action 수
        """
        self._actions.clear()
        self._by_category.clear()
        self._triggers_index.clear()

        if not self.actions_dir.exists():
            return 0

        count = 0
        for yaml_file in self.actions_dir.rglob("*.yaml"):
            try:
                action = self._load_action(yaml_file)
                if action:
                    self._register(action)
                    count += 1
            except Exception as e:
                print(f"[ActionRegistry] Error loading {yaml_file}: {e}")

        return count

    def _load_action(
        self,
        file_path: Path,
        layer: int = 1,
        validate: bool = True,
    ) -> Optional[Action]:
        """
        YAML 파일에서 Action 로드

        Args:
            file_path: YAML 파일 경로
            layer: 로드할 레이어 (1, 2, 3)
            validate: JSON Schema 검증 여부
        """
        with open(file_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        if not data or "name" not in data:
            return None

        # Schema 검증
        if validate and HAS_SCHEMA:
            is_valid, errors = validate_action(data)
            if not is_valid:
                print(f"[ActionRegistry] Schema validation failed for {file_path}: {errors}")
                # 경고만 하고 계속 진행 (strict=False 동작)

        # Layer 1: 메타데이터
        action = Action(
            name=data["name"],
            category=data.get("category", "unknown"),
            description=data.get("description", ""),
            triggers=data.get("triggers", []),
            tags=data.get("tags", []),
            file_path=str(file_path),
        )

        # Layer 2: 실행 정보
        if layer >= 2 and "execution" in data:
            exec_data = data["execution"]
            action.execution = ActionExecution(
                type=ExecutionType(exec_data.get("type", "direct")),
                working_dir=exec_data.get("working_dir", "."),
                commands=exec_data.get("commands", []),
                command=exec_data.get("command"),
                timeout=exec_data.get("timeout", 300),
                retry=exec_data.get("retry", 0),
                env=exec_data.get("env", {}),
            )

            if "params" in data:
                action.params = [
                    ActionParam(
                        name=p["name"],
                        type=p.get("type", "string"),
                        required=p.get("required", False),
                        default=p.get("default"),
                        description=p.get("description", ""),
                        options=p.get("options", []),
                    )
                    for p in data["params"]
                ]

        # Layer 3: 상세 설정
        if layer >= 3:
            action.advanced = data.get("advanced", {})
            action.outputs = data.get("outputs", [])

        action._loaded_layer = layer
        return action

    def _register(self, action: Action):
        """Action 등록"""
        self._actions[action.name] = action

        # 카테고리별 인덱스
        if action.category not in self._by_category:
            self._by_category[action.category] = []
        self._by_category[action.category].append(action.name)

        # 트리거 인덱스
        for trigger in action.triggers:
            self._triggers_index[trigger.lower()] = action.name

    def get(self, name: str, layer: int = 2) -> Optional[Action]:
        """
        Action 조회

        Args:
            name: Action 이름
            layer: 필요한 레이어 (기본 2)
        """
        action = self._actions.get(name)
        if not action:
            return None

        # 필요한 레이어가 로드되지 않았으면 다시 로드
        if action._loaded_layer < layer and action.file_path:
            action = self._load_action(Path(action.file_path), layer)
            if action:
                self._actions[name] = action

        return action

    def find_by_trigger(self, text: str) -> Optional[Action]:
        """
        트리거 텍스트로 Action 찾기

        Args:
            text: 사용자 입력 텍스트
        """
        text_lower = text.lower()

        # 정확한 매칭
        if text_lower in self._triggers_index:
            return self.get(self._triggers_index[text_lower])

        # 부분 매칭
        for trigger, name in self._triggers_index.items():
            if trigger in text_lower or text_lower in trigger:
                return self.get(name)

        return None

    def list(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Action 목록 반환 (Layer 1 정보만)

        Args:
            category: 카테고리 필터
        """
        if category:
            names = self._by_category.get(category, [])
        else:
            names = list(self._actions.keys())

        return [
            self._actions[name].to_dict(layer=1)
            for name in names
            if name in self._actions
        ]

    def categories(self) -> List[str]:
        """사용 가능한 카테고리 목록"""
        return list(self._by_category.keys())

    def stats(self) -> Dict[str, Any]:
        """레지스트리 통계"""
        return {
            "total_actions": len(self._actions),
            "categories": {cat: len(names) for cat, names in self._by_category.items()},
            "total_triggers": len(self._triggers_index),
        }


# 편의 함수
def get_registry() -> ActionRegistry:
    """글로벌 레지스트리 인스턴스 반환"""
    return ActionRegistry.get_instance()
