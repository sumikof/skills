# GraphRAG 実装パターン

Neo4jグラフデータベースを使ったRAG（検索拡張生成）の実装パターン。

## パターン1: ベクトル検索 + グラフ検索のハイブリッド

最も推奨されるアプローチ。ベクトル類似検索でドキュメントを見つけ、グラフ関係で追加コンテキストを取得する。

```python
from langchain_neo4j import Neo4jGraph, Neo4jVector
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

graph = Neo4jGraph()
embeddings = OpenAIEmbeddings()

# ベクトルインデックスに接続
vector_retriever = Neo4jVector.from_existing_index(
    embedding=embeddings,
    index_name="vector",           # Neo4jVector.from_existing_graph で作成したインデックス名
    node_label="Document",
    text_node_property="text",
    embedding_node_property="embedding",
).as_retriever(search_kwargs={"k": 3})

def retrieve_with_graph(query: str) -> str:
    """ベクトル検索 + グラフトラバーサルでコンテキストを取得。"""
    # ステップ1: ベクトル検索で関連ドキュメントを取得
    docs = vector_retriever.invoke(query)

    # ステップ2: 取得したドキュメントに関連するエンティティをグラフから取得
    contexts = []
    for doc in docs:
        contexts.append(doc.page_content)

        # ドキュメントに含まれるエンティティの関係を追加取得
        entity_data = graph.query("""
            MATCH (d:Document {text: $text}) <-[:MENTIONS]- (e)
            MATCH (e) -[r]-> (related)
            RETURN e.id AS entity, type(r) AS relation, related.id AS related
            LIMIT 20
        """, params={"text": doc.page_content})

        if entity_data:
            graph_context = "\n".join(
                f"- {row['entity']} --[{row['relation']}]--> {row['related']}"
                for row in entity_data
            )
            contexts.append(f"関連グラフ情報:\n{graph_context}")

    return "\n\n".join(contexts)
```

## パターン2: Cypherクエリ自動生成

自然言語からCypherクエリを自動生成してNeo4jを直接クエリする。

```python
from langchain_neo4j import GraphCypherQAChain
from langchain_openai import ChatOpenAI

graph = Neo4jGraph()
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

# スキーマをLLMに渡してCypherクエリを自動生成
chain = GraphCypherQAChain.from_llm(
    llm=llm,
    graph=graph,
    verbose=True,       # 生成されたCypherクエリを表示
    return_intermediate_steps=True,  # Cypherと結果を返す
)

result = chain.invoke({"query": "AppleのCEOは誰ですか？"})
print(result["result"])
```

カスタムプロンプトで精度向上:

```python
from langchain_core.prompts import PromptTemplate

CYPHER_GENERATION_TEMPLATE = """
あなたはNeo4jのCypherクエリ生成の専門家です。
以下のグラフスキーマに基づいてCypherクエリを生成してください。

スキーマ:
{schema}

重要なルール:
- LIMIT 25 を必ず付ける
- 存在するノードラベルとプロパティのみ使う
- 関係の向きに注意する

質問: {question}

Cypherクエリ:
"""

cypher_prompt = PromptTemplate(
    input_variables=["schema", "question"],
    template=CYPHER_GENERATION_TEMPLATE,
)

chain = GraphCypherQAChain.from_llm(
    llm=llm,
    graph=graph,
    cypher_prompt=cypher_prompt,
)
```

## パターン3: LangGraphエージェントとの統合

### シンプルなGraphRAGノード

```python
from langgraph.graph import StateGraph, MessagesState, START, END
from langchain_core.messages import HumanMessage, AIMessage

def retrieve_graph_context(state: MessagesState) -> dict:
    """Neo4jからコンテキストを取得するノード。"""
    query = state["messages"][-1].content
    context = retrieve_with_graph(query)  # 上記のretrieve_with_graph関数
    return {"messages": [AIMessage(content=f"[グラフコンテキスト]\n{context}")]}

def generate_answer(state: MessagesState) -> dict:
    """LLMで回答を生成するノード。"""
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    response = llm.invoke(state["messages"])
    return {"messages": [response]}

graph_builder = StateGraph(MessagesState)
graph_builder.add_node("retrieve", retrieve_graph_context)
graph_builder.add_node("generate", generate_answer)
graph_builder.add_edge(START, "retrieve")
graph_builder.add_edge("retrieve", "generate")
graph_builder.add_edge("generate", END)

app = graph_builder.compile()
```

### ツールとして定義する方法

```python
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent

@tool
def search_knowledge_graph(query: str) -> str:
    """ナレッジグラフからクエリに関連する情報を検索する。"""
    result = graph.query("""
        CALL db.index.fulltext.queryNodes('entity_fulltext', $query)
        YIELD node, score
        MATCH (node) -[r]-> (related)
        RETURN node.id AS entity, type(r) AS relation, related.id AS target, score
        ORDER BY score DESC LIMIT 10
    """, params={"query": query})

    if not result:
        return "関連情報が見つかりませんでした。"

    lines = [f"- {r['entity']} --[{r['relation']}]--> {r['target']}" for r in result]
    return "\n".join(lines)

@tool
def query_neo4j(cypher: str) -> str:
    """Cypherクエリを実行してNeo4jからデータを取得する。READ ONLYクエリのみ使うこと。"""
    try:
        result = graph.query(cypher)
        return str(result[:20])  # 最大20件
    except Exception as e:
        return f"クエリエラー: {e}"

# ReActエージェントにツールとして渡す
agent = create_react_agent(
    model="openai:gpt-4o-mini",
    tools=[search_knowledge_graph, query_neo4j],
    prompt="あなたはナレッジグラフを活用して質問に答えるAIです。",
)
```

## Neo4jVector の各種検索タイプ

```python
# ベクトル類似検索のみ
vector_index = Neo4jVector.from_existing_graph(
    embedding=OpenAIEmbeddings(),
    search_type="vector",
    node_label="Document",
    text_node_properties=["text"],
    embedding_node_property="embedding",
)

# ベクトル + キーワードのハイブリッド検索（精度向上）
hybrid_index = Neo4jVector.from_existing_graph(
    embedding=OpenAIEmbeddings(),
    search_type="hybrid",
    node_label="Document",
    text_node_properties=["text"],
    embedding_node_property="embedding",
)

retriever = hybrid_index.as_retriever(search_kwargs={"k": 5})
docs = retriever.invoke("AppleのiPhoneについて教えて")
```

## よくある問題

| 問題 | 対処 |
|---|---|
| Cypherクエリが間違っている | スキーマを正確に渡す・プロンプトにルールを追加 |
| ベクトル検索の精度が低い | embedding モデルを変更・チャンクサイズを調整 |
| グラフ検索で関係が取れない | エンティティ抽出時の `include_source=True` を確認 |
| クエリが遅い | Cypherにインデックス（`CREATE INDEX`）を追加 |
