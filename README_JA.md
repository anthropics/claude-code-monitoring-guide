# Claude Code Monitoring Guide

Claude Code のテレメトリデータを収集・可視化し、コスト・効率・異常を監視するためのガイドです。

[English](README.md)

## アーキテクチャ

```
Claude Code
  │  (OTLP gRPC / localhost:4317)
  ▼
OpenTelemetry Collector
  ├─ metrics ──▶ Prometheus (:9090)
  ├─ logs    ──▶ Loki (:3100)
  └─ traces  ──▶ Tempo (:3200)
                    ▲
                Grafana (:3000) ─ 全データソースを横断可視化
                    │
                    └─ lifecycle ──▶ DuckDB API (:8082)

Claude Code Hooks (lifecycle-logger.sh)
  └─ events.jsonl ──▶ DuckDB API (:8082) ──▶ Grafana Infinity DS
```

Claude Code は `prompt.id`（UUID v4）をすべてのイベントに付与して送信します。この ID をキーに `user_prompt → api_request → tool_result` の処理フロー全体をトレースできます。

## 前提条件

- Docker / Docker Compose
- Claude Code がインストール済み

## セットアップ

### 1. 監視スタックの起動

```bash
git clone https://github.com/samuraikun/claude-code-monitoring-guide
cd claude-code-monitoring-guide
docker compose up -d
```

起動するサービス:

| サービス | ポート | 役割 |
|---|---|---|
| OpenTelemetry Collector | 4317 (gRPC), 4318 (HTTP) | テレメトリ受信・転送 |
| Prometheus | 9090 | メトリクス保存 |
| Loki | 3100 | ログ/イベント保存 |
| Tempo | 3200 | トレース保存 |
| Grafana | 3000 | 可視化 (admin/admin) |
| DuckDB API | 8082 | ライフサイクルイベント保存・クエリ (Go + DuckDB) |

### 2. Claude Code のテレメトリ設定

このリポジトリで `claude` を起動すると `.claude/settings.json` により自動でテレメトリが有効になります。

```json
{
  "env": {
    "CLAUDE_CODE_ENABLE_TELEMETRY": "1",
    "CLAUDE_CODE_ENHANCED_TELEMETRY_BETA": "1",
    "OTEL_METRICS_EXPORTER": "otlp",
    "OTEL_LOGS_EXPORTER": "otlp",
    "OTEL_EXPORTER_OTLP_PROTOCOL": "grpc",
    "OTEL_EXPORTER_OTLP_ENDPOINT": "http://localhost:4317",
    "OTEL_EXPORTER_OTLP_METRICS_TEMPORALITY_PREFERENCE": "cumulative"
  }
}
```

他のリポジトリで使う場合は `~/.claude/settings.json`（グローバル設定）に同じ内容を追記します。

### 3. 動作確認

```bash
# Claude Code を起動して何か作業する
claude

# Loki にデータが届いているか確認
curl -s http://localhost:3100/loki/api/v1/labels | jq .

# Grafana でログを確認: http://localhost:3000
# Explore → Loki → {service_name="claude-code"}
```

## Grafana ダッシュボード

Grafana 起動後、`http://localhost:3000` にアクセスすると **Claude Code** フォルダに以下のダッシュボードが自動プロビジョニングされています。

---

### Prompt Timeline

**UID**: `claude-code-prompt-timeline`

1つのプロンプト処理の全イベントを時系列で確認する、トレース相当のビューです。

**使い方**:
1. "Recent Prompts" パネルで調査したい `prompt_id` をコピー
2. 画面上部の "Prompt ID" 入力欄に貼り付け
3. `user_prompt → api_request → tool_result` の流れを確認

**パネル構成**:

| パネル | タイプ | 内容 |
|---|---|---|
| Recent Prompts | Logs | 直近のプロンプト一覧。prompt_id をここからコピー |
| Prompt Event Timeline | Logs | 選択した prompt_id の全イベントを時系列表示 |
| API Requests for Prompt | Table | モデル・コスト・トークン数・レイテンシ |
| Tool Executions for Prompt | Table | ツール名・成否・実行時間・結果サイズ |

---

### Session Timeline

**UID**: `claude-code-session-timeline`

特定セッションの全イベントを時系列で確認するドリルダウンビューです。

