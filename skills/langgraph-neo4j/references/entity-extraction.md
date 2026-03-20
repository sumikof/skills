# エンティティ抽出・ナレッジグラフ構築

LangChainの `LLMGraphTransformer` を使ってドキュメントからエンティティと関係を抽出し、Neo4jに保存する。

## 基本パターン

```python
from langchain_core.documents import Document
from langchain_experimental.graph_transformers import LLMGraphTransformer
from langchain_neo4j import Neo4jGraph
from langchain_openai import ChatOpenAI

graph = Neo4jGraph()
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
transformer = LLMGraphTransformer(llm=llm)

# ドキュメントを準備
documents = [
    Document(page_content="Apple社はティム・クックが率いており、iPhone 15を発売した。"),
    Document(page_content="OpenAIはサム・アルトマンがCEOを務め、GPT-4oを開発した。"),
]

# エンティティ・関係を抽出
graph_documents = transformer.convert_to_graph_documents(documents)

# グラフの内容を確認
for gd in graph_documents:
    print("ノード:", [n.id for n in gd.nodes])
    print("関係:", [(r.source.id, r.type, r.target.id) for r in gd.relationships])

# Neo4jに保存
graph.add_graph_documents(graph_documents, include_source=True)
```

## 抽出するエンティティ・関係を指定する

デフォルトではLLMが自由に抽出するが、ドメインに合わせて制約できる。

```python
transformer = LLMGraphTransformer(
    llm=llm,
    # 抽出するノードタイプを指定（指定なしで全種類）
    allowed_nodes=["Person", "Organization", "Product", "Location"],
    # 抽出する関係タイプを指定
    allowed_relationships=["CEO_OF", "WORKS_FOR", "DEVELOPED", "LOCATED_IN"],
    # ノードのプロパティも抽出する
    node_properties=["description", "founded_year"],
    relationship_properties=["since"],
)
```

## 大量ドキュメントの処理

```python
from langchain_text_splitters import TokenTextSplitter
from langchain_community.document_loaders import DirectoryLoader

# ドキュメントを読み込んでチャンク分割
loader = DirectoryLoader("./docs", glob="**/*.txt")
raw_docs = loader.load()

splitter = TokenTextSplitter(chunk_size=512, chunk_overlap=24)
documents = splitter.split_documents(raw_docs)

# バッチ処理（LLMコール削減のため）
# convert_to_graph_documents はリストを受け取るのでそのまま渡せる
graph_documents = transformer.convert_to_graph_documents(documents)
graph.add_graph_documents(graph_documents, include_source=True)
print(f"処理完了: {len(documents)} チャンク → {len(graph_documents)} グラフドキュメント")
```

## ベクトルインデックスの作成（GraphRAG用）

ナレッジグラフ構築後、ベクトル検索も使えるようにインデックスを作成する。

```python
from langchain_neo4j import Neo4jVector
from langchain_openai import OpenAIEmbeddings

# ソースドキュメントのベクトルインデックスを作成
# （add_graph_documents で include_source=True にした場合）
vector_index = Neo4jVector.from_existing_graph(
    embedding=OpenAIEmbeddings(),
    search_type="hybrid",          # ベクトル + キーワードのハイブリッド
    node_label="Document",         # include_source=True で作成されるノード
    text_node_properties=["text"],
    embedding_node_property="embedding",
)
```

## グラフ構造の確認

```python
# 保存されたスキーマを確認
graph.refresh_schema()
print(graph.schema)

# ノード数を確認
result = graph.query("MATCH (n) RETURN labels(n) AS label, count(n) AS count")
for r in result:
    print(f"{r['label']}: {r['count']}件")

# 特定エンティティの関係を確認
result = graph.query("""
    MATCH (n {id: 'Apple'}) -[r]-> (m)
    RETURN type(r) AS relation, m.id AS target
""")
print(result)
```

## LangGraphノードとしての実装例

```python
from langgraph.graph import StateGraph, MessagesState, START, END

class KGState(MessagesState):
    documents: list  # 処理するドキュメント

def extract_and_store(state: KGState) -> dict:
    """ドキュメントからエンティティを抽出してNeo4jに保存するノード。"""
    graph_docs = transformer.convert_to_graph_documents(state["documents"])
    graph.add_graph_documents(graph_docs, include_source=True)
    return {"messages": [f"{len(graph_docs)}件のグラフドキュメントを保存しました。"]}
```

## よくある問題

| 問題 | 対処 |
|---|---|
| 抽出精度が低い | `gpt-4o` など高性能モデルを使う |
| 同じエンティティが別名で重複 | `allowed_nodes` で正規化するか、後処理でマージ |
| コストが高い | チャンクサイズを大きくする・必要なドキュメントのみ処理 |
| 関係が抽出されない | システムプロンプトをカスタマイズして関係の例を与える |
