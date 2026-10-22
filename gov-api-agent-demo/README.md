# 政务 API 安全运营 Agent Demo

个人学习用本地 Demo，当前实现以下阶段：

1. 项目骨架、配置文件和启动说明。
2. FastAPI 路由、模拟 Java 业务数据、Prometheus exporter 指标和 ES 应用日志适配器。
3. LangGraph 工作流与 MongoDB 运行记录。
4. OpenAI 兼容 Embedding/聊天服务、Milvus 向量化、元数据过滤检索和引用式 RAG 问答。

## 当前工作流

```text
POST /api/analysis
  → 创建 MongoDB 运行记录（running）
  → LangGraph：加载模拟告警和 Java API 资产
  → LangGraph 并行查询：模拟 Prometheus 指标 + Elasticsearch 应用日志
  → LangGraph：按告警类型整理分析草稿
  → LangGraph：将结果更新到 MongoDB（completed）
```

告警分析接口当前由规则模板生成，**不是大模型生成**；每条证据都来自标记为 Mock 的本地模拟适配器。

告警分析流程仍使用规则模板。RAG 问答单独走 `/api/rag/ask`，从样例知识库检索资料后调用聊天模型回答，并返回引用；当前样例是合成学习材料，不代表真实制度或生产事故。

## RAG 样例语料

`data/knowledge/samples/` 已准备 7 类场景、每类 100 条，共 700 条 JSONL 案例，可导入 Milvus 并用于检索效果评估：

| 文件 | 场景 | 数量 |
|---|---|---:|
| `jwt_401.jsonl` | 401 与 SSO/JWT 验签异常 | 100 |
| `traffic_spike.jsonl` | API 异常流量 | 100 |
| `latency_5xx.jsonl` | 慢请求与 5xx | 100 |
| `path_scan.jsonl` | 路径扫描与探测 | 100 |
| `pii_exposure.jsonl` | 个人信息返回风险 | 100 |
| `cert_expiry.jsonl` | 证书与密钥到期 | 100 |
| `runbook_qa.jsonl` | 处置手册知识问答 | 100 |

**数据性质：** 这些是贴近运维语境的全合成示例，不是政府生产数据或真实事故记录，不应当作为真实处置依据。IP 使用文档示例网段；个人信息只有字段名，不含真实个人信息。以后接入单位实际资料时，应使用经授权、脱敏、带版本和权限标签的数据替换或补充。

每条记录包含 `id`、`scenario_id`、`title`、`user_query`、`content`、`reference_conclusion`、`recommended_actions` 和来源/密级元数据。`content` 可用于知识检索；`user_query` 与参考结论可用于构造离线评估问题。具体字段见 `data/knowledge/README.md`。

重新生成全部样例：

```powershell
python scripts/generate_sample_cases.py
```

## 环境要求

- Docker Desktop（包含 Docker Compose）
- 可用端口 `8000`、`27017`、`19530`、`9091`
- 可调用的 OpenAI 兼容 Embedding 和聊天模型服务

## 启动

在项目目录执行：

```powershell
Copy-Item .env.example .env
docker compose up --build
```

首次启动后配置 `.env` 中的 Embedding/聊天模型地址、模型名和 API Key。向量维度须与 Embedding 模型输出一致；下面示例默认 `1024`。

启动 Milvus、MongoDB 与 API 后，先导入合成知识：

```powershell
python scripts/ingest_knowledge.py
```

Docker API 容器也包含导入脚本；可用以下命令在容器内导入：

```powershell
docker compose exec agent-api python scripts/ingest_knowledge.py
```

首次导入需调用 Embedding 服务对 700 条样例向量化。修改语料后再次运行会按稳定 ID upsert。

启动后打开：

- API 文档：<http://localhost:8000/docs>
- 健康状态：<http://localhost:8000/health>
- 模拟告警列表：<http://localhost:8000/api/alerts>
- RAG 问答接口：<http://localhost:8000/docs> 中的 `POST /api/rag/ask`

停止服务：

```powershell
docker compose down
```

保留 MongoDB 数据卷。若需要连同本地 Demo 数据一起清空，可使用 `docker compose down -v`。

## 发起分析

在 Swagger 页面调用 `POST /api/analysis`，请求体示例：

```json
{
  "alert_id": "SEC-2026-1012",
  "question": "请分析告警并给出排查建议",
  "user_id": "demo-user"
}
```

也可以在 PowerShell 中执行：

