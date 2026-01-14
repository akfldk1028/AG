"""
Screen Actions
===============

Computer Use API의 화면 관련 Action.

Features:
- Screenshot capture
- Resolution Scaling (XGA/WXGA 지원)
- Coordinate transformation
"""

import io
import base64
import time
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, Tuple
from enum import Enum


class ScalingTarget(Enum):
    """
    스케일링 대상 해상도 (공식 패턴)

    XGA (1024x768): 작은 모니터, 토큰 최소화
    WXGA (1280x800): 와이드스크린, 균형잡힌 선택
    """
    XGA = (1024, 768)      # 4:3 비율
    WXGA = (1280, 800)     # 16:10 비율
    NONE = None            # 스케일링 없음


@dataclass
class ScalingInfo:
    """Resolution Scaling 정보"""
    enabled: bool = False
    original_width: int = 0
    original_height: int = 0
    scaled_width: int = 0
    scaled_height: int = 0
    scale_x: float = 1.0
    scale_y: float = 1.0

    def to_original_coords(self, scaled_x: int, scaled_y: int) -> Tuple[int, int]:
        """
        스케일된 좌표 → 원본 좌표 변환

        Args:
            scaled_x, scaled_y: 스케일된 이미지에서의 좌표 (Claude가 반환)

        Returns:
            원본 화면에서의 좌표 (실제 클릭 위치)
        """
        if not self.enabled:
            return (scaled_x, scaled_y)

        original_x = int(scaled_x * self.scale_x)
        original_y = int(scaled_y * self.scale_y)
        return (original_x, original_y)

    def to_scaled_coords(self, original_x: int, original_y: int) -> Tuple[int, int]:
        """원본 좌표 → 스케일된 좌표 변환 (디버깅용)"""
        if not self.enabled:
            return (original_x, original_y)

        scaled_x = int(original_x / self.scale_x)
        scaled_y = int(original_y / self.scale_y)
        return (scaled_x, scaled_y)


@dataclass
class ScreenAction:
    """스크린 액션 결과"""
    action: str
    success: bool
    data: bytes = None
    base64_data: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "action": self.action,
            "success": self.success,
            "base64_data": self.base64_data[:100] + "..." if self.base64_data else "",
            "metadata": self.metadata,
            "error": self.error,
        }


