"""
Graph Engineering デモ ― LangGraph + LangChain 版（約1分）

graph_demo.py（自作ミニエンジン）と同じ問い合わせ対応フローを、
LangGraph の StateGraph と LangChain の LCEL チェーンで実装し、見える化する。

  - LangChain : ChatPromptTemplate | ChatModel | OutputParser のチェーン（LCEL）を各ノードで使用
  - LangGraph : StateGraph / 条件付きエッジ / 差し戻しサイクル / stream によるトレース
  - 見える化   : ターミナルに ASCII 図、Mermaid 定義、通過経路をハイライトした HTML を出力

モデルは LangChain の FakeListChatModel（API キー不要・毎回同じ結果）。
実モデルにする場合は FakeListChatModel を ChatAnthropic などに差し替えるだけ。

準備: pip install -r requirements-langgraph.txt
実行: python demos/langgraph_demo.py [--fast] [--open] [--png]
  --open : 生成した HTML をブラウザで開く
  --png  : PNG も出力（mermaid.ink の外部 API にグラフ定義を送信するので注意）
"""
import html
import os
import sys
import webbrowser
from typing import TypedDict

from langchain_core.language_models.fake_chat_models import FakeListChatModel
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import END, START, StateGraph

from _common import say, title, pause

OUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "output")


# ---------------------------------------------------------------
# 1. 共有状態（State）
# ---------------------------------------------------------------
class SupportState(TypedDict, total=False):
    query: str
    kind: str
    order: dict
    answer: str
    revisions: int
    approved: bool


# ---------------------------------------------------------------
# 2. LangChain のチェーン（LCEL: prompt | model | parser）
#    FakeListChatModel は responses を順番に返すだけの「台本モデル」
# ---------------------------------------------------------------
classify_chain = (
    ChatPromptTemplate.from_messages([
        ("system", "問い合わせを faq か refund のどちらかに分類し、ラベルだけを返す。"),
        ("human", "{query}"),
    ])
    | FakeListChatModel(responses=["faq", "refund"])
    | StrOutputParser()
)

draft_chain = (
    ChatPromptTemplate.from_messages([
        ("system", "返金問い合わせへの回答を書く。注文情報: {order}。レビュー指摘: {feedback}"),
        ("human", "{query}"),
    ])
    | FakeListChatModel(responses=[
        "返金できます。",                                   # v1: 根拠なし → レビューで NG
        "注文#1234は購入5日以内のため返金可能です。",          # v2: 指摘を反映
    ])
    | StrOutputParser()
)


# ---------------------------------------------------------------
# 3. ノード（状態を受け取り、更新したいキーだけを返す）
# ---------------------------------------------------------------
def classify(s: SupportState):
    kind = classify_chain.invoke({"query": s["query"]}).strip()
    return {"kind": kind}


def faq_answer(s: SupportState):
    return {"answer": "営業時間は 9:00-18:00 です。"}


def lookup_order(s: SupportState):
    return {"order": {"id": 1234, "days": 5}}


def draft(s: SupportState):
    feedback = "" if s.get("revisions", 0) == 0 else "根拠となる注文番号を入れること"
    text = draft_chain.invoke({"query": s["query"], "order": s["order"], "feedback": feedback})
    return {"answer": text, "revisions": s.get("revisions", 0) + 1}


def review(s: SupportState):
    return {"approved": "注文#" in s["answer"]}


def send(s: SupportState):
    return {}


# ---------------------------------------------------------------
# 4. グラフ定義（LangGraph StateGraph）
# ---------------------------------------------------------------
def build_graph():
    g = StateGraph(SupportState)
    for name, fn in [("classify", classify), ("faq_answer", faq_answer),
                     ("lookup_order", lookup_order), ("draft", draft),
                     ("review", review), ("send", send)]:
        g.add_node(name, fn)

    g.add_edge(START, "classify")
    g.add_conditional_edges("classify", lambda s: s["kind"],
                            {"faq": "faq_answer", "refund": "lookup_order"})
    g.add_edge("faq_answer", "send")
    g.add_edge("lookup_order", "draft")
    g.add_edge("draft", "review")
    g.add_conditional_edges(
        "review",
        lambda s: "approve" if s["approved"] or s["revisions"] >= 3 else "revise",
        {"approve": "send", "revise": "draft"},
    )
    g.add_edge("send", END)
    return g.compile()


