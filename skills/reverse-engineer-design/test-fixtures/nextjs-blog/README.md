# Next.js Blog

Next.js 14 App Router を使ったブログアプリケーション。

## 技術スタック

- **フレームワーク**: Next.js 14 (App Router)
- **言語**: TypeScript
- **ORM**: Prisma
- **認証**: NextAuth.js v4 (Google / GitHub OAuth)
- **スタイリング**: Tailwind CSS
- **DB**: PostgreSQL

## 機能

- 記事の一覧・詳細表示（カテゴリ・タグ対応）
- ページネーション・カテゴリフィルタ
- コメント投稿（ログインユーザのみ）
- ダッシュボード（自分の記事管理・公開/下書き切替）
- REST API（`/api/posts`, `/api/categories`）

## ディレクトリ構成

```
.
├── app/
│   ├── page.tsx                        # ブログ一覧
│   ├── posts/[slug]/page.tsx           # 記事詳細
│   ├── dashboard/page.tsx              # ダッシュボード（要認証）
│   └── api/
│       ├── posts/route.ts              # GET(一覧) / POST(作成)
│       ├── posts/[id]/route.ts         # GET / PUT / DELETE
│       ├── categories/route.ts         # GET / POST
│       └── auth/[...nextauth]/route.ts # NextAuth ハンドラ
├── components/
│   └── PostCard.tsx                    # 記事カードコンポーネント
└── prisma/
    └── schema.prisma                   # DBスキーマ定義
```

## セットアップ

```bash
# 依存パッケージのインストール
npm install

# 環境変数の設定
cp .env.example .env.local
# DATABASE_URL, NEXTAUTH_SECRET, GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET,
# GITHUB_CLIENT_ID, GITHUB_CLIENT_SECRET を設定

# DBマイグレーション
npm run db:migrate

# 開発サーバ起動
npm run dev
```

## API エンドポイント

| Method | Path | 説明 | 認証 |
|--------|------|------|------|
| GET | /api/posts | 記事一覧（?page, ?limit, ?category, ?tag, ?authorId） | 不要 |
| POST | /api/posts | 記事作成 | 必要 |
| GET | /api/posts/:id | 記事詳細 | 不要 |
| PUT | /api/posts/:id | 記事更新（所有者のみ） | 必要 |
| DELETE | /api/posts/:id | 記事削除（所有者のみ） | 必要 |
| GET | /api/categories | カテゴリ一覧 | 不要 |
| POST | /api/categories | カテゴリ作成 | 必要 |
