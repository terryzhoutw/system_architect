# RAG 知识库样例目录

`samples/` 下有 7 个场景的合成案例数据，每个场景 100 条，完整清单见 `samples/manifest.json`。

## 数据说明

- 文件格式：UTF-8 JSON Lines，每行一条记录。
- `content`：后续用于 Embedding 和 Milvus 检索的正文。
- `user_query`、`reference_conclusion`：可作为检索/回答评估样例。
- `scenario_id`、`security_level`、`department_scope`、`source_version`：可用于分类、权限过滤和版本管理演示。
- `synthetic: true`：所有记录均为合成数据，不是真实生产或政府数据。

个人信息场景只出现字段名，不含真实姓名、证件号、手机号等值；网络地址使用文档示例地址。合成案例只能用于开发演示，不应被作为单位制度或真实处置依据引用。

以后接入真实知识时，应另建经过授权和脱敏的制度/手册语料，并标注文件来源、版本、生效时间、适用部门和密级，再导入 Milvus。当前项目尚未实现 Milvus 导入和 RAG 检索接口。
