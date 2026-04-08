# フレームワーク別分析ガイド

ソースコードの分析時に、フレームワーク固有のファイル配置パターンを知っていると、重要なファイルを素早く見つけられる。このガイドでは主要なフレームワークごとの分析ポイントを示す。

## 目次

1. [Next.js / React](#nextjs--react)
2. [Nuxt.js / Vue](#nuxtjs--vue)
3. [Django](#django)
4. [FastAPI](#fastapi)
5. [Ruby on Rails](#ruby-on-rails)
6. [Express / NestJS](#express--nestjs)
7. [Spring Boot](#spring-boot)
8. [Laravel](#laravel)
9. [Flutter](#flutter)
10. [Go (Gin / Echo)](#go-gin--echo)
11. [Rust (Actix / Axum)](#rust-actix--axum)

---

## Next.js / React

### プロジェクト識別
- `next.config.js` / `next.config.ts` の存在
- `package.json` に `next` 依存

### ルーティング
- **App Router**: `app/` ディレクトリ内の `page.tsx`, `layout.tsx`, `route.ts`
- **Pages Router**: `pages/` ディレクトリ内の `.tsx` ファイル
- **APIルート**: `app/api/` or `pages/api/` 内の `route.ts` / `.ts` ファイル

### モデル/データ
- Prisma: `prisma/schema.prisma`
- Drizzle: `drizzle/` or `src/db/schema.ts`
- 型定義: `types/` or `src/types/`

### 画面構成
- `app/` 内の各ディレクトリが画面に対応
- `components/` にUI部品
- `(group)` ディレクトリでレイアウトグループ化

### 状態管理
- `store/`, `context/`, `hooks/` を確認
- Zustand, Redux, Jotai, React Context の使用パターン

---

## Nuxt.js / Vue

### プロジェクト識別
- `nuxt.config.ts` の存在
- `package.json` に `nuxt` 依存

### ルーティング
- `pages/` ディレクトリのファイルベースルーティング
- `server/api/` にAPIルート（Nuxt 3）

### モデル/データ
- `server/models/` or `server/database/`
- Nitro サーバーエンジン

### 画面構成
- `pages/` が画面に対応
- `components/` にUI部品
- `layouts/` にレイアウト定義

---

## Django

### プロジェクト識別
- `manage.py`, `settings.py` の存在
- `requirements.txt` or `pyproject.toml` に `django`

### ルーティング
- `urls.py`（プロジェクト/アプリレベル）
- `urlpatterns` リストからすべてのパスを抽出

### モデル/データ
- `models.py`（各アプリ内）
- `migrations/` ディレクトリ
- `admin.py`（管理画面のモデル登録状況）

### 画面構成
- `templates/` ディレクトリ
- `views.py` のビュー関数/クラス
- `forms.py` のフォーム定義

### 認証
- `django.contrib.auth` の使用
- カスタムユーザーモデル（`AUTH_USER_MODEL`）
- `permissions.py`, `decorators.py`

---

## FastAPI

### プロジェクト識別
- `main.py` or `app.py` に `FastAPI()` インスタンス
- `requirements.txt` or `pyproject.toml` に `fastapi`

### ルーティング
- `@app.get()`, `@app.post()` 等のデコレータ
- `APIRouter` を使ったルーター分割（`routers/` ディレクトリ）
- `app.include_router()` でルーター登録

### モデル/データ
- Pydantic モデル: `schemas/` or `models/` 内の `BaseModel` 継承クラス
- SQLAlchemy モデル: `models/` 内の `Base` 継承クラス
- Alembic マイグレーション: `alembic/versions/`

### 認証
- `Depends()` によるDI
- OAuth2, JWT の実装パターン
- `security.py` or `auth.py`

---

## Ruby on Rails

### プロジェクト識別
- `Gemfile` に `rails`
- `config/routes.rb` の存在

### ルーティング
- `config/routes.rb`（`resources`, `namespace`, `scope` 等）
- `rails routes` コマンドの出力に相当する情報を抽出

### モデル/データ
- `app/models/` 内のActiveRecordモデル
- `db/schema.rb` or `db/structure.sql`
- `db/migrate/` のマイグレーションファイル

### 画面構成
- `app/views/` のERBテンプレート
- `app/controllers/` のコントローラアクション
- `app/helpers/` のヘルパー

---

## Express / NestJS

### プロジェクト識別
- `package.json` に `express` or `@nestjs/core`

### ルーティング（Express）
- `router.get()`, `router.post()` 等
- `routes/` ディレクトリ内のルーター定義
- ミドルウェア: `middleware/` ディレクトリ

### ルーティング（NestJS）
- `@Controller()`, `@Get()`, `@Post()` デコレータ
- `*.controller.ts` ファイル
- `*.module.ts` でモジュール構成を把握

### モデル/データ
- TypeORM: `*.entity.ts` ファイル
- Prisma: `prisma/schema.prisma`
- Mongoose: `*.schema.ts` or `*.model.ts`

---

## Spring Boot

### プロジェクト識別
- `pom.xml` or `build.gradle` に `spring-boot`
- `@SpringBootApplication` アノテーション

### ルーティング
- `@RestController` + `@RequestMapping` / `@GetMapping` / `@PostMapping`
- `controller/` パッケージ内のクラス

### モデル/データ
- `@Entity` アノテーション付きクラス（`entity/` or `model/` パッケージ）
- `@Repository` インターフェース（Spring Data JPA）
- `resources/` 内のSQL/Flyway/Liquibaseマイグレーション

### 画面構成
- Thymeleaf: `resources/templates/`
- REST API のみの場合は画面なし

---

## Laravel

### プロジェクト識別
- `artisan` ファイルの存在
- `composer.json` に `laravel/framework`

### ルーティング
- `routes/web.php`（Web画面）
- `routes/api.php`（API）
- `Route::resource()`, `Route::group()` 等

### モデル/データ
- `app/Models/` 内の Eloquent モデル
- `database/migrations/` のマイグレーション
- `database/factories/`, `database/seeders/`

### 画面構成
- `resources/views/` の Blade テンプレート
- `resources/js/` のフロントエンド（Vue/React との連携）

---

## Flutter

### プロジェクト識別
- `pubspec.yaml` に `flutter`
- `lib/main.dart`

### ルーティング（ナビゲーション）
- `MaterialApp` の `routes` プロパティ
- `GoRouter`, `AutoRoute` 等のパッケージ
- `Navigator.push()` の呼び出し箇所

### モデル/データ
- `models/` ディレクトリ内のDartクラス
- `freezed` / `json_serializable` の使用
- ローカルDB: `sqflite`, `hive`, `drift`

### 画面構成
- `screens/` or `pages/` 内のWidgetクラス
- `widgets/` に再利用可能なUI部品
- 状態管理: `riverpod`, `bloc`, `provider`

---

## Go (Gin / Echo)

### プロジェクト識別
- `go.mod` に `gin-gonic/gin` or `labstack/echo`

### ルーティング
- `r.GET()`, `r.POST()` 等（Gin）
- `e.GET()`, `e.POST()` 等（Echo）
- ルートグループ: `r.Group()`

### モデル/データ
- GORM: `type User struct` + `gorm:"..."` タグ
- `models/` パッケージ内の構造体
- マイグレーション: `migrate/` or `migrations/`

---

## Rust (Actix / Axum)

### プロジェクト識別
- `Cargo.toml` に `actix-web` or `axum`

### ルーティング
- Actix: `web::resource()`, `web::scope()`
- Axum: `Router::new().route()`, `.nest()`
- `handlers/` or `routes/` モジュール

### モデル/データ
- Diesel: `schema.rs`, `models.rs`
- SQLx: `migrations/` ディレクトリ
- SeaORM: `entity/` ディレクトリ
