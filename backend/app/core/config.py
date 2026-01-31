from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """应用配置"""
    APP_NAME: str = "FundPro API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    # CORS配置
    CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]
    
    # 数据文件路径
    DATA_DIR: str = "data"
    
    class Config:
        env_file = ".env"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
