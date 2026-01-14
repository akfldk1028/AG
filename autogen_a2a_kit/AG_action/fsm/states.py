"""
FSM States for Computer Use Actions
=====================================

Claude Computer Use의 Action을 FSM으로 관리.

States:
- IDLE: 대기 상태
- SCREENSHOT: 화면 캡처
- ANALYZE: 화면 분석 (LLM)
- ACTION: Action 실행
- VERIFY: 결과 검증
- ERROR: 에러 상태
"""

from enum import Enum, auto
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from datetime import datetime


class State(Enum):
    """FSM 상태 정의"""
    IDLE = auto()        # 대기
    SCREENSHOT = auto()  # 화면 캡처
    ANALYZE = auto()     # 분석 (LLM)
    ACTION = auto()      # 실행
    VERIFY = auto()      # 검증
    ERROR = auto()       # 에러
    COMPLETE = auto()    # 완료


@dataclass
class FSMState:
    """FSM 상태 객체"""

    current: State = State.IDLE
    previous: Optional[State] = None
    data: Dict[str, Any] = field(default_factory=dict)
    history: List[Dict[str, Any]] = field(default_factory=list)
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self):
        self.started_at = datetime.now()
        self.updated_at = self.started_at

    def transition_to(self, new_state: State, data: Dict[str, Any] = None) -> bool:
        """상태 전이"""
        self.history.append({
            "from": self.current.name,
            "to": new_state.name,
            "data": data or {},
            "timestamp": datetime.now().isoformat(),
        })

        self.previous = self.current
        self.current = new_state
        self.updated_at = datetime.now()

        if data:
            self.data.update(data)

        return True

    def set_error(self, error: str):
        """에러 설정"""
        self.error = error
        self.transition_to(State.ERROR, {"error": error})

    def reset(self):
        """초기화"""
        self.current = State.IDLE
        self.previous = None
        self.data = {}
        self.error = None
        self.updated_at = datetime.now()
        # history는 유지

    @property
    def is_idle(self) -> bool:
        return self.current == State.IDLE

    @property
    def is_complete(self) -> bool:
        return self.current == State.COMPLETE

    @property
    def is_error(self) -> bool:
        return self.current == State.ERROR

    @property
    def is_running(self) -> bool:
        return self.current in {
            State.SCREENSHOT,
            State.ANALYZE,
            State.ACTION,
            State.VERIFY,
        }

    def to_dict(self) -> Dict[str, Any]:
        """직렬화"""
        return {
            "current": self.current.name,
            "previous": self.previous.name if self.previous else None,
            "data": self.data,
            "error": self.error,
            "history_count": len(self.history),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


# State별 허용 전이
VALID_TRANSITIONS = {
    State.IDLE: {State.SCREENSHOT, State.ERROR},
    State.SCREENSHOT: {State.ANALYZE, State.ERROR},
    State.ANALYZE: {State.ACTION, State.ERROR, State.COMPLETE},
    State.ACTION: {State.VERIFY, State.ERROR},
    State.VERIFY: {State.ANALYZE, State.COMPLETE, State.ERROR},  # loop back 가능
    State.ERROR: {State.IDLE},  # 복구
    State.COMPLETE: {State.IDLE},  # 재시작
}


def is_valid_transition(from_state: State, to_state: State) -> bool:
    """전이 유효성 검사"""
    if from_state not in VALID_TRANSITIONS:
        return False
    return to_state in VALID_TRANSITIONS[from_state]