```powershell
$body = @{
  alert_id = "SEC-2026-1012"
  question = "请分析告警并给出排查建议"
  user_id = "demo-user"
} | ConvertTo-Json

Invoke-RestMethod -Method Post -Uri http://localhost:8000/api/analysis `
  -ContentType "application/json" -Body $body
```

可用模拟告警：

| 告警编号 | 场景 |
|---|---|
| `SEC-2026-1012` | JWT / SSO 相关 401 激增 |
| `SEC-2026-1026` | API 请求量突然升高 |
| `OPS-2026-1103` | 依赖调用超时、5xx 和慢请求 |

分析响应包含 `run_id`。通过 `GET /api/runs/{run_id}` 查询 MongoDB 中的持久化运行记录。

## RAG 知识问答

在 Swagger 页面调用 `POST /api/rag/ask`：

```json
{
  "question": "JWT 出现 kid_not_found 时先查什么？",
  "user_id": "demo-user",
  "scenario_id": "runbook_qa",
  "top_k": 5
}
```

流程为：问题 Embedding → Milvus 相似度 Top-K 检索与可选场景过滤 → 按相似度阈值筛选 → 聊天模型基于检索上下文生成答案 → 返回引用并写入 MongoDB。没有足够相关资料时返回明确的无依据答复，不调用模型补写。问答记录同样可通过 `GET /api/runs/{run_id}` 查询。

## 配置

复制 `.env.example` 为 `.env` 后配置：

- `EMBEDDING_BASE_URL`、`EMBEDDING_API_KEY`、`EMBEDDING_MODEL`：向量模型的 OpenAI 兼容接口。
- `EMBEDDING_DIMENSION`：模型输出维度，必须与 Milvus collection 一致。
- `LLM_BASE_URL`、`LLM_API_KEY`、`LLM_MODEL`：问答聊天模型接口。
- `MILVUS_COLLECTION`、`RAG_TOP_K`、`RAG_MIN_SCORE`：向量集合、召回条数和最低相似度。

Embedding 和聊天服务可以是同一个提供方，也可以分开配置。Compose 中 API 容器通过服务名连接 MongoDB 和 Milvus；若直接在本机运行 Python，则需使用 `MONGODB_URI=mongodb://localhost:27017` 和 `MILVUS_URI=http://localhost:19530`。

本机直接运行的可选方式：

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
$env:MONGODB_URI = "mongodb://localhost:27017"
uvicorn app.main:app --reload
```

## 目录结构

```text
app/
  adapters/
    java_business_mock.py  # 模拟告警和 API 资产；后续替换为 Java API 适配器
    prometheus_mock.py     # 模拟服务器/中间件 exporter 指标
    elasticsearch_mock.py  # 模拟 ES 应用日志查询
  repositories/
    mongo_runs.py          # Agent 运行记录的 MongoDB 持久化
  graph.py                 # LangGraph 节点和流程
  rag/                      # OpenAI 兼容模型、Milvus store、RAG 服务和 LangGraph 问答流
  main.py                  # FastAPI 路由
  schemas.py               # 请求/响应模型
  settings.py              # 环境配置
data/
  knowledge/samples/       # 7 个场景，每个场景 100 条合成 JSONL 样例
scripts/
  generate_sample_cases.py # 可重复生成上述演示语料
  ingest_knowledge.py      # Embedding 向量化并批量 upsert 至 Milvus
```

## 当前范围与后续接口位置

- **已实现**：本地 Mock 告警/指标/日志；告警分析 LangGraph；MongoDB 运行记录；Embedding 和聊天模型 OpenAI 兼容适配；Milvus 向量写入/Top-K/场景过滤；RAG LangGraph 问答和引用。
- **尚未接入**：三家国内模型的专属 SDK/容灾路由、Redis、Kafka、真实 Prometheus、真实 Elasticsearch、真实 Java 服务、APISIX、SSO、前端工作台及现有可观测平台。
- 真实企业接入时，应把 Mock adapter 替换为只读 HTTP 客户端；用户身份和租户权限由 SSO/APISIX 与服务端校验，不信任客户端提交的身份字段。

## API 一览

| 方法 | 路径 | 用途 |
|---|---|---|
| `GET` | `/health` | 检查 API 与 MongoDB 状态 |
| `GET` | `/api/alerts` | 查看模拟告警 |
| `POST` | `/api/analysis` | 启动一次分析并返回结果 |
| `POST` | `/api/rag/ask` | 检索知识库并生成带引用的回答 |
| `GET` | `/api/runs/{run_id}` | 查询持久化运行记录 |
