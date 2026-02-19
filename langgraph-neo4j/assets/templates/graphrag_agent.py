"""
GraphRAGエージェント テンプレート (LangGraph + Neo4j)

このテンプレートは以下を示します:
  - Neo4jナレッジグラフを検索ツールとして持つReActエージェント
  - ベクトル検索 + グラフトラバーサルのハイブリッド検索
  - Cypherクエリ自動生成ツール

使い方:
  1. knowledge_graph_builder.py を先に実行してグラフを構築すること
  2. .env に NEO4J_URI/USERNAME/PASSWORD/OPENAI_API_KEY を設定
  3. python graphrag_agent.py で実行

依存関係:
  pip install langchain-neo4j langchain-openai langgraph neo4j python-dotenv
"""

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage
from langchain_core.tools import tool
from langchain_neo4j import GraphCypherQAChain, Neo4jGraph, Neo4jVector
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langgraph.prebuilt import create_react_agent

load_dotenv()

# ---- Neo4j 接続 ----

graph = Neo4jGraph()

# ベクトルインデックスに接続（knowledge_graph_builder.py で作成済みであること）
try:
    vector_retriever = Neo4jVector.from_existing_index(
        embedding=OpenAIEmbeddings(),
        index_name="vector",
        node_label="Document",
        text_node_property="text",
        embedding_node_property="embedding",
    ).as_retriever(search_kwargs={"k": 3})
    VECTOR_AVAILABLE = True
except Exception:
    VECTOR_AVAILABLE = False
    print("警告: ベクトルインデックスが見つかりません。knowledge_graph_builder.py を先に実行してください。")

# ---- ツール定義 ----


@tool
def search_knowledge_graph(query: str) -> str:
    """
    ナレッジグラフをベクトル検索 + グラフトラバーサルで検索する。
    エンティティに関連する情報や関係を取得するときに使う。
    """
    contexts = []

    # ベクトル検索
    if VECTOR_AVAILABLE:
        docs = vector_retriever.invoke(query)
        for doc in docs:
            contexts.append(doc.page_content)

            # ドキュメントに関連するグラフ情報を追加取得
            entity_data = graph.query(
                """
                MATCH (d:Document {text: $text}) <-[:MENTIONS]- (e)
                MATCH (e) -[r]-> (related)
                RETURN e.id AS entity, type(r) AS relation, related.id AS target
                LIMIT 15
            """,
                params={"text": doc.page_content},
            )
            if entity_data:
                graph_lines = [
                    f"  {row['entity']} --[{row['relation']}]--> {row['target']}"
                    for row in entity_data
                ]
                contexts.append("関連グラフ情報:\n" + "\n".join(graph_lines))
    else:
        # ベクトルインデックスがない場合はフルテキスト検索にフォールバック
        result = graph.query(
            """
            MATCH (n) WHERE n.id CONTAINS $query OR n.text CONTAINS $query
            MATCH (n) -[r]-> (m)
            RETURN n.id AS entity, type(r) AS relation, m.id AS target
            LIMIT 20
        """,
            params={"query": query},
        )
        if result:
            lines = [
                f"- {r['entity']} --[{r['relation']}]--> {r['target']}" for r in result
            ]
            contexts.append("\n".join(lines))

    if not contexts:
        return "関連情報が見つかりませんでした。"

    return "\n\n---\n\n".join(contexts)


@tool
def get_entity_relations(entity_name: str) -> str:
    """
    特定のエンティティ（人物・組織・製品など）に関連する全関係を取得する。
    エンティティ名は英語・日本語どちらでも可。
    """
    result = graph.query(
        """
        MATCH (n {id: $name}) -[r]-> (m)
        RETURN n.id AS source, type(r) AS relation, m.id AS target
        UNION
        MATCH (n) -[r]-> (m {id: $name})
        RETURN n.id AS source, type(r) AS relation, m.id AS target
        LIMIT 30
    """,
        params={"name": entity_name},
    )

    if not result:
        return f"'{entity_name}' に関するエンティティが見つかりませんでした。"

    lines = [f"- {r['source']} --[{r['relation']}]--> {r['target']}" for r in result]
    return f"'{entity_name}' の関係:\n" + "\n".join(lines)


@tool
def run_cypher_query(cypher: str) -> str:
    """
    Cypherクエリを実行してNeo4jからデータを取得する。
    MATCH/RETURN のみの読み取りクエリを使うこと。CREATE/DELETE は使わない。
    """
    # 安全チェック: 書き込み操作をブロック
    upper = cypher.upper()
    if any(kw in upper for kw in ["CREATE", "DELETE", "MERGE", "SET", "REMOVE", "DROP"]):
        return "エラー: 書き込みクエリは実行できません。MATCH/RETURN のみ使ってください。"

    try:
        result = graph.query(cypher)
        if not result:
            return "クエリ結果が空でした。"
        return str(result[:20])  # 最大20件
    except Exception as e:
        return f"クエリエラー: {e}"


# ---- エージェント構築 ----


def create_graphrag_agent():
    """GraphRAGエージェントを作成する。"""
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

    tools = [search_knowledge_graph, get_entity_relations, run_cypher_query]

    # グラフスキーマをシステムプロンプトに含める（Cypherクエリ精度向上）
    graph.refresh_schema()
    schema_info = graph.schema or "スキーマ情報なし"

    system_prompt = f"""あなたはナレッジグラフを活用して質問に答えるAIアシスタントです。

Neo4jグラフデータベースのスキーマ:
{schema_info}

ツールの使い方:
- search_knowledge_graph: 自然言語でグラフを検索（最初に試す）
- get_entity_relations: 特定エンティティの関係を詳細取得
- run_cypher_query: 具体的なCypherクエリが必要な場合

グラフに情報がない場合は、その旨を正直に伝えてください。"""

    agent = create_react_agent(
        model=llm,
        tools=tools,
        prompt=system_prompt,
    )

    return agent


# ---- 実行 ----


def main():
    agent = create_graphrag_agent()

    print("GraphRAGエージェントが起動しました。'quit' で終了します。")
    print("-" * 50)

    config = {"configurable": {"thread_id": "graphrag-session-1"}}

    while True:
        user_input = input("You: ").strip()
        if not user_input or user_input.lower() in ("quit", "exit", "終了"):
            print("終了します。")
            break

        print("Agent: ", end="", flush=True)
        for chunk in agent.stream(
            {"messages": [HumanMessage(content=user_input)]},
            config=config,
            stream_mode="messages",
        ):
            msg, metadata = chunk
            if msg.content and metadata.get("langgraph_node") == "agent":
                print(msg.content, end="", flush=True)
        print("\n")


if __name__ == "__main__":
    main()
