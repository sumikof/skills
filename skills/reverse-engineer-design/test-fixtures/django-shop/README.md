# Django Shop

Django + Django REST Framework を使ったECサイト。

## 技術スタック

- **フレームワーク**: Django 4.2
- **API**: Django REST Framework 3.14
- **認証**: Django 標準認証 + カスタムユーザモデル
- **決済**: Stripe
- **画像処理**: Pillow
- **フィルタ**: django-filter
- **DB**: PostgreSQL（開発環境は SQLite）

## 機能

- 商品一覧・詳細表示（カテゴリ別フィルタ）
- ユーザ登録・ログイン・プロフィール管理
- カート（追加・削除・数量変更）
- 注文管理（チェックアウト・注文履歴）
- REST API（`/api/v1/products/`, `/api/v1/categories/`）

## ディレクトリ構成

```
.
├── config/
│   └── urls.py                 # メインURLconf
├── apps/
│   ├── accounts/
│   │   ├── models.py           # CustomUser
│   │   └── urls.py             # 認証URL
│   ├── products/
│   │   ├── models.py           # Product, Category
│   │   └── urls.py             # 商品URL + API
│   └── orders/
│       ├── models.py           # Cart, CartItem, Order, OrderItem
│       └── urls.py             # カート・注文URL
└── templates/
    ├── products/
    │   ├── list.html           # 商品一覧
    │   └── detail.html         # 商品詳細
    └── orders/
        └── cart.html           # カート
```

## セットアップ

```bash
# 仮想環境の作成・有効化
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 依存パッケージのインストール
pip install -r requirements.txt

# 環境変数の設定
cp .env.example .env
# SECRET_KEY, DATABASE_URL, STRIPE_SECRET_KEY などを設定

# マイグレーション
python manage.py migrate

# スーパーユーザの作成
python manage.py createsuperuser

# 開発サーバ起動
python manage.py runserver
```

## URL 一覧

| URL | 説明 |
|-----|------|
| /accounts/register/ | ユーザ登録 |
| /accounts/login/ | ログイン |
| /accounts/logout/ | ログアウト |
| /accounts/profile/ | プロフィール |
| /products/ | 商品一覧 |
| /products/{slug}/ | 商品詳細 |
| /products/categories/ | カテゴリ一覧 |
| /orders/cart/ | カート |
| /orders/cart/add/ | カートに追加 |
| /orders/cart/remove/ | カートから削除 |
| /orders/checkout/ | チェックアウト |
| /orders/orders/ | 注文履歴 |
| /orders/orders/{id}/ | 注文詳細 |
| /api/v1/products/ | 商品API |
| /api/v1/products/{id}/ | 商品詳細API |
| /api/v1/categories/ | カテゴリAPI |
