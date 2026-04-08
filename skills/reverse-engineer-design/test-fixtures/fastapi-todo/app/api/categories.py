from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.category import Category
from app.models.todo import Todo
from app.models.user import User
from app.schemas.category import CategoryCreate, CategoryResponse, CategoryUpdate

router = APIRouter(prefix="/categories", tags=["カテゴリ"])


@router.get(
    "",
    response_model=list[CategoryResponse],
    summary="カテゴリ一覧取得",
    description="ログイン中のユーザーのカテゴリ一覧を返します。",
)
def list_categories(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[Category]:
    categories = (
        db.query(Category)
        .filter(Category.user_id == current_user.id)
        .order_by(Category.name)
        .all()
    )
    return categories


@router.post(
    "",
    response_model=CategoryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="カテゴリ作成",
    description="新しいカテゴリを作成します。同じユーザーは同名カテゴリを重複して作れません。",
)
def create_category(
    request: CategoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Category:
    # 同じユーザーの同名カテゴリの重複チェック
    existing = db.query(Category).filter(
        Category.user_id == current_user.id,
        Category.name == request.name,
    ).first()
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"カテゴリ名 '{request.name}' はすでに存在します",
        )

    category = Category(
        name=request.name,
        color=request.color,
        user_id=current_user.id,
    )
    db.add(category)
    db.commit()
    db.refresh(category)
    return category


@router.put(
    "/{category_id}",
    response_model=CategoryResponse,
    summary="カテゴリ更新",
    description="指定IDのカテゴリを部分更新します。",
)
def update_category(
    category_id: int,
    request: CategoryUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Category:
    category = db.query(Category).filter(
        Category.id == category_id,
        Category.user_id == current_user.id,
    ).first()
    if category is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="カテゴリが見つかりません",
        )

    # 名前変更時は重複チェック
    if request.name is not None and request.name != category.name:
        existing = db.query(Category).filter(
            Category.user_id == current_user.id,
            Category.name == request.name,
        ).first()
        if existing is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"カテゴリ名 '{request.name}' はすでに存在します",
            )

    update_data = request.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(category, field, value)

    db.commit()
    db.refresh(category)
    return category


@router.delete(
    "/{category_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="カテゴリ削除",
    description="指定IDのカテゴリを削除します。このカテゴリに紐づくToDoのcategory_idはNULLになります。",
)
def delete_category(
    category_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    category = db.query(Category).filter(
        Category.id == category_id,
        Category.user_id == current_user.id,
    ).first()
    if category is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="カテゴリが見つかりません",
        )

    # カテゴリ削除前に紐づくToDoのcategory_idをNULLクリア
    # （DBのON DELETE SET NULLに依存しない場合の明示的な処理）
    db.query(Todo).filter(
        Todo.category_id == category_id,
        Todo.user_id == current_user.id,
    ).update({"category_id": None})

    db.delete(category)
    db.commit()
