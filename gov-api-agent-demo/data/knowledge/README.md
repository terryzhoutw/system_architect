# RAG 知识库样例目录

`samples/` 下有 7 个场景的合成案例数据，每个场景 100 条，完整清单见 `samples/manifest.json`。

## 数据说明

- 文件格式：UTF-8 JSON Lines，每行一条记录。
- `content`：后续用于 Embedding 和 Milvus 检索的正文。
- `user_query`、`reference_conclusion`：可作为检索/回答评估样例。
- `scenario_id`、`security_level`、`department_scope`、`source_version`：可用于分类、权限过滤和版本管理演示。
- `synthetic: true`：所有记录均为合成数据，不是真实生产或政府数据。

个人信息场景只出现字段名，不含真实姓名、证件号、手机号等值；网络地址使用文档示例地址。合成案例只能用于开发演示，不应被作为单位制度或真实处置依据引用。

## 导入与检索

Milvus Lite 以本地文件运行，不需要单独启动 Milvus 服务。配置 `.env` 中的 Embedding 兼容接口、模型名、API Key 和向量维度后，在项目根目录运行：

```powershell
python scripts/ingest_knowledge.py
```

脚本按记录组合标题、问题、正文、参考结论和建议，按最多 1200 字符切片并保留 160 字符重叠；每批生成向量后以稳定 ID upsert 到 `MILVUS_COLLECTION`。Lite 数据持久化在 `MILVUS_URI` 指向的 `.db` 文件中。重复运行会覆盖相同 ID，方便重新索引。模型返回维度必须等于 `EMBEDDING_DIMENSION`。

Milvus Lite 的同一数据目录由单个进程持有。首次导入可在 API 服务启动后、首次 RAG 问答前运行；以后重新导入时，先停止正在使用该数据库文件的 API 进程，再导入并重启服务。

调用 `POST /api/rag/ask` 执行问题向量化、Milvus Top-K 召回、带引用的模型回答，并将问答和引用写入 MongoDB 运行记录。可选 `scenario_id` 元数据过滤；低于 `RAG_MIN_SCORE` 的命中不会提供给模型。引用列表包含样例编号、来源版本、场景、相似度和文本片段。

Embedding 与聊天模型使用 OpenAI 兼容 HTTP 接口，因此可连接提供该接口的国内模型服务。两者可配置不同模型、地址和密钥。API Key 只从环境变量读取，不写入样例数据。Milvus Lite 面向本地开发和小规模样例；需要多实例并发写入或生产级扩展时，将 `MILVUS_URI` 切换为独立 Milvus 服务地址。

以后接入真实知识时，应另建经过授权和脱敏的制度/手册语料，并标注文件来源、版本、生效时间、适用部门和密级，再导入 Milvus；需要在服务端加入按登录用户/部门执行的权限过滤。当前接口的 `scenario_id` 只是演示过滤条件，不能代替真实 SSO 身份授权。
