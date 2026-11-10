---
name: demo
description: Harness / Loop / Graph Engineering の教材デモを実行して解説する。「デモ見せて」「ハーネスのデモ」「LangGraph 版動かして」「全部見せて」などの依頼や /demo で使う。
argument-hint: "[harness | loop | graph | all | loop-vs-langgraph | langgraph]"
---

# デモ実行

引数（または依頼文）からデモを選び、CLAUDE.md の「デモ一覧」のコマンドを `--fast` 付きで実行する。

| 引数 | デモ |
|---|---|
| `harness` | `demos/harness_demo.py` |
| `loop` | `demos/loop_demo.py` |
| `graph` | `demos/graph_demo.py` |
| `all` または引数なし | `demos/run_all.py` |
| `loop-vs-langgraph` | `demos/loop_vs_langgraph_demo.py`（LangGraph 必要） |
| `langgraph` | `demos/langgraph_demo.py --open`（LangGraph 必要） |

## 手順
1. 引数がなく依頼文からも決められないときは、上の一覧を示して選んでもらう
2. LangGraph が必要なデモなら、CLAUDE.md の手順で `.venv` を確認・作成し、依存をインストールする
3. デモを `--fast` 付きで実行する
4. 次の形で日本語で説明する
   - **何を見せるデモか**（1文）
   - **出力の要点**（重要な行を数行だけ引用。`✋` `✅` `⛔` などの行と最後の `💡` 行）
   - **ここが大事**（対応する docs の「話すポイント」から2〜3点）
   - **自分のターミナルで発表用テンポで見るには**: `--fast` なしのコマンド
5. 次に見ると良いデモを1つ提案する（harness → loop → graph → loop-vs-langgraph → langgraph の順）