# ---------------------------------------------------------------
# 5. 見える化
# ---------------------------------------------------------------
def highlight(mermaid: str, path: list[str]) -> str:
    """Mermaid 定義に、実際に通ったノードの色付けを追記する。"""
    visited = ",".join(dict.fromkeys(path))
    return (mermaid.rstrip()
            + "\n\tclassDef visited fill:#fde68a,stroke:#b45309,stroke-width:3px,color:#000;"
            + f"\n\tclass {visited} visited;\n")


def write_html(base: str, runs: list[tuple[str, list[str], str]]) -> str:
    os.makedirs(OUT_DIR, exist_ok=True)
    cards = [f"<section><h2>グラフ定義</h2><pre class='mermaid'>{html.escape(base)}</pre></section>"]
    for query, path, answer in runs:
        cards.append(
            "<section>"
            f"<h2>入力: 「{html.escape(query)}」</h2>"
            f"<p class='path'>経路: {' → '.join(html.escape(p) for p in path)}</p>"
            f"<p>回答: {html.escape(answer)}</p>"
            f"<pre class='mermaid'>{html.escape(highlight(base, path))}</pre>"
            "</section>"
        )
    page = f"""<!doctype html>
<html lang="ja"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>LangGraph 実行の見える化</title>
<style>
  body {{ font-family: system-ui, sans-serif; margin: 0 auto; max-width: 1100px; padding: 16px; background: #f8fafc; color: #0f172a; }}
  .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 16px; }}
  section {{ background: #fff; border: 1px solid #e2e8f0; border-radius: 12px; padding: 16px; }}
  h1 {{ font-size: 1.4rem; }} h2 {{ font-size: 1rem; margin-top: 0; }}
  .path {{ font-family: ui-monospace, monospace; font-size: .85rem; color: #b45309; }}
  pre.mermaid {{ background: none; text-align: center; }}
</style></head>
<body>
<h1>LangGraph 問い合わせ対応フロー（黄色 = 実際に通ったノード）</h1>
<div class="grid">{''.join(cards)}</div>
<script type="module">
  import mermaid from "https://cdn.jsdelivr.net/npm/mermaid@11.4.1/dist/mermaid.esm.min.mjs";
  // 複数図を同時描画すると ID/スタイルが衝突するため、1枚ずつ順番に描画する
  mermaid.initialize({{ startOnLoad: false, theme: "default" }});
  const blocks = [...document.querySelectorAll("pre.mermaid")];
  for (let i = 0; i < blocks.length; i++) {{
    const {{ svg }} = await mermaid.render(`graph${{i}}`, blocks[i].textContent);
    blocks[i].innerHTML = svg;
  }}
</script>
</body></html>"""
    path = os.path.join(OUT_DIR, "langgraph_flow.html")
    with open(path, "w", encoding="utf-8") as f:
        f.write(page)
    return path


# ---------------------------------------------------------------
# 6. 実行
# ---------------------------------------------------------------
def main():
    app = build_graph()
    drawable = app.get_graph()

    title("LangGraph のグラフ（ASCII 表示: get_graph().draw_ascii()）")
    try:
        say(drawable.draw_ascii(), "blue", 1.0)
    except ImportError:
        say("（grandalf 未インストールのため ASCII 図は省略）", "dim")

    base = drawable.draw_mermaid()
    runs = []
    for q in ["営業時間を教えて", "先週買った商品を返金したい"]:
        title(f"入力: 「{q}」  (app.stream でノードごとの更新を表示)")
        path, final = [], {}
        for step, update in enumerate(app.stream({"query": q}, stream_mode="updates"), 1):
            for node, diff in update.items():
                path.append(node)
                final.update(diff or {})
                say(f"  [{step}] ▶ {node:<13} {diff or {}}", "cyan", 0.3)
        say(f"  ✅ 回答: {final['answer']}", "green", 0.8)
        runs.append((q, path, final["answer"]))
        pause(0.4)

    html_path = write_html(base, runs)
    title("見える化ファイル")
    say(f"  HTML : {html_path}", "yellow")
    if "--png" in sys.argv:
        png = os.path.join(OUT_DIR, "langgraph_flow.png")
        with open(png, "wb") as f:
            f.write(drawable.draw_mermaid_png())   # mermaid.ink API を使用
        say(f"  PNG  : {png}", "yellow")
    if "--open" in sys.argv:
        webbrowser.open("file://" + html_path.replace("\\", "/"))

    say("\n💡 自作エンジンと同じフローを LangGraph で。図・トレース・差し替えが標準機能で手に入る。",
        "bold")


if __name__ == "__main__":
    main()