**使い方**:
1. "Recent Sessions" パネルで調査したい `session_id` をコピー
2. 画面上部の "Session ID" 入力欄に貼り付け
3. セッション内の全プロンプト・コスト・ツール利用状況を確認

**パネル構成**:

| パネル | タイプ | 内容 |
|---|---|---|
| Recent Sessions | Table | 直近のセッション一覧（プロンプト数・コスト付き） |
| Session Event Stream | Logs | 選択した session_id の全イベントを時系列表示 |
| Prompts in Session — Turn Count | Table | セッション内の各プロンプトのターン数 |
| Prompts in Session — Cost | Table | セッション内の各プロンプトのコスト |
| Tool Usage in Session | Bar chart | セッション内のツール利用分布 |
| Cache Performance in Session | Time series | セッション内のキャッシュ読み取り vs 作成トークン |

---

### Developer Efficiency

**UID**: `claude-code-dev-efficiency`

ツール使用パターン・コスト・キャッシュ効率・モデル性能を把握するダッシュボードです。

**パネル構成**:

| パネル | タイプ | 内容 |
|---|---|---|
| Tool Usage Distribution | Bar chart | ツール別の総実行回数。Bash 比率が高い場合はプロンプトの曖昧さを疑う |
| Bash vs Total Tool Executions | Time series | Bash と全ツール実行の比率推移 |
| Top 10 Sessions by Cost | Table | コスト上位セッション（USD） |
| Top 10 Prompts by Turn Count | Table | ターン数上位プロンプト。10回超はループや非効率の可能性 |
| Cache Performance | Time series | Cache Read（緑）と Cache Creation（橙）の比率。緑が多いほど効率的 |
| Prompt Activity Over Time | Time series | 時系列でのプロンプト数（使用頻度のパターン把握） |
| Token Usage by Model | Time series | モデル別のトークン使用量の時系列 |
| Code Edit Approvals by Language | Bar chart | 言語別のコード編集承認数 |
| Code Edit Decisions by Source | Bar chart | 編集判断ソース別内訳（config / user_permanent / user_reject） |
| Fast Mode Usage Rate | Stat | Fast Mode を使用した API リクエストの割合 |
| Model Cost Efficiency (Output Tokens / $) | Time series | モデル別の 1 ドルあたり出力トークン数。高いほど効率的 |
| Tool Success Rate Trend by Tool | Time series | ツール別の成功率の時系列推移 |

---

### Anomaly & Health

**UID**: `claude-code-anomaly-health`

異常検知と健全性監視のダッシュボードです。

**パネル構成**:

| パネル | タイプ | 内容 |
|---|---|---|
| Tool Failure Rate | Time series | ツール失敗数の推移。連続失敗は手動介入のサイン |
| API Request Duration (p50/p95) | Time series | p95 が 30 秒超は API 遅延またはスタックの疑い |
| Loop Detection — High Turn Count | Table | ターン数上位 20 プロンプト。10 回超は要確認 |
| Large Tool Results (> 100KB) | Logs | 意図しない大量データ読み出しの検知 |
| Tool Failure Count by Tool Name | Table | ツール別の失敗回数 |
| Max Tool Result Size by Tool | Table | ツール別の最大出力サイズ |
| API Errors by Status Code | Bar chart | HTTP ステータスコード別の API エラー数（429、500 等） |
| High Retry Prompts (Top 10) | Table | リトライが多発したプロンプト上位 10 件 |
| Tool Decision Rate (Accept vs Reject) | Time series | ツール実行の承認・拒否レートの時系列 |
| API Request Duration (p99/p95) | Time series | P99 レイテンシ。P95 との差が大きい場合は特定リクエストのボトルネック |
| Rate Limit & Server Error Frequency | Time series | 429（レート制限）・500（サーバーエラー）・529（過負荷）の推移 |
| Average Retry Attempts | Stat | API エラー時の平均リトライ回数。3 回以上はキャパシティ問題の可能性 |
| Tool Rejections by Source | Bar chart | ツール拒否のソース別内訳（config / user_reject 等） |

---

### Working Dashboard

**UID**: `claude-code-working`

コスト・トークン・セッション数などの基本メトリクスと主要 KPI を表示する汎用ダッシュボードです。

