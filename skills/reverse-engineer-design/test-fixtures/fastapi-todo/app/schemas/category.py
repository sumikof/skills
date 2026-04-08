from datetime import datetime

from pydantic import BaseModel, Field, field_validator
import re


class CategoryCreate(BaseModel):
    """カテゴリ作成リクエスト"""
    name: str = Field(..., min_length=1, max_length=100, description="カテゴリ名")
    color: str | None = Field(None, description="カラーコード（例: #FF5733）")

    @field_validator("color")
    @classmethod
    def validate_color(cls, v: str | None) -> str | None:
        if v is None:
            return v
        if not re.match(r"^#[0-9A-Fa-f]{6}$", v):
            raise ValueError("カラーコードは #RRGGBB 形式で入力してください（例: #FF5733）")
        return v.upper()


class CategoryUpdate(BaseModel):
    """カテゴリ更新リクエスト（全フィールドが任意）"""
    name: str | None = Field(None, min_length=1, max_length=100, description="カテゴリ名")
    color: str | None = Field(None, description="カラーコード（例: #FF5733）")

    @field_validator("color")
    @classmethod
    def validate_color(cls, v: str | None) -> str | None:
        if v is None:
            return v
        if not re.match(r"^#[0-9A-Fa-f]{6}$", v):
            raise ValueError("カラーコードは #RRGGBB 形式で入力してください（例: #FF5733）")
        return v.upper()


class CategoryResponse(BaseModel):
    """カテゴリレスポンス"""
    id: int
    name: str
    color: str | None
    user_id: int
    created_at: datetime

    model_config = {"from_attributes": True}
