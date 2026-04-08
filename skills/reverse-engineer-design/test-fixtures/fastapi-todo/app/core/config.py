from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # アプリ設定
    app_name: str = "FastAPI ToDo API"
    debug: bool = False

    # データベース
    database_url: str = "sqlite:///./todo.db"

    # JWT設定
    secret_key: str = "change-me-in-production-use-openssl-rand-hex-32"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # CORS設定
    allowed_origins: list[str] = ["http://localhost:3000", "http://localhost:5173"]

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