**パネル構成**:

| パネル | タイプ | 内容 |
|---|---|---|
| Total Cost / Active Users / Total Tokens / Lines of Code | Stat | トップレベル KPI カード |
| Cost by Model | Pie chart | モデル別コスト内訳 |
| Token Usage by Type | Pie chart | トークン種別内訳（input, output, cacheRead, cacheCreation） |
| Cost by User / Lines of Code by Type | Table | ユーザー別コスト、タイプ別 LOC（追加/削除） |
| Active Time (Total) / Active Time by Type | Stat + Pie | 合計・種別ごとのアクティブ時間 |
| Cost by Organization | Table | 組織別コスト |
| Tool Results / API Errors | Logs | ツール結果と API エラーの生ログ |
| Sessions / Commits / Pull Requests | Stat | セッション数・成果物カウント |
| Cost per Commit | Stat | コミット 1 件あたりの AI コスト — ROI 測定の基本指標 |
| DAU (Daily Active Users) | Stat | 直近 24 時間のユニークユーザー数 |
| Cache Hit Rate | Stat | cache_read_tokens / (input_tokens + cache_read_tokens) |

---

### ROI & Productivity

**UID**: `claude-code-roi-productivity`

ROI（投資対効果）と開発者の生産性を測定するダッシュボードです。

**パネル構成**:

| パネル | タイプ | 内容 |
|---|---|---|
| Cost per Commit | Stat | コミット 1 件あたりの AI コスト — ROI の核心指標 |
| Cost per PR | Stat | PR 1 件あたりの AI コスト |
| Cost per LOC (Added) | Stat | 追加コード 1 行あたりの AI コスト |
| LOC per Session | Stat | セッションあたりのコード行数 — 生産性指標 |
| Commits per Session | Stat | セッションあたりのコミット数 — 成果指標 |
| User Wait Time Ratio | Stat | CLI 処理時間 / 全アクティブ時間 — AI 待機時間の割合 |
| Cache Hit Rate | Stat | キャッシュ読み取りトークンの割合 |
| Estimated Cache Savings | Stat | キャッシュヒットによる推定コスト節約額 |
| Cache Hit Rate Trend | Time series | キャッシュヒット率の時系列推移 |
| Cache Hit Rate by Model | Bar chart | モデル別のキャッシュ効率比較 |
| Cost Efficiency Trend | Time series | Cost/Commit と Cost/PR の推移 |
| Lines of Code Trend by Type | Time series | LOC（追加・削除）の時系列推移 |
| User Productivity Summary | Table | ユーザー別コスト・コミット数・LOC の比較一覧 |

---

### Adoption & Usage Patterns

**UID**: `claude-code-adoption-usage`

組織全体の採用状況と利用パターンを追跡するダッシュボードです。

**パネル構成**:

| パネル | タイプ | 内容 |
|---|---|---|
| DAU / WAU / MAU | Stat | 日次・週次・月次のアクティブユーザー数 |
| Fast Mode Usage Rate | Stat | Fast Mode を使用した API リクエストの割合 |
| Model Usage Over Time | Time series | モデル別 API リクエスト数の時系列推移 |
| Sessions Over Time | Time series | セッション数の推移 |
| Terminal / IDE Distribution | Pie chart | ターミナル・IDE 別のセッション分布（VSCode、JetBrains 等） |
| Organization Cost Trend | Time series | 組織別のコスト推移 |
| Fast Mode vs Normal Mode Over Time | Time series | Fast Mode の採用状況トラッキング |
| Prompt Activity Over Time | Time series | プロンプト数の推移（ピーク利用時間帯の把握） |
| User Adoption Summary | Table | ユーザー別セッション数・コスト・アクティブ時間の一覧 |

---

### Trace Explorer

**UID**: `claude-code-trace-explorer`

Enhanced Telemetry Beta のトレーススパンを探索するダッシュボード。TTFT、ツール実行分解、権限待ち時間を可視化します。`CLAUDE_CODE_ENHANCED_TELEMETRY_BETA=1` が必要です。

**パネル構成**:

