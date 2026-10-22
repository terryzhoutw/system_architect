# 政务 API 安全运营 Agent Demo

个人学习用本地 Demo，当前实现前三个阶段：

1. 项目骨架、配置文件和启动说明。
2. FastAPI 路由、模拟 Java 业务数据、Prometheus exporter 指标和 ES 应用日志适配器。
3. LangGraph 工作流与 MongoDB 运行记录。

## 当前工作流

```text
POST /api/analysis
  → 创建 MongoDB 运行记录（running）
  → LangGraph：加载模拟告警和 Java API 资产
  → LangGraph 并行查询：模拟 Prometheus 指标 + Elasticsearch 应用日志
  → LangGraph：按告警类型整理分析草稿
  → LangGraph：将结果更新到 MongoDB（completed）
```

当前结论由规则模板生成，**不是大模型生成**；每条证据都来自标记为 Mock 的本地模拟适配器。这样可先验证接口、图流程和运行记录，再接入模型、Milvus 和真实企业系统。

## RAG 样例语料

`data/knowledge/samples/` 已准备 7 类场景、每类 100 条，共 700 条 JSONL 案例，可供后续 Milvus 导入和检索效果评估：

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
- 可用端口 `8000`、`27017`

## 启动

在项目目录执行：

```powershell
Copy-Item .env.example .env
docker compose up --build
```

启动后打开：

- API 文档：<http://localhost:8000/docs>
- 健康状态：<http://localhost:8000/health>
- 模拟告警列表：<http://localhost:8000/api/alerts>

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

## 配置

复制 `.env.example` 为 `.env` 后可调整应用名称和 MongoDB 数据库、集合名。Compose 中 API 容器通过服务名 `mongo` 连接 MongoDB；若直接在本机运行 Python，则需将 `MONGODB_URI` 设为 `mongodb://localhost:27017`。

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
  main.py                  # FastAPI 路由
  schemas.py               # 请求/响应模型
  settings.py              # 环境配置
data/
  knowledge/samples/       # 7 个场景，每个场景 100 条合成 JSONL 样例
scripts/
  generate_sample_cases.py # 可重复生成上述演示语料
```

## 当前范围与后续接口位置

- **已实现**：本地 Mock 告警、API 资产、Prometheus 指标和 ES 应用日志；LangGraph 并行查询两类观测数据；MongoDB `running/completed/failed` 运行状态；运行结果查询 API。
- **尚未接入**：三家模型、Milvus/RAG、Redis、Kafka、真实 Prometheus、真实 Elasticsearch、真实 Java 服务、APISIX、SSO、前端工作台及现有可观测平台。
- 真实企业接入时，应把 Mock adapter 替换为只读 HTTP 客户端；用户身份和租户权限由 SSO/APISIX 与服务端校验，不信任客户端提交的身份字段。

## API 一览

| 方法 | 路径 | 用途 |
|---|---|---|
| `GET` | `/health` | 检查 API 与 MongoDB 状态 |
| `GET` | `/api/alerts` | 查看模拟告警 |
| `POST` | `/api/analysis` | 启动一次分析并返回结果 |
| `GET` | `/api/runs/{run_id}` | 查询持久化运行记录 |
