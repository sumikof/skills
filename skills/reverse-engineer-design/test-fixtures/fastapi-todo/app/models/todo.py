from datetime import date, datetime
from enum import IntEnum
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.category import Category


class Priority(IntEnum):
    """ToDoの優先度"""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    URGENT = 4


class Todo(Base):
    """ToDoモデル"""

    __tablename__ = "todos"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_completed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    priority: Mapped[int] = mapped_column(
        Integer,
        default=Priority.MEDIUM,
        nullable=False,
        comment="1=低, 2=中, 3=高, 4=緊急",
    )
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    # 外部キー
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    category_id: Mapped[int | None] = mapped_column(
        ForeignKey("categories.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # タイムスタンプ
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # リレーション
    user: Mapped["User"] = relationship("User", back_populates="todos")
    category: Mapped["Category | None"] = relationship("Category", back_populates="todos")

    def __repr__(self) -> str:
        return f"<Todo id={self.id} title={self.title!r} user_id={self.user_id}>"
