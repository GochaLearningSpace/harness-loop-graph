"""
Loop Engineering デモ（約1分）

エージェントループ  Observe → Think → Act → Verify  を回してバグを直す。
ポイント:
  - 検証（テスト）の結果をフィードバックとして次の反復に渡す
  - 停止条件: 成功 / 最大反復回数 / 進捗なし
  - 一発回答 (single-shot) との比較

モデルは台本どおりに修正案を出す FakeCoder（API キー不要）。
実行: python demos/loop_demo.py  [--fast]
"""
from _common import say, title, pause

BUGGY = "def average(xs):\n    return sum(xs) / len(xs) + 1"

TESTS = [
    (([2, 4],), 3.0),
    (([5],), 5.0),
    (([],), 0.0),          # 空リストの扱い（見落としがち）
]


class FakeCoder:
    """フィードバックの内容に応じて修正案を出す台本モデル。"""
    def propose(self, code: str, feedback: str) -> str:
        if "+ 1" in code:
            return "def average(xs):\n    return sum(xs) / len(xs)"
        if "ZeroDivisionError" in feedback:
            return ("def average(xs):\n    if not xs:\n        return 0.0\n"
                    "    return sum(xs) / len(xs)")
        return code


def run_tests(code: str):
    """Verify: コードを実行してテスト。失敗内容のリストを返す。"""
    ns = {}
    exec(code, ns)
    fails = []
    for args, expected in TESTS:
        try:
            got = ns["average"](*args)
            if got != expected:
                fails.append(f"average{args} = {got}, expected {expected}")
        except Exception as e:
            fails.append(f"average{args} raised {type(e).__name__}")
    return fails


def show_code(code: str):
    for line in code.splitlines():
        say(f"    │ {line}", "dim", 0.15)


def single_shot():
    title("(A) 一発回答: 1回直して終わり（検証なし）")
    code = FakeCoder().propose(BUGGY, "")
    show_code(code)
    fails = run_tests(code)
    say(f"  あとでテストすると… ❌ {len(fails)} 件失敗: {fails}", "red", 1.0)


def agent_loop(max_iters: int = 5):
    title("(B) ループ: Observe → Think → Act → Verify を繰り返す")
    coder, code = FakeCoder(), BUGGY
    for i in range(1, max_iters + 1):
        say(f"\n── iteration {i}/{max_iters} ──", "magenta", 0.3)
        fails = run_tests(code)                                   # Observe / Verify
        say(f"  observe: テスト {len(TESTS) - len(fails)}/{len(TESTS)} 合格", "cyan")
        if not fails:                                             # 停止条件①: 成功
            say("  stop   : ✅ 全テスト合格 → ループ終了", "green")
            show_code(code)
            return
        feedback = "; ".join(fails)
        say(f"  think  : 失敗 → {feedback}", "yellow")
        new_code = coder.propose(code, feedback)                  # Act
        if new_code == code:                                      # 停止条件③: 停滞
            say("  stop   : ⛔ 修正案が変わらない（進捗なし）→ 人間に相談", "red")
            return
        code = new_code
        say("  act    : 修正案を適用", "blue", 0.3)
        show_code(code)
    say("  stop   : ⛔ 最大反復回数に到達", "red")                 # 停止条件②: 予算


if __name__ == "__main__":
    single_shot()
    pause(0.8)
    agent_loop()
    say("\n💡 品質を決めるのはモデルの賢さだけでなく『ループの設計』"
        "（検証・フィードバック・停止条件）。", "bold")
