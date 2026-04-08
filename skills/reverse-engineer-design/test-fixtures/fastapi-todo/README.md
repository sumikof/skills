# FastAPI ToDo API

FastAPI + SQLAlchemy + JWT認証を使ったToDo管理REST APIです。

## 機能

- ユーザー登録・ログイン（JWT認証）
- ToDoの作成・取得・更新・削除（CRUD）
- カテゴリによるToDoの分類
- 優先度・期限・完了状態の管理

## 技術スタック

| 分類 | 技術 |
|---|---|
| Webフレームワーク | FastAPI 0.111 |
| ORM | SQLAlchemy 2.0 |
| バリデーション | Pydantic v2 |
| 認証 | python-jose（JWT）、passlib（bcrypt） |
| DBマイグレーション | Alembic |
| サーバー | Uvicorn |
| DB | SQLite（開発）/ PostgreSQL（本番） |

## セットアップ

```bash
# 依存パッケージのインストール
uv sync

# DBマイグレーション
uv run alembic upgrade head

# 開発サーバー起動
uv run uvicorn app.main:app --reload
```

## API エンドポイント

### 認証

| メソッド | パス | 説明 |
|---|---|---|
| POST | /auth/register | ユーザー登録 |
| POST | /auth/login | ログイン（JWTトークン取得） |

### ToDo

| メソッド | パス | 説明 |
|---|---|---|
| GET | /todos | ToDo一覧取得 |
| POST | /todos | ToDo作成 |
| GET | /todos/{id} | ToDo詳細取得 |
| PUT | /todos/{id} | ToDo更新 |
| DELETE | /todos/{id} | ToDo削除 |
| GET | /todos/by-category/{category_id} | カテゴリ別ToDo取得 |

### カテゴリ

| メソッド | パス | 説明 |
|---|---|---|
| GET | /categories | カテゴリ一覧取得 |
| POST | /categories | カテゴリ作成 |
| PUT | /categories/{id} | カテゴリ更新 |
| DELETE | /categories/{id} | カテゴリ削除 |

## プロジェクト構成

```
fastapi-todo/
├── README.md
├── pyproject.toml
├── alembic.ini
├── alembic/
│   └── versions/
└── app/
    ├── main.py              # FastAPIアプリ本体
    ├── database.py          # DB接続設定
    ├── dependencies.py      # 共通依存関係
    ├── core/
    │   ├── config.py        # 設定値
    │   └── security.py      # JWT・パスワードハッシュ
    ├── api/
    │   ├── auth.py          # 認証ルーター
    │   ├── todos.py         # ToDoルーター
    │   └── categories.py    # カテゴリルーター
    ├── models/
    │   ├── user.py          # Userモデル
    │   ├── todo.py          # Todoモデル
    │   └── category.py      # Categoryモデル
    └── schemas/
        ├── auth.py          # 認証スキーマ
        ├── todo.py          # ToDoスキーマ
        └── category.py      # カテゴリスキーマ
```

## 認証フロー

1. `POST /auth/register` でユーザー登録
2. `POST /auth/login` でJWTアクセストークン取得
3. 以降のリクエストは `Authorization: Bearer <token>` ヘッダーを付与

## 環境変数

| 変数名 | デフォルト | 説明 |
|---|---|---|
| `DATABASE_URL` | `sqlite:///./todo.db` | DB接続URL |
| `SECRET_KEY` | （必須） | JWT署名キー |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `30` | トークン有効期限（分） |
| `ALLOWED_ORIGINS` | `["http://localhost:3000"]` | CORSオリジン |
