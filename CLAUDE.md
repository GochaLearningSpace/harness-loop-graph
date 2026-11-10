# CLAUDE.md

このリポジトリは **Harness / Loop / Graph Engineering** を各1分程度のデモで学ぶ教材です。
利用者は「ハーネスのデモを見せて」「LangGraph 版を動かして」のように自然言語で頼みます。
該当するデモを実行し、結果の要点を日本語で説明してください。

## 基本方針
- 回答は日本語。専門用語には短い説明を添える（利用者は AI エージェント開発の初学者を想定）
- デモは API キー不要。モデルは台本どおりに答える Fake モデルなので、毎回同じ結果になる
- Claude Code から実行するときは **必ず `--fast`** を付ける（待ち時間は人が見る発表用で、ここでは不要）
- ツールの出力は利用者に見えにくいので、実行後に**出力の要点を引用して**説明する
  （各デモの最後の `💡` 行が結論。関連する docs の「話すポイント」も参考にする）
- 利用者が自分のターミナルで発表用テンポのまま見たい場合は、`--fast` なしのコマンドを案内する
- デモのコードを変更する依頼でなければ、ファイルは編集しない

## デモ一覧（自然言語 → 実行するコマンド）

| 依頼の例 | コマンド | 依存 | 解説ドキュメント |
|---|---|---|---|
| ハーネス / Harness / ガードレール / 権限チェック | `python demos/harness_demo.py --fast` | なし | docs/01_harness_engineering.md |
| ループ / Loop / 自己修正 / 停止条件 | `python demos/loop_demo.py --fast` | なし | docs/02_loop_engineering.md |
| グラフ / Graph（自作エンジン版） | `python demos/graph_demo.py --fast` | なし | docs/03_graph_engineering.md |
| 全部 / 3つ続けて | `python demos/run_all.py --fast` | なし | README.md |
| ループと LangGraph の違い / 比較 | `<venv-python> demos/loop_vs_langgraph_demo.py --fast` | LangGraph | docs/02_loop_engineering.md |
| LangGraph 版 / LangChain 版 / グラフの見える化 | `<venv-python> demos/langgraph_demo.py --fast --open` | LangGraph | docs/03_graph_engineering.md |
| Dify / Copilot Studio / n8n との関係 | 実行なし。docs/04_graph_tools.md を要約 | — | docs/04_graph_tools.md |

- `python` が見つからない環境（macOS/Linux）では `python3` を使う
- `langgraph_demo.py` は `output/langgraph_flow.html` を生成し、`--open` でブラウザに表示する（通った経路が黄色）

## LangGraph 系デモのセットアップ
LangGraph 系デモを頼まれたら、まず `.venv` があるか確認し、なければ作る。

```bash
python -m venv .venv                                   # macOS/Linux: python3 -m venv .venv
<venv-python> -m pip install -r requirements-langgraph.txt
```

`<venv-python>` は OS で異なる:
- Windows: `.venv/Scripts/python`
- macOS / Linux: `.venv/bin/python`

LangGraph 系は Python 3.10 以上が必要。`python --version` が 3.9 以下なら、その旨を伝える。

## n8n（GUI 版）について
`gui/n8n/support_flow.json` は n8n にインポートして使う。n8n の起動は利用者自身の作業で、
インストールに時間がかかる（Node.js 24 系が必要、26 は不可）。自動で起動しようとせず、
docs/04_graph_tools.md の手順を案内する。

## ファイル構成
- `demos/` … デモ本体（`_common.py` は色付き出力と `--fast` 処理）
- `docs/` … 各テーマの説明、話すポイント（台本）、コードの見どころ
- `gui/n8n/` … n8n 用ワークフロー
- `requirements-langgraph.txt` … LangGraph 系デモの依存（バージョン固定）
