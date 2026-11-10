# Harness / Loop / Graph Engineering 入門

AI エージェント開発で重要な3つの設計観点を、**各1分程度のデモ**で体験する教材です。

| # | テーマ | ひとことで | デモ |
|---|---|---|---|
| 1 | [Harness Engineering](docs/01_harness_engineering.md) | モデルの**周りの仕組み**（検証・権限・リトライ・ログ）を設計する | `demos/harness_demo.py` |
| 2 | [Loop Engineering](docs/02_loop_engineering.md) | **試す→検証→直す** の反復と停止条件を設計する | `demos/loop_demo.py` |
| 3 | [Graph Engineering](docs/03_graph_engineering.md) | 処理フローを**ノード・エッジ・状態**のグラフで設計する | `demos/graph_demo.py` |

```
 Graph（構造）   ┌─ classify ─▶ draft ─▶ review ─┐
                 │                 ▲        │    │
 Loop（反復）    │                 └─revise─┘    ▼
                 │                              send
 Harness（器）   └ 各ノードのモデル呼び出しを 検証・権限・リトライ で包む
```

## 動かし方

必要なもの: **Python 3.9+ のみ**（外部ライブラリ・API キー不要）

```bash
# 個別に実行（発表用のテンポで表示）
python demos/harness_demo.py
python demos/loop_demo.py
python demos/graph_demo.py

# 3つ続けて実行（Enter で次へ）
python demos/run_all.py

# 待ち時間なしで一気に表示
python demos/run_all.py --fast
```

> デモの「モデル」は、再現性のため台本どおりに応答する Fake モデルです。
> 毎回同じ結果になるので、説明会・研修でも安心して使えます。
> 本物の LLM（Claude API など）に差し替えても、ハーネス・ループ・グラフの構造はそのまま使えます。

## 進め方の例（約10分）

| 時間 | 内容 |
|---|---|
| 0:00 | 導入: 「エージェントの性能 = モデル × 周りの設計」 |
| 1:00 | Harness: 説明（1分）→ デモ（1分） |
| 3:00 | Loop: 説明（1分）→ デモ（1分） |
| 5:00 | Graph: 説明（1分）→ デモ（1分） |
| 7:00 | まとめ: 3つの関係（Graph の中に Loop、各ノードに Harness） |
| 8:00 | 質疑 |

各ドキュメントに **「話すポイント（台本）」** と **「コードの見どころ」** を載せています。

## ファイル構成

```
.
├── README.md
├── docs/
│   ├── 01_harness_engineering.md
│   ├── 02_loop_engineering.md
│   └── 03_graph_engineering.md
└── demos/
    ├── _common.py         # 色付き出力・テンポ調整
    ├── harness_demo.py
    ├── loop_demo.py
    ├── graph_demo.py
    └── run_all.py
```

## ハンズオン課題（任意）
1. **Harness**: `ALLOWED_RISK = {"read", "write"}` に変えて実行し、何が起きるか確認する
2. **Loop**: `TESTS` に `(([1, 2],), 1.5)` を追加しても通るか、`max_iters=1` にするとどうなるか確認する
3. **Graph**: 「解約」の問い合わせを扱う `cancel` ルートを追加し、Mermaid 図に反映されることを確認する
