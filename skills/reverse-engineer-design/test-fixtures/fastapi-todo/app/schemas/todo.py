from datetime import date, datetime

from pydantic import BaseModel, Field


class TodoCreate(BaseModel):
    """ToDo作成リクエスト"""
    title: str = Field(..., min_length=1, max_length=200, description="ToDoのタイトル")
    description: str | None = Field(None, description="詳細説明")
    priority: int = Field(2, ge=1, le=4, description="優先度（1=低, 2=中, 3=高, 4=緊急）")
    due_date: date | None = Field(None, description="期限日")
    category_id: int | None = Field(None, description="カテゴリID")


class TodoUpdate(BaseModel):
    """ToDo更新リクエスト（全フィールドが任意）"""
    title: str | None = Field(None, min_length=1, max_length=200, description="ToDoのタイトル")
    description: str | None = Field(None, description="詳細説明")
    is_completed: bool | None = Field(None, description="完了フラグ")
    priority: int | None = Field(None, ge=1, le=4, description="優先度（1=低, 2=中, 3=高, 4=緊急）")
    due_date: date | None = Field(None, description="期限日")
    category_id: int | None = Field(None, description="カテゴリID")


class CategorySummary(BaseModel):
    """ToDoレスポンスに含める簡略カテゴリ情報"""
    id: int
    name: str
    color: str | None

    model_config = {"from_attributes": True}


class TodoResponse(BaseModel):
    """ToDoレスポンス"""
    id: int
    title: str
    description: str | None
    is_completed: bool
    priority: int
    due_date: date | None
    user_id: int
    category_id: int | None
    category: CategorySummary | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TodoListResponse(BaseModel):
    """ToDo一覧レスポンス（ページネーション対応）"""
    items: list[TodoResponse]
    total: int
    skip: int
    limit: int
