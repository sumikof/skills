"""
ナレッジグラフ構築テンプレート (LangGraph + Neo4j)

このテンプレートは以下を行います:
  1. テキストドキュメントを読み込む
  2. LLMGraphTransformer でエンティティ・関係を抽出
  3. Neo4jグラフデータベースに保存
  4. ベクトルインデックスを作成（GraphRAG用）

使い方:
  1. .env に NEO4J_URI/USERNAME/PASSWORD/OPENAI_API_KEY を設定
  2. DOCUMENTS に処理するテキストを追加
  3. python knowledge_graph_builder.py で実行

依存関係:
  pip install langchain-neo4j langchain-experimental langchain-openai neo4j python-dotenv
"""

from dotenv import load_dotenv
from langchain_core.documents import Document
from langchain_experimental.graph_transformers import LLMGraphTransformer
from langchain_neo4j import Neo4jGraph, Neo4jVector
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

load_dotenv()

# ---- 設定 ----

# 抽出するノード・関係タイプ（Noneで全種類を自動抽出）
ALLOWED_NODES = None       # 例: ["Person", "Organization", "Product"]
ALLOWED_RELATIONSHIPS = None  # 例: ["CEO_OF", "WORKS_FOR", "DEVELOPED"]

# ---- サンプルドキュメント（実際のデータに置き換えること）----

DOCUMENTS = [
    Document(page_content="Appleはティム・クックが率いるテクノロジー企業で、iPhoneやMacBookを開発している。"),
    Document(page_content="OpenAIはサム・アルトマンがCEOを務め、GPT-4oやChatGPTを開発した。Microsoftが主要投資家である。"),
    Document(page_content="GoogleはサンダーPichaiがCEOで、Android OSとGemini AIを提供している。"),
]


# ---- ナレッジグラフ構築 ----


def build_knowledge_graph(documents: list[Document]) -> None:
    """ドキュメントからエンティティを抽出してNeo4jに保存する。"""

    print(f"対象ドキュメント数: {len(documents)}")

    # Neo4j接続
    graph = Neo4jGraph()

    # LLMとトランスフォーマーを設定
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    transformer = LLMGraphTransformer(
        llm=llm,
        allowed_nodes=ALLOWED_NODES,
        allowed_relationships=ALLOWED_RELATIONSHIPS,
        node_properties=True,   # ノードのプロパティも抽出
    )

    # エンティティ・関係を抽出
    print("エンティティを抽出中...")
    graph_documents = transformer.convert_to_graph_documents(documents)

    # 抽出結果を確認
    for i, gd in enumerate(graph_documents):
        nodes = [n.id for n in gd.nodes]
        rels = [(r.source.id, r.type, r.target.id) for r in gd.relationships]
        print(f"\nドキュメント {i + 1}:")
        print(f"  ノード: {nodes}")
        print(f"  関係: {rels}")

    # Neo4jに保存（include_source=True でドキュメントノードも保存）
    print("\nNeo4jに保存中...")
    graph.add_graph_documents(graph_documents, include_source=True)
    print(f"{len(graph_documents)} 件のグラフドキュメントを保存しました。")

    # スキーマを表示
    graph.refresh_schema()
    print("\n--- グラフスキーマ ---")
    print(graph.schema)

    return graph


def create_vector_index(graph: Neo4jGraph) -> Neo4jVector:
    """GraphRAG用のベクトルインデックスを作成する。"""
    print("\nベクトルインデックスを作成中...")
    embeddings = OpenAIEmbeddings()

    vector_index = Neo4jVector.from_existing_graph(
        embedding=embeddings,
        search_type="hybrid",
        node_label="Document",
        text_node_properties=["text"],
        embedding_node_property="embedding",
    )
    print("ベクトルインデックスを作成しました。")
    return vector_index


def query_graph(graph: Neo4jGraph, entity_name: str) -> None:
    """特定エンティティの関係を確認する。"""
    result = graph.query("""
        MATCH (n {id: $name}) -[r]-> (m)
        RETURN n.id AS source, type(r) AS relation, m.id AS target
        LIMIT 20
    """, params={"name": entity_name})

    if result:
        print(f"\n'{entity_name}' の関係:")
        for row in result:
            print(f"  {row['source']} --[{row['relation']}]--> {row['target']}")
    else:
        print(f"'{entity_name}' に関する関係が見つかりませんでした。")


# ---- メイン ----


def main():
    # ナレッジグラフを構築
    graph = build_knowledge_graph(DOCUMENTS)

    # ベクトルインデックスを作成（GraphRAG用）
    vector_index = create_vector_index(graph)

    # クエリテスト
    query_graph(graph, "Apple")

    # ベクトル検索テスト
    retriever = vector_index.as_retriever(search_kwargs={"k": 2})
    docs = retriever.invoke("AI企業のCEOについて")
    print("\n--- ベクトル検索結果 ---")
    for doc in docs:
        print(f"  {doc.page_content[:80]}...")


if __name__ == "__main__":
    main()
