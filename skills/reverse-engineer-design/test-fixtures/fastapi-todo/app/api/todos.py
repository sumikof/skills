from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.todo import Priority, Todo
from app.models.user import User
from app.schemas.todo import TodoCreate, TodoListResponse, TodoResponse, TodoUpdate

router = APIRouter(prefix="/todos", tags=["ToDo"])


@router.get(
    "",
    response_model=TodoListResponse,
    summary="ToDo一覧取得",
    description="ログイン中のユーザーのToDo一覧を返します。完了状態・優先度・カテゴリでフィルタ可能。",
)
def list_todos(
    is_completed: bool | None = Query(None, description="完了状態でフィルタ"),
    priority: int | None = Query(None, ge=1, le=4, description="優先度でフィルタ（1=低, 2=中, 3=高, 4=緊急）"),
    category_id: int | None = Query(None, description="カテゴリIDでフィルタ"),
    skip: int = Query(0, ge=0, description="スキップ件数（ページネーション用）"),
    limit: int = Query(20, ge=1, le=100, description="取得件数上限"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TodoListResponse:
    query = db.query(Todo).filter(Todo.user_id == current_user.id)

    if is_completed is not None:
        query = query.filter(Todo.is_completed == is_completed)
    if priority is not None:
        query = query.filter(Todo.priority == priority)
    if category_id is not None:
        query = query.filter(Todo.category_id == category_id)

    total = query.count()
    items = (
        query
        .order_by(Todo.priority.desc(), Todo.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    return TodoListResponse(items=items, total=total, skip=skip, limit=limit)


@router.post(
    "",
    response_model=TodoResponse,
    status_code=status.HTTP_201_CREATED,
    summary="ToDo作成",
    description="新しいToDoを作成します。",
)
def create_todo(
    request: TodoCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Todo:
    # カテゴリが指定されている場合は所有チェック
    if request.category_id is not None:
        from app.models.category import Category
        category = db.query(Category).filter(
            Category.id == request.category_id,
            Category.user_id == current_user.id,
        ).first()
        if category is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="指定されたカテゴリが見つかりません",
            )

    todo = Todo(
        title=request.title,
        description=request.description,
        priority=request.priority,
        due_date=request.due_date,
        category_id=request.category_id,
        user_id=current_user.id,
    )
    db.add(todo)
    db.commit()
    db.refresh(todo)
    return todo


@router.get(
    "/by-category/{category_id}",
    response_model=list[TodoResponse],
    summary="カテゴリ別ToDo取得",
    description="指定カテゴリに属するToDoを全件返します。",
)
def list_todos_by_category(
    category_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[Todo]:
    # カテゴリの所有チェック
    from app.models.category import Category
    category = db.query(Category).filter(
        Category.id == category_id,
        Category.user_id == current_user.id,
    ).first()
    if category is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="指定されたカテゴリが見つかりません",
        )

    todos = (
        db.query(Todo)
        .filter(Todo.user_id == current_user.id, Todo.category_id == category_id)
        .order_by(Todo.priority.desc(), Todo.created_at.desc())
        .all()
    )
    return todos


@router.get(
    "/{todo_id}",
    response_model=TodoResponse,
    summary="ToDo詳細取得",
    description="指定IDのToDoを取得します。",
)
def get_todo(
    todo_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Todo:
    todo = db.query(Todo).filter(
        Todo.id == todo_id,
        Todo.user_id == current_user.id,
    ).first()
    if todo is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="ToDoが見つかりません",
        )
    return todo


@router.put(
    "/{todo_id}",
    response_model=TodoResponse,
    summary="ToDo更新",
    description="指定IDのToDoを部分更新します。送信したフィールドのみが更新されます。",
)
def update_todo(
    todo_id: int,
    request: TodoUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Todo:
    todo = db.query(Todo).filter(
        Todo.id == todo_id,
        Todo.user_id == current_user.id,
    ).first()
    if todo is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="ToDoが見つかりません",
        )

    # カテゴリの変更がある場合は所有チェック
    if request.category_id is not None:
        from app.models.category import Category
        category = db.query(Category).filter(
            Category.id == request.category_id,
            Category.user_id == current_user.id,
        ).first()
        if category is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="指定されたカテゴリが見つかりません",
            )

    # 送信されたフィールドのみ更新（exclude_unsetで未送信フィールドを無視）
    update_data = request.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(todo, field, value)

    db.commit()
    db.refresh(todo)
    return todo


@router.delete(
    "/{todo_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="ToDo削除",
    description="指定IDのToDoを削除します。",
)
def delete_todo(
    todo_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    todo = db.query(Todo).filter(
        Todo.id == todo_id,
        Todo.user_id == current_user.id,
    ).first()
    if todo is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="ToDoが見つかりません",
        )

    db.delete(todo)
    db.commit()
