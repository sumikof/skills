from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.database import Base, engine
from app.api import auth, todos, categories


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """アプリケーションのライフサイクル管理"""
    # startup: テーブルが存在しない場合のみ作成（開発用。本番はAlembicを使用）
    Base.metadata.create_all(bind=engine)
    yield
    # shutdown: 必要に応じてクリーンアップ処理を追加


app = FastAPI(
    title=settings.app_name,
    description="FastAPI + SQLAlchemy + JWT認証によるToDo管理REST API",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

# ルーター登録
app.include_router(auth.router)
app.include_router(todos.router)
app.include_router(categories.router)


@app.get("/", tags=["ヘルスチェック"], summary="ルートエンドポイント")
def root() -> dict[str, str]:
    """APIの稼働確認用エンドポイント"""
    return {"status": "ok", "app": settings.app_name}


@app.get("/health", tags=["ヘルスチェック"], summary="ヘルスチェック")
def health_check() -> dict[str, str]:
    """ヘルスチェック用エンドポイント（ロードバランサー等から利用）"""
    return {"status": "healthy"}
