---
name: langgraph-neo4j
description: "LangGraph + Neo4j グラフデータベースの構築・活用をサポートする。Use when the user wants to: (1) Neo4jをLangGraphエージェントで使う, (2) ドキュメントからエンティティ・関係を抽出してナレッジグラフを構築する, (3) GraphRAG（グラフベースの検索拡張生成）を実装する, (4) 自然言語からCypherクエリを自動生成する, (5) Neo4jをLangGraphのメモリ・ストアとして活用する, (6) ベクトル検索とグラフ検索のハイブリッド検索を実装する。キーワード例: 'ナレッジグラフ', '知識グラフ', 'GraphRAG', 'Neo4j', 'グラフDB', 'エンティティ抽出', 'Cypher'."
---

# LangGraph + Neo4j

Neo4jグラフデータベースをLangGraph 1.0+と組み合わせて使うためのスキル。

**必須環境**: Python 3.10以上、Neo4j 5.x以上

## 依存関係のインストール

```bash
pip install langchain-neo4j langchain-experimental neo4j python-dotenv langchain-openai langgraph
```

## 環境変数

```bash
# .envファイル
NEO4J_URI=bolt://localhost:7687      # AuraDB: neo4j+s://xxxxx.databases.neo4j.io
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your-password
OPENAI_API_KEY=your-key
```

## ユースケース別ガイド

| やりたいこと | 参照ファイル |
|---|---|
| Neo4jの起動・接続設定 | `references/setup.md` |
| ドキュメントからナレッジグラフを構築 | `references/entity-extraction.md` |
| GraphRAGエージェントを実装 | `references/graphrag.md` |

## 基本接続

```python
from dotenv import load_dotenv
from langchain_neo4j import Neo4jGraph

load_dotenv()

graph = Neo4jGraph()  # 環境変数 NEO4J_URI/USERNAME/PASSWORD を自動読み込み
# または明示的に指定:
# graph = Neo4jGraph(url="bolt://localhost:7687", username="neo4j", password="pass")

# 接続確認
print(graph.schema)
```

## 典型的なワークフロー

### パターン1: ナレッジグラフ構築 → GraphRAG

```
ドキュメント
  → LLMGraphTransformer でエンティティ・関係を抽出
  → Neo4jGraph.add_graph_documents() でグラフに保存
  → Neo4jVector でベクトルインデックスを作成
  → LangGraphエージェント (retrieval node) で検索・回答生成
```

詳細: `references/entity-extraction.md` → `references/graphrag.md`

### パターン2: 既存データへのCypherクエリ生成

```
ユーザの質問
  → LLM が Cyphercクエリを生成
  → Neo4j でクエリ実行
  → 結果をLLMが自然言語に変換
```

詳細: `references/graphrag.md` の「Cypherクエリ自動生成」セクション

## テンプレートファイル

- `assets/templates/knowledge_graph_builder.py` - ナレッジグラフ構築の完全サンプル
- `assets/templates/graphrag_agent.py` - GraphRAGエージェントの完全サンプル
