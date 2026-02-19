# Neo4j セットアップ

## 方法1: Docker（ローカル開発推奨）

```bash
docker run \
  --name neo4j \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/password \
  -e NEO4J_PLUGINS='["apoc", "graph-data-science"]' \
  neo4j:5
```

- ブラウザUI: http://localhost:7474
- Bolt接続: `bolt://localhost:7687`
- 初期認証: `neo4j` / `password`

プラグイン説明:
- `apoc` - 汎用手続きライブラリ（必須に近い）
- `graph-data-science` - グラフアルゴリズム（GraphRAGで活用可能）

## 方法2: Neo4j AuraDB（クラウド・無料枠あり）

1. https://neo4j.com/cloud/platform/aura-graph-database/ でアカウント作成
2. 「Create Free Instance」でインスタンス作成
3. 接続情報をダウンロード（`.env`形式）

```bash
NEO4J_URI=neo4j+s://xxxxxxxx.databases.neo4j.io
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your-generated-password
```

AuraDB URIは `neo4j+s://`（TLS付き）を使うこと。

## 方法3: Neo4j Desktop（GUIツール）

https://neo4j.com/download/ からインストール。
ローカル開発に便利なGUI管理ツール付き。

## 接続確認

```python
from langchain_neo4j import Neo4jGraph
from dotenv import load_dotenv

load_dotenv()
graph = Neo4jGraph()

# スキーマを確認
print(graph.schema)

# 簡単なクエリ
result = graph.query("RETURN 1 AS n")
print(result)  # [{'n': 1}]
```

## ベクトルインデックスの前提条件

Neo4jのベクトル検索（`Neo4jVector`）には Neo4j 5.11以上が必要。
Docker/AuraDB の最新版であれば問題ない。

## スキーマリセット（開発時）

```python
# 全ノード・リレーションシップを削除（開発時のリセット用）
graph.query("MATCH (n) DETACH DELETE n")

# インデックスも削除する場合
graph.query("CALL apoc.schema.assert({}, {})")
```

## よくある接続エラー

| エラー | 原因 | 対処 |
|---|---|---|
| `ServiceUnavailable` | Neo4jが起動していない | Dockerコンテナ/AuraDB状態を確認 |
| `AuthError` | 認証情報が間違い | パスワードを確認、初期変更が必要な場合あり |
| `ClientError: SSLError` | AuraDBにbolt://で接続 | `neo4j+s://` を使う |
| `Neo4jError: vector index` | Neo4jのバージョンが古い | 5.11以上を使う |
