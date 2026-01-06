"""
설정 파일 로더 - YAML/dict에서 에이전트 설정 로드
"""

import os
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional, List, Any
import yaml
from dotenv import load_dotenv


@dataclass
class AgentConfig:
    """에이전트 설정 데이터 클래스"""
    name: str
    model: str = "openai/gpt-4o-mini"
    description: str = ""
    instruction: str = ""
    port: int = 8001
    host: str = "127.0.0.1"
    
    # 환경 변수
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    
    # 추가 설정
    extra: dict = field(default_factory=dict)
    
    def __post_init__(self):
        """환경 변수에서 API 키 로드"""
        if not self.openai_api_key:
            self.openai_api_key = os.getenv("OPENAI_API_KEY")
        if not self.anthropic_api_key:
            self.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")


def load_config(config_path: str | Path | dict) -> AgentConfig:
    """
    설정 로드 (YAML 파일 또는 dict)
    
    Args:
        config_path: YAML 파일 경로 또는 dict
        
    Returns:
        AgentConfig 객체
        
    Example:
        # YAML 파일에서
        config = load_config("config.yaml")
        
        # dict에서
        config = load_config({
            "name": "my_agent",
            "model": "openai/gpt-4o-mini"
        })
    """
    # .env 파일 로드
    load_dotenv()
    
    if isinstance(config_path, dict):
        data = config_path
    else:
        path = Path(config_path)
        if not path.exists():
            raise FileNotFoundError(f"설정 파일을 찾을 수 없습니다: {path}")
        
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
    
    # 기본 필드 추출
    known_fields = {
        "name", "model", "description", "instruction", 
        "port", "host", "openai_api_key", "anthropic_api_key"
    }
    
    main_config = {k: v for k, v in data.items() if k in known_fields}
    extra_config = {k: v for k, v in data.items() if k not in known_fields}
    
    return AgentConfig(**main_config, extra=extra_config)


def save_config(config: AgentConfig, path: str | Path) -> None:
    """설정을 YAML 파일로 저장"""
    data = {
        "name": config.name,
        "model": config.model,
        "description": config.description,
        "instruction": config.instruction,
        "port": config.port,
        "host": config.host,
    }
    data.update(config.extra)
    
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(data, f, allow_unicode=True, default_flow_style=False)
