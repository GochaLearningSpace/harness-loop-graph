"""
Graph Engineering デモ（約1分）

問い合わせ対応ワークフローを「ノード + エッジ + 共有状態」のグラフとして定義し実行する。
  - 条件分岐エッジ（ルーター）
  - 差し戻しループ（レビュー NG → 下書きへ戻る）
  - 実行トレースと Mermaid 図の出力

外部ライブラリ不要の最小グラフエンジン（LangGraph などの考え方を再現）。
実行: python demos/graph_demo.py  [--fast]
"""
from _common import say, title, pause

END = "END"


class Graph:
    def __init__(self):
        self.nodes, self.edges, self.cond = {}, {}, {}

    def node(self, name):
        def deco(fn):
            self.nodes[name] = fn
            return fn
        return deco

    def edge(self, src, dst):
        self.edges[src] = dst

    def conditional(self, src, router, mapping):
        self.cond[src] = (router, mapping)

    def run(self, state, start, max_steps=20):
        cur, step = start, 0
        while cur != END:
            step += 1
            if step > max_steps:
                raise RuntimeError("max_steps 超過（無限ループ防止）")
            say(f"  [{step}] ▶ {cur}", "cyan", 0.2)
            state = {**state, **self.nodes[cur](state)}   # ノードは状態の差分を返す
            if cur in self.cond:
                router, mapping = self.cond[cur]
                key = router(state)
                nxt = mapping[key]
                say(f"       ↳ route '{key}' → {nxt}", "yellow", 0.3)
            else:
                nxt = self.edges[cur]
            cur = nxt
        return state

    def mermaid(self, start):
        lines = ["graph TD", f"  START((START)) --> {start}"]
        for s, d in self.edges.items():
            lines.append(f"  {s} --> {d}")
        for s, (_, m) in self.cond.items():
            for k, d in m.items():
                lines.append(f"  {s} -- {k} --> {d}")
        return "\n".join(lines)


# ---------------------------------------------------------------
# ワークフロー定義（ノード = 関数、エッジ = 遷移ルール）
# ---------------------------------------------------------------
g = Graph()


@g.node("classify")
def classify(s):
    kind = "refund" if "返金" in s["query"] else "faq"
    say(f"       分類: {kind}", "dim", 0.2)
    return {"kind": kind}


@g.node("faq_answer")
def faq_answer(s):
    return {"answer": "営業時間は 9:00-18:00 です。"}


@g.node("lookup_order")
def lookup_order(s):
    say("       注文DB参照: #1234 / 購入から5日", "dim", 0.2)
    return {"order": {"id": 1234, "days": 5}}


@g.node("draft")
def draft(s):
    n = s.get("revisions", 0) + 1
    text = ("返金できます。" if n == 1
            else f"注文#{s['order']['id']}は購入{s['order']['days']}日以内のため返金可能です。")
    say(f"       下書き v{n}: {text}", "dim", 0.2)
    return {"answer": text, "revisions": n}


@g.node("review")
def review(s):
    ok = "注文#" in s["answer"]
    say(f"       レビュー: {'OK' if ok else 'NG（根拠となる注文番号がない）'}", "dim", 0.2)
    return {"approved": ok}


@g.node("send")
def send(s):
    return {"sent": True}


g.conditional("classify", lambda s: s["kind"],
              {"faq": "faq_answer", "refund": "lookup_order"})
g.edge("faq_answer", "send")
g.edge("lookup_order", "draft")
g.edge("draft", "review")
g.conditional("review",
              lambda s: "approve" if s["approved"] or s["revisions"] >= 3 else "revise",
              {"approve": "send", "revise": "draft"})
g.edge("send", END)


if __name__ == "__main__":
    title("グラフ定義（Mermaid）")
    say(g.mermaid("classify"), "blue", 1.0)

    for q in ["営業時間を教えて", "先週買った商品を返金したい"]:
        title(f"入力: 「{q}」")
        final = g.run({"query": q}, start="classify")
        say(f"  ✅ 回答: {final['answer']}", "green", 0.8)
        pause(0.4)

    say("\n💡 処理を『ノード・エッジ・状態』で明示すると、分岐・差し戻し・可視化・"
        "テストが容易になる。", "bold")
