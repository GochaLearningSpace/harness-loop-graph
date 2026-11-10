"""
Loop Engineering と LangGraph の違いが分かる一番簡単なデモ（約1分）

loop_demo.py と同じ「バグ修正ループ」を2通りで書いて比べる。
  (A) 普通の while ループ   … ループの中身はコードの中に埋もれている
  (B) LangGraph のグラフ    … 同じループを「test → fix → test …」のサイクルとして定義

ポイント: Loop Engineering は「何を繰り返し、いつ止めるか」という設計の考え方。
          LangGraph はそのループを「グラフのサイクル」として書く道具。対立するものではない。
          グラフにすると「図にできる」「各ステップの状態が自動で保存される」「途中から再開できる」。

準備: pip install -r requirements-langgraph.txt
実行: python demos/loop_vs_langgraph_demo.py  [--fast]
"""
from typing import TypedDict

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph

from _common import say, title, pause
from loop_demo import BUGGY, TESTS, FakeCoder, run_tests

MAX_ITERS = 5
coder = FakeCoder()


# ---------------------------------------------------------------
# (A) 普通の while ループ
# ---------------------------------------------------------------
def plain_loop():
    title("(A) 普通の while ループ")
    code, i = BUGGY, 0
    while True:
        i += 1
        fails = run_tests(code)
        say(f"  iteration {i}: テスト {len(TESTS) - len(fails)}/{len(TESTS)} 合格", "cyan", 0.3)
        if not fails or i >= MAX_ITERS:
            break
        code = coder.propose(code, "; ".join(fails))
    say("  ✅ 完了。ただし…", "green", 0.4)
    say("     ・流れはコードを読まないと分からない", "yellow", 0.3)
    say("     ・途中の状態（各回のコード）は残っていない", "yellow", 0.3)
    say("     ・途中で止まったら最初からやり直し", "yellow", 0.8)


# ---------------------------------------------------------------
# (B) 同じループを LangGraph で
# ---------------------------------------------------------------
class State(TypedDict):
    code: str
    fails: list
    iteration: int


def test(s: State):                       # ノード1: 検証
    return {"fails": run_tests(s["code"]), "iteration": s["iteration"] + 1}


def fix(s: State):                        # ノード2: 修正
    return {"code": coder.propose(s["code"], "; ".join(s["fails"]))}


def escalate(s: State):                   # ノード3: 上限に達したら人間に相談
    say("    ⛔ 最大反復回数に到達 → 人間に相談", "red", 0.3)
    return {}


def should_continue(s: State):            # 停止条件 = 条件付きエッジ
    if not s["fails"]:
        return "pass"
    if s["iteration"] >= MAX_ITERS:
        return "give_up"
    return "retry"


def describe(code: str) -> str:
    """履歴表示用: コードがどの段階かを短く表す。"""
    if "+ 1" in code:
        return "バグあり（+1）"
    if "if not xs" in code:
        return "空リスト対応済み"
    return "+1 は修正、空リスト未対応"


def build():
    g = StateGraph(State)
    g.add_node("test", test)
    g.add_node("fix", fix)
    g.add_node("escalate", escalate)
    g.add_edge(START, "test")
    g.add_conditional_edges("test", should_continue,
                            {"retry": "fix", "pass": END, "give_up": "escalate"})
    g.add_edge("fix", "test")             # ← これがループ（サイクル）
    g.add_edge("escalate", END)
    return g.compile(checkpointer=MemorySaver())   # 各ステップの状態を自動保存


def langgraph_loop():
    title("(B) 同じループを LangGraph で（test ⇄ fix のサイクル）")
    app = build()

    say("  メリット1: ループの構造がそのまま図になる（get_graph() から自動生成）", "bold", 0.4)
    for e in app.get_graph().edges:
        arrow = f"--{e.data}-->" if e.conditional else "------->"
        say(f"    {e.source:>9} {arrow:<12} {e.target}", "blue", 0.2)
    say("    （fix → test の線がループ。draw_mermaid() で Mermaid 図にもできる）", "dim", 0.8)

    config = {"configurable": {"thread_id": "demo-1"}}
    say("\n  実行（stream でノードごとに表示）", "bold", 0.3)
    for update in app.stream({"code": BUGGY, "fails": [], "iteration": 0}, config,
                             stream_mode="updates"):
        for node, diff in update.items():
            if node == "test":
                n = len(TESTS) - len(diff["fails"])
                say(f"    ▶ test  : iteration {diff['iteration']} → {n}/{len(TESTS)} 合格", "cyan", 0.3)
            else:
                say("    ▶ fix   : 修正案を適用", "magenta", 0.3)

    say("\n  メリット2: 各ステップの状態が自動で保存され、後から見返せる", "bold", 0.4)
    history = list(app.get_state_history(config))[::-1]   # 古い順
    for snap in history:
        if not snap.values:
            continue
        nxt = snap.next[0] if snap.next else "END"
        say(f"    step {snap.metadata['step']:>2} | 次: {nxt:<6} | iteration={snap.values['iteration']} | "
            f"コード: {describe(snap.values['code'])}", "dim", 0.2)

    say("\n  メリット3: 保存された途中の状態から再開できる（タイムトラベル）", "bold", 0.4)
    mid = next(s for s in history if s.next == ("fix",) and s.values["iteration"] == 2)
    say(f"    iteration 2 の fix 直前（step {mid.metadata['step']}）から再実行 →", "dim", 0.3)
    for update in app.stream(None, mid.config, stream_mode="updates"):
        for node in update:
            say(f"    ▶ {node}", "cyan", 0.3)
    say("    ✅ 最初からやり直さずに、途中から続きを実行できた", "green", 0.8)


if __name__ == "__main__":
    plain_loop()
    pause(0.6)
    langgraph_loop()
    say("\n💡 Loop Engineering = 何を繰り返し、いつ止めるかの『設計』。"
        "\n   LangGraph = そのループをグラフで書き、図・履歴・再開を手に入れる『道具』。", "bold")
