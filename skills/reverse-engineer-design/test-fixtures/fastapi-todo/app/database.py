from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker, Session

from app.core.config import settings

# SQLiteの場合はcheck_same_thread=Falseが必要
connect_args = {}
if settings.database_url.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(
    settings.database_url,
    connect_args=connect_args,
    echo=settings.debug,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """全モデルの基底クラス"""
    pass


def get_db() -> Session:
    """DBセッションを生成するジェネレーター（依存注入用）"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
