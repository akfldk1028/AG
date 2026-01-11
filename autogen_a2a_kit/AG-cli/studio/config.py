# AG-CLI Agent Configuration
"""
전역 설정 모듈

사용법:
    from config import config
    print(config.WORK_FOLDER)
    config.update(folder="frontend", expertise="React")
"""
from pathlib import Path


class Config:
    """전역 설정 클래스 (Singleton 패턴)"""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True

        # 기본값 설정
        self.WORK_FOLDER = "project"
        self.SHARED_FOLDER = "shared"
        self.EXPERTISE = "General"
        self.MAX_TURNS = 10
        self.VERBOSE_MODE = False

        # 외부 서비스 URL (현재 미사용)
        self.MESSAGE_BUS_URL = "http://localhost:8100"
        self.SHARED_MEMORY_URL = "http://localhost:8101"

        # 로그 디렉토리
        self.LOG_DIR = Path("logs")
        self.LOG_DIR.mkdir(exist_ok=True)

    def update(self, **kwargs):
        """설정값 업데이트

        Args:
            folder: 작업 폴더
            shared_folder: 공유 폴더
            expertise: 전문 분야
            max_turns: 최대 턴 수
            verbose: 상세 로그 모드
        """
        if "folder" in kwargs:
            self.WORK_FOLDER = kwargs["folder"]
        if "shared_folder" in kwargs:
            self.SHARED_FOLDER = kwargs["shared_folder"]
        if "expertise" in kwargs:
            self.EXPERTISE = kwargs["expertise"]
        if "max_turns" in kwargs:
            self.MAX_TURNS = kwargs["max_turns"]
        if "verbose" in kwargs:
            self.VERBOSE_MODE = kwargs["verbose"]

    def __repr__(self):
        return (
            f"Config(WORK_FOLDER={self.WORK_FOLDER}, "
            f"SHARED_FOLDER={self.SHARED_FOLDER}, "
            f"EXPERTISE={self.EXPERTISE}, "
            f"MAX_TURNS={self.MAX_TURNS})"
        )


# 싱글톤 인스턴스
config = Config()