| パネル | タイプ | 内容 |
|---|---|---|
| TTFT (Time to First Token) - P50/P95/P99 | Time series | LLM リクエストの最初のトークンが返るまでの時間分布 |
| TTFT by Model | Bar chart | モデル別の平均 TTFT 比較 |
| Tool Permission Wait Time (P50/P95) | Time series | ユーザーの権限承認待ち時間 |
| Permission Decision Distribution | Bar chart | accept/reject/timeout の判断分布 |
| Interaction Duration Breakdown | Time series (stacked) | LLM リクエスト vs ツール実行 vs 権限待ちの内訳 |
| Tool Result Token Consumption | Bar chart | ツール別のトークン消費量 — コスト大きいツールの特定 |
| Tool Execution Details | Table | 最近のツール実行スパン（実行時間・成否・エラー） |
| Recent Interaction Traces | Table | 最近のインタラクショントレース — traceID クリックでウォーターフォール表示 |

---

### Lifecycle Observability

**UID**: `claude-code-lifecycle`

セッション単位でどのスキル・コマンド・エージェントが使用されたかを追跡するダッシュボード。DuckDB + Claude Code Hooks で実現。

**使い方**:
1. 全セッションの概要統計と使用内訳を確認
2. Session List で `session_id` をクリックしてドリルダウン
3. Session Event Timeline でセッション内の全ライフサイクルイベントを時系列で確認

**パネル構成**:

| パネル | タイプ | 内容 |
|---|---|---|
| Total Sessions / Skill Invocations / Agent Spawns / Command Invocations / Unique Skills / Unique Agent Types | Stat | 概要 KPI カード — session_id でフィルタ可能 |
| Top Skills by Usage | Bar chart | スキル呼び出し回数ランキング（commit, review 等） |
| Command Distribution | Bar chart | スラッシュコマンドの使用回数（UserPromptSubmit で検出） |
| Agent Types | Bar chart | エージェントタイプ別スポーン数（Explore, Plan, general-purpose） |
| Session List | Table | 全セッション一覧（モデル・プロンプト数・スキル/エージェント/コマンド数）。session_id クリックでドリルダウン |
| Session Event Timeline | Table | セッション内の全ライフサイクルイベントを時系列表示 |

---

### Global Usage Tracking

**UID**: `claude-code-global-usage`

全セッション横断でのスキル・コマンド・エージェント使用トレンドを追跡するダッシュボード。モデル別・プロジェクト別の分析も可能。

**パネル構成**:

| パネル | タイプ | 内容 |
|---|---|---|
| Total Sessions / Skill Invocations / Agent Spawns / Commands / Unique Skills / Unique Agent Types | Stat | グローバル KPI カード（セッションフィルタなし） |
| Daily Sessions / Daily Skill Invocations / Daily Agent Spawns | Time series (bar) | 日別の利用トレンド |
| Top Skills / Top Commands / Top Agent Types | Bar chart | 全セッション横断の使用ランキング |
| Model Usage | Bar chart | モデル別セッション数 |
| Top Projects | Table | プロジェクト（作業ディレクトリ）別のセッション・スキル・エージェント数 |

## トレーススパン (Enhanced Telemetry Beta)

`CLAUDE_CODE_ENHANCED_TELEMETRY_BETA=1` が必要。スパンは OTLP 経由で Tempo に送信されます。

| スパン名 | 主な属性 |
|---|---|
| `claude_code.interaction` | ユーザーインタラクション全体のルートスパン（プロンプト → レスポンス） |
| `claude_code.llm_request` | LLM API 呼び出し。`ttft_ms`, `model`, `input_tokens`, `output_tokens` |
| `claude_code.tool` | ツール呼び出し。`tool_name`, `result_tokens` |
| `claude_code.tool.execution` | ツール実行フェーズ。`tool_name`, `success`, `error` |
| `claude_code.tool.blocked_on_user` | 権限待ち。`decision`（accept/reject/timeout） |

## ファイル構成

