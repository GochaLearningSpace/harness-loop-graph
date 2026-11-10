"""
Harness Engineering デモ（約1分）

同じ「モデル」を
  (A) ハーネスなし … モデルの出力をそのまま実行
  (B) ハーネスあり … ツール定義 / 出力検証 / 権限チェック / リトライ / ログ
で動かし、結果の違いを見せる。

モデルは再現性のため台本どおりに答える FakeModel（API キー不要）。
実行: python demos/harness_demo.py  [--fast]
"""
import json
from _common import say, title, pause

# ---------------------------------------------------------------
# 1. モデル（中身は差し替え可能な "黒箱"）
# ---------------------------------------------------------------
class FakeModel:
    """よくある失敗を含んだ台本どおりの応答を返す。"""
    def __init__(self):
        self.script = [
            # 1回目: JSON が壊れている（説明文が混ざる）
            'はい！実行します → {"tool": "delete_files", "args": {"path": "/"}}',
            # 2回目: JSON は正しいが危険なツールを要求
            '{"tool": "delete_files", "args": {"path": "/"}}',
            # 3回目: フィードバックを受けて安全な操作に修正
            '{"tool": "list_files", "args": {"path": "./tmp"}}',
        ]
        self.i = 0

    def generate(self, prompt: str) -> str:
        out = self.script[min(self.i, len(self.script) - 1)]
        self.i += 1
        return out


# ---------------------------------------------------------------
# 2. ツール（副作用はシミュレーションのみ。実ファイルには触れない）
# ---------------------------------------------------------------
def list_files(path):
    return ["cache_01.tmp", "cache_02.tmp", "old.log"]


def delete_files(path):
    return f"💥 {path} 以下をすべて削除しました（※シミュレーション）"


TOOLS = {
    "list_files":   {"fn": list_files,   "risk": "read",  "args": ["path"]},
    "delete_files": {"fn": delete_files, "risk": "write", "args": ["path"]},
}

TASK = "tmp フォルダの中身を確認して"


# ---------------------------------------------------------------
# (A) ハーネスなし
# ---------------------------------------------------------------
def run_without_harness():
    title("(A) ハーネスなし: モデルの出力を信じてそのまま実行")
    model = FakeModel()
    model.i = 1  # 「JSON は正しいが危険」な応答から
    raw = model.generate(TASK)
    say(f"model > {raw}", "dim")
    call = json.loads(raw)
    result = TOOLS[call["tool"]]["fn"](**call["args"])
    say(f"result > {result}", "red", 1.0)


# ---------------------------------------------------------------
# (B) ハーネスあり
# ---------------------------------------------------------------
ALLOWED_RISK = {"read"}   # 権限ポリシー: 読み取りのみ許可
MAX_RETRIES = 3


def validate(raw: str):
    """出力検証: JSON / スキーマ / 権限 をチェックし (call, error) を返す。"""
    try:
        call = json.loads(raw)
    except json.JSONDecodeError:
        return None, "出力が JSON ではありません。JSON のみを返してください。"
    if call.get("tool") not in TOOLS:
        return None, f"未知のツール: {call.get('tool')}"
    spec = TOOLS[call["tool"]]
    if set(call.get("args", {})) != set(spec["args"]):
        return None, f"引数が不正です。必要: {spec['args']}"
    if spec["risk"] not in ALLOWED_RISK:
        return None, f"権限エラー: '{call['tool']}' ({spec['risk']}) は許可されていません。"
    return call, None


def run_with_harness():
    title("(B) ハーネスあり: 検証 → 権限 → リトライ → ログ")
    model = FakeModel()
    # コンテキスト設計: ツール一覧と出力形式をプロンプトに明示
    prompt = (f"タスク: {TASK}\n利用可能なツール: {list(TOOLS)}\n"
              'JSON {"tool": ..., "args": {...}} のみで答えること')
    for attempt in range(1, MAX_RETRIES + 1):
        raw = model.generate(prompt)
        say(f"[try {attempt}] model > {raw}", "dim")
        call, err = validate(raw)
        if err:
            say(f"  harness ✋ {err}", "yellow")
            prompt += f"\n前回のエラー: {err}"   # エラーを文脈に追加して再試行
            continue
        result = TOOLS[call["tool"]]["fn"](**call["args"])
        say(f"  harness ✅ 実行: {call['tool']}({call['args']})", "green")
        say(f"  result > {result}", "green")
        say(f"  log    > {{'attempts': {attempt}, 'tool': '{call['tool']}', 'ok': True}}", "cyan", 1.0)
        return
    say("  harness ⛔ リトライ上限。人間にエスカレーション", "red")


if __name__ == "__main__":
    run_without_harness()
    pause(0.8)
    run_with_harness()
    say("\n💡 モデルは同じ。違いは『周りの仕組み（ハーネス）』だけ。", "bold")
