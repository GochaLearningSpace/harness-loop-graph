"""デモ共通ユーティリティ: 色付き出力とテンポ調整（外部ライブラリ不要）。"""
import os
import sys
import time

# Windows ターミナルでも ANSI カラー / UTF-8 を有効化
if os.name == "nt":
    os.system("")  # 定数の空コマンド。Windows コンソールの VT 処理を有効化する定番手法（入力は渡さない）
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

FAST = "--fast" in sys.argv or os.environ.get("DEMO_FAST") == "1"

C = {
    "reset": "\033[0m", "bold": "\033[1m", "dim": "\033[2m",
    "red": "\033[31m", "green": "\033[32m", "yellow": "\033[33m",
    "blue": "\033[34m", "magenta": "\033[35m", "cyan": "\033[36m",
}


def pause(sec: float = 0.6) -> None:
    if not FAST:
        time.sleep(sec)


def say(msg: str, color: str = "reset", wait: float = 0.6) -> None:
    print(f"{C[color]}{msg}{C['reset']}", flush=True)
    pause(wait)


def title(msg: str) -> None:
    line = "=" * 64
    say(f"\n{line}\n {msg}\n{line}", "bold", 0.8)