class ScreenActions:
    """
    Screen Action Primitives

    Claude Computer Use API의 화면 관련 액션들.
    """

    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run
        self._gui = None
        self._pil = None
        self._init_libs()

    def _init_libs(self):
        """라이브러리 초기화"""
        if self.dry_run:
            return

        try:
            import pyautogui
            from PIL import Image
            self._gui = pyautogui
            self._pil = Image
        except ImportError as e:
            print(f"[ScreenActions] Library not installed: {e}. Running in dry_run mode.")
            self.dry_run = True

    def screenshot(self, region: Tuple[int, int, int, int] = None) -> ScreenAction:
        """
        스크린샷 촬영

        Args:
            region: (x, y, width, height) - None이면 전체 화면

        Returns:
            ScreenAction with base64 encoded image
        """
        action_name = "screenshot"

        if self.dry_run:
            print(f"[DRY_RUN] screenshot region={region}")
            return ScreenAction(
                action_name,
                True,
                metadata={"region": region, "dry_run": True}
            )

        try:
            # 스크린샷 촬영
            if region:
                img = self._gui.screenshot(region=region)
            else:
                img = self._gui.screenshot()

            # PNG로 인코딩
            buffer = io.BytesIO()
            img.save(buffer, format="PNG")
            img_bytes = buffer.getvalue()

            # Base64 인코딩 (Claude API용)
            base64_data = base64.standard_b64encode(img_bytes).decode("utf-8")

            return ScreenAction(
                action_name,
                True,
                data=img_bytes,
                base64_data=base64_data,
                metadata={
                    "width": img.width,
                    "height": img.height,
                    "region": region,
                    "format": "PNG",
                    "size_bytes": len(img_bytes),
                }
            )
        except Exception as e:
            return ScreenAction(action_name, False, error=str(e))

    def wait(self, seconds: float) -> ScreenAction:
        """
        대기

        Args:
            seconds: 대기 시간 (초)
        """
        action_name = "wait"

        if self.dry_run:
            print(f"[DRY_RUN] wait {seconds}s")
            return ScreenAction(
                action_name,
                True,
                metadata={"seconds": seconds, "dry_run": True}
            )

        try:
            time.sleep(seconds)
            return ScreenAction(
                action_name,
                True,
                metadata={"seconds": seconds}
            )
        except Exception as e:
            return ScreenAction(action_name, False, error=str(e))

    def zoom(self, region: Tuple[int, int, int, int]) -> ScreenAction:
        """
        영역 확대 (Opus 4.5 전용)

        Args:
            region: (x, y, width, height) - 확대할 영역

        Returns:
            확대된 영역의 스크린샷
        """
        return self.screenshot(region)

    def get_screen_size(self) -> Tuple[int, int]:
        """화면 크기 조회"""
        if self.dry_run:
            return (1920, 1080)  # 기본값

        try:
            return self._gui.size()
        except Exception:
            return (1920, 1080)

    def screenshot_scaled(
        self,
        target: ScalingTarget = ScalingTarget.XGA,
        region: Tuple[int, int, int, int] = None,
    ) -> Tuple[ScreenAction, ScalingInfo]:
        """
        Resolution Scaling이 적용된 스크린샷 (공식 패턴)

        Claude Computer Use에서 토큰 효율을 위해 스크린샷을 작은 해상도로 축소.
        좌표는 ScalingInfo를 통해 원본으로 변환.

        Args:
            target: ScalingTarget (XGA, WXGA, NONE)
            region: (x, y, width, height) - None이면 전체 화면

        Returns:
            (ScreenAction, ScalingInfo)

        Usage:
            screen = ScreenActions()
            action, scaling = screen.screenshot_scaled(ScalingTarget.XGA)
            # Claude가 반환한 좌표 변환
            original_x, original_y = scaling.to_original_coords(claude_x, claude_y)
        """
        action_name = "screenshot_scaled"

        # 스케일링 없음
        if target == ScalingTarget.NONE:
            action = self.screenshot(region)
            scaling_info = ScalingInfo(enabled=False)
            return (action, scaling_info)

        if self.dry_run:
            target_w, target_h = target.value
            screen_w, screen_h = self.get_screen_size()
            print(f"[DRY_RUN] screenshot_scaled {screen_w}x{screen_h} → {target_w}x{target_h}")
            scaling_info = ScalingInfo(
                enabled=True,
                original_width=screen_w,
                original_height=screen_h,
                scaled_width=target_w,
                scaled_height=target_h,
                scale_x=screen_w / target_w,
                scale_y=screen_h / target_h,
            )
            return (
                ScreenAction(
                    action_name,
                    True,
                    metadata={"target": target.name, "dry_run": True}
                ),
                scaling_info
            )

        try:
            # 원본 스크린샷 촬영
            if region:
                img = self._gui.screenshot(region=region)
            else:
                img = self._gui.screenshot()

            original_width = img.width
            original_height = img.height
            target_width, target_height = target.value

            # 비율 유지하면서 스케일링
            # 공식 패턴: 가로/세로 중 큰 비율에 맞춤
            scale_ratio = min(
                target_width / original_width,
                target_height / original_height
            )

            new_width = int(original_width * scale_ratio)
            new_height = int(original_height * scale_ratio)

            # 리사이즈 (LANCZOS = 고품질 다운샘플링)
            scaled_img = img.resize(
                (new_width, new_height),
                self._pil.Resampling.LANCZOS
            )

            # PNG로 인코딩
            buffer = io.BytesIO()
            scaled_img.save(buffer, format="PNG", optimize=True)
            img_bytes = buffer.getvalue()

            # Base64 인코딩
            base64_data = base64.standard_b64encode(img_bytes).decode("utf-8")

            # ScalingInfo 생성
            scaling_info = ScalingInfo(
                enabled=True,
                original_width=original_width,
                original_height=original_height,
                scaled_width=new_width,
                scaled_height=new_height,
                scale_x=original_width / new_width,
                scale_y=original_height / new_height,
            )

            return (
                ScreenAction(
                    action_name,
                    True,
                    data=img_bytes,
                    base64_data=base64_data,
                    metadata={
                        "original_size": f"{original_width}x{original_height}",
                        "scaled_size": f"{new_width}x{new_height}",
                        "target": target.name,
                        "scale_ratio": scale_ratio,
                        "format": "PNG",
                        "size_bytes": len(img_bytes),
                    }
                ),
                scaling_info
            )

        except Exception as e:
            scaling_info = ScalingInfo(enabled=False)
            return (
                ScreenAction(action_name, False, error=str(e)),
                scaling_info
            )