```
.
├── docker-compose.yml              # 監視スタック定義
├── otel-collector-config.yaml      # OTEL Collector 設定
├── prometheus.yml                  # Prometheus スクレイプ設定
├── tempo.yaml                      # Tempo 設定
├── .claude/
│   └── settings.json               # Claude Code テレメトリ設定（自動有効化）
├── grafana/
│   ├── dashboards/
│   │   ├── prompt-timeline.json    # Prompt Timeline ダッシュボード
│   │   ├── session-timeline.json   # Session Timeline ダッシュボード
│   │   ├── developer-efficiency.json # Developer Efficiency ダッシュボード
│   │   ├── anomaly-health.json     # Anomaly & Health ダッシュボード
│   │   ├── working-dashboard.json  # 基本メトリクスダッシュボード
│   │   ├── roi-productivity.json   # ROI & Productivity ダッシュボード
│   │   ├── adoption-usage.json     # Adoption & Usage Patterns ダッシュボード
│   │   ├── trace-explorer.json    # Trace Explorer ダッシュボード (Enhanced Telemetry Beta)
│   │   ├── lifecycle-observability.json # Lifecycle Observability ダッシュボード (DuckDB + Hooks)
│   │   └── global-usage.json          # Global Usage Tracking ダッシュボード (DuckDB)
│   └── provisioning/
│       ├── dashboards/
│       │   └── dashboards.yaml     # ダッシュボード自動プロビジョニング設定
│       └── datasources/
│           └── datasources.yaml    # データソース設定（Prometheus/Loki/Tempo/DuckDB）
├── duckdb-api/
│   ├── Dockerfile                  # Go マルチステージビルド
│   ├── main.go                     # HTTP サーバー + API ハンドラ
│   ├── db.go                       # DuckDB 接続管理 + JSONL インポーター
│   ├── schema.sql                  # DuckDB テーブル定義
│   └── go.mod / go.sum             # Go モジュール依存
├── hooks/
│   └── lifecycle-logger.sh         # ライフサイクルイベント記録用 Hook スクリプト
├── claude_code_roi_full.md         # ROI 計測の詳細ガイド
├── troubleshooting.md              # トラブルシューティング
└── report-generation-prompt.md    # 自動レポート生成プロンプトテンプレート
```

## 主要メトリクスとログイベント

Claude Code は以下のイベントを OTLP で送信します：

| イベント | 用途 |
|---|---|
| `user_prompt` | プロンプト送信。`prompt_id` / `session_id` / `prompt_length` を含む |
| `api_request` | API リクエスト。`model` / `cost_usd` / `duration_ms` / `input_tokens` / `output_tokens` / `cache_read_tokens` / `cache_creation_tokens` / `speed` を含む |
| `tool_result` | ツール実行結果。`tool_name` / `success` / `duration_ms` / `tool_result_size_bytes` を含む |
| `api_error` | API エラー。`status_code` / `attempt` / `prompt_id` を含む |
| `tool_decision` | ツール実行の承認・拒否。`decision`（accept/reject）/ `source`（config/user_reject 等）を含む |
| `system_prompt` | システムプロンプト追跡。`system_prompt_hash` / `system_prompt_length` を含む |
| `hook_execution_complete` | Hook 実行結果。`hook_name` / `num_success` / `num_blocking` を含む |
| `feedback_survey` | フィードバック調査（compact conversation 検知含む）。`survey_type`（`post_compact`）を含む |

Loki での基本クエリ:

```logql
# 全イベントを確認
{service_name="claude-code"} | json | drop __error__, __error_details__

# 特定 prompt_id のイベントをトレース
{service_name="claude-code"} | json | drop __error__, __error_details__ | prompt_id=`<your-prompt-id>`

# ツール失敗のみ抽出
{service_name="claude-code"} | json | drop __error__, __error_details__ | event_name=`tool_result` | success=`false`
```

## トラブルシューティング

詳細は [troubleshooting.md](troubleshooting.md) を参照してください。

**よくある問題**:

- **Loki にデータが届かない**: `OTEL_LOGS_EXPORTER=otlp` が設定されているか確認
- **Prometheus の値が不正確**: `OTEL_EXPORTER_OTLP_METRICS_TEMPORALITY_PREFERENCE=cumulative` が必要
- **テレメトリが有効にならない**: `docker compose ps` でコンテナが起動しているか確認し、`curl http://localhost:4317` でポートが開いているか確認

## Contributing

実装経験に基づいた改善や追加ユースケースがあれば、Issue / PR をお送りください。

Original guide by [Kashyap Coimbatore Murali](https://www.linkedin.com/in/kashyap-murali/)
