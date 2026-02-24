from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Phase 2: Drift Detection & Risk Scoring
    DRIFT_WINDOW_SIZE: int = 100
    PSI_THRESHOLD: float = 0.25
    KS_THRESHOLD: float = 0.2
    
    # Phase 3: Fairness Monitoring
    FAIRNESS_THRESHOLD: float = 0.1

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
