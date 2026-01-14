"""
FSM Transitions
================

상태 전이 로직 정의.

Transitions:
- user_request: IDLE → SCREENSHOT
- screenshot_taken: SCREENSHOT → ANALYZE
- action_decided: ANALYZE → ACTION
- action_done: ACTION → VERIFY
- need_more: VERIFY → ANALYZE (loop)
- task_complete: VERIFY → COMPLETE
- error: * → ERROR
- recover: ERROR → IDLE
"""

from dataclasses import dataclass
from typing import Callable, Optional, Dict, Any, List
from enum import Enum, auto

from .states import State, FSMState, is_valid_transition


class Event(Enum):
    """FSM 이벤트"""
    USER_REQUEST = auto()      # 사용자 요청
    SCREENSHOT_TAKEN = auto()  # 스크린샷 완료
    ACTION_DECIDED = auto()    # 액션 결정됨
    ACTION_DONE = auto()       # 액션 완료
    NEED_MORE = auto()         # 추가 작업 필요
    TASK_COMPLETE = auto()     # 작업 완료
    ERROR = auto()             # 에러 발생
    RECOVER = auto()           # 복구


@dataclass
class Transition:
    """상태 전이 정의"""
    event: Event
    from_state: State
    to_state: State
    guard: Optional[Callable[[FSMState], bool]] = None  # 조건
    action: Optional[Callable[[FSMState, Dict], None]] = None  # 실행

    def can_execute(self, state: FSMState) -> bool:
        """전이 가능 여부"""
        if state.current != self.from_state:
            return False
        if not is_valid_transition(self.from_state, self.to_state):
            return False
        if self.guard and not self.guard(state):
            return False
        return True

    def execute(self, state: FSMState, data: Dict[str, Any] = None) -> bool:
        """전이 실행"""
        if not self.can_execute(state):
            return False

        if self.action:
            self.action(state, data or {})

        return state.transition_to(self.to_state, data)


class TransitionTable:
    """전이 테이블"""

    def __init__(self):
        self._transitions: Dict[Event, List[Transition]] = {}
        self._setup_defaults()

    def _setup_defaults(self):
        """기본 전이 설정"""
        defaults = [
            # IDLE → SCREENSHOT
            Transition(
                Event.USER_REQUEST,
                State.IDLE,
                State.SCREENSHOT,
            ),
            # SCREENSHOT → ANALYZE
            Transition(
                Event.SCREENSHOT_TAKEN,
                State.SCREENSHOT,
                State.ANALYZE,
            ),
            # ANALYZE → ACTION
            Transition(
                Event.ACTION_DECIDED,
                State.ANALYZE,
                State.ACTION,
            ),
            # ACTION → VERIFY
            Transition(
                Event.ACTION_DONE,
                State.ACTION,
                State.VERIFY,
            ),
            # VERIFY → ANALYZE (loop)
            Transition(
                Event.NEED_MORE,
                State.VERIFY,
                State.ANALYZE,
            ),
            # VERIFY → COMPLETE
            Transition(
                Event.TASK_COMPLETE,
                State.VERIFY,
                State.COMPLETE,
            ),
            # ANALYZE → COMPLETE (작업 불필요)
            Transition(
                Event.TASK_COMPLETE,
                State.ANALYZE,
                State.COMPLETE,
            ),
            # ERROR 복구
            Transition(
                Event.RECOVER,
                State.ERROR,
                State.IDLE,
            ),
            # COMPLETE → IDLE
            Transition(
                Event.RECOVER,
                State.COMPLETE,
                State.IDLE,
            ),
        ]

        # 모든 상태에서 ERROR 전이 가능
        for from_state in State:
            if from_state not in {State.ERROR, State.COMPLETE}:
                defaults.append(Transition(
                    Event.ERROR,
                    from_state,
                    State.ERROR,
                ))

        for t in defaults:
            self.add(t)

    def add(self, transition: Transition):
        """전이 추가"""
        if transition.event not in self._transitions:
            self._transitions[transition.event] = []
        self._transitions[transition.event].append(transition)

    def get(self, event: Event, state: FSMState) -> Optional[Transition]:
        """해당 이벤트와 상태에 맞는 전이 찾기"""
        if event not in self._transitions:
            return None

        for t in self._transitions[event]:
            if t.can_execute(state):
                return t

        return None

    def fire(self, event: Event, state: FSMState, data: Dict[str, Any] = None) -> bool:
        """이벤트 발생"""
        transition = self.get(event, state)
        if not transition:
            return False
        return transition.execute(state, data)
