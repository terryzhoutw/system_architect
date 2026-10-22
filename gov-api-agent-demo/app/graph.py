from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph

from app.adapters.elasticsearch_mock import ElasticsearchMock
from app.adapters.java_business_mock import JavaBusinessMock
from app.adapters.prometheus_mock import PrometheusMock
from app.repositories.mongo_runs import MongoRunRepository


class AnalysisState(TypedDict, total=False):
    run_id: str
    alert_id: str
    question: str
    alert: dict[str, Any]
    business_context: dict[str, Any]
    prometheus_metrics: list[dict[str, Any]]
    application_logs: list[dict[str, Any]]
    report: dict[str, Any]


def build_analysis_graph(repository: MongoRunRepository):
    java = JavaBusinessMock()
    elasticsearch = ElasticsearchMock()
    prometheus = PrometheusMock()

    def load_business_context(state: AnalysisState) -> dict[str, Any]:
        alert = java.get_alert(state["alert_id"])
        asset = java.get_api_asset(alert["api_id"])
        return {"alert": alert, "business_context": asset}

    def query_prometheus_metrics(state: AnalysisState) -> dict[str, Any]:
        return {"prometheus_metrics": prometheus.query_metrics(state["alert_id"])}

    def query_elasticsearch_logs(state: AnalysisState) -> dict[str, Any]:
        return {"application_logs": elasticsearch.search_application_logs(state["alert_id"])}

    def draft_report(state: AnalysisState) -> dict[str, Any]:
        alert = state["alert"]
        asset = state["business_context"]
        logs = state["application_logs"]
        metrics = state["prometheus_metrics"]
        messages = [event["message"] for event in logs]
        metric_notes = [item["note"] for item in metrics]

        if alert["alert_type"] == "jwt_401_spike":
            assessment = "证据倾向于 JWT 验证配置或密钥同步异常；当前不足以确认攻击或最终根因。"
            actions = [
                "核对 SSO 在告警时间前后的签名密钥轮换记录。",
                "对比失败请求中的 kid、issuer 与当前验证配置。",
                "检查 APISIX 或验证组件是否仍缓存旧公钥。",
                "按客户端对比失败比例和来源，确认影响范围。",
            ]
            limitations = ["模拟数据未包含 SSO 变更记录和网关公钥缓存状态，根因待核实。"]
        elif alert["alert_type"] == "traffic_spike":
            assessment = "请求量明显高于模拟基线，存在自动化访问迹象；目前不能仅凭流量判断为恶意攻击。"
            actions = [
                "核对调用客户端和用户身份是否符合业务授权。",
                "检查重复分页游标和高频轮询情况。",
                "向业务负责人确认是否存在活动或批量作业。",
                "按现有审批流程评估是否需要调整限流策略。",
            ]
            limitations = ["模拟数据没有业务活动日历和历史基线明细，不能直接判定为攻击。"]
        else:
            assessment = "日志显示下游依赖调用超时，当前证据更支持依赖服务变慢，需要继续核对实例和变更记录。"
            actions = [
                "检查证书服务实例健康度和连接池状态。",
                "核对告警前后的依赖服务发布或配置变更。",
                "查看完整链路追踪，确认耗时是否集中在下游调用。",
                "观察下游恢复后接口 P95 和 5xx 是否同步回落。",
            ]
            limitations = ["模拟数据未连接真实指标、链路追踪或发布平台，原因尚未确认。"]

        findings = [alert["summary"], f"接口使用 {asset['auth_type']}，所属系统为 {asset['system_name']}。"]
        if messages:
            findings.append("ES 应用日志：" + "；".join(dict.fromkeys(messages)))
        if metric_notes:
            findings.append("Prometheus 指标：" + "；".join(metric_notes))

        evidence = [
            {"source": "JavaMock", "ref": f"alert:{alert['alert_id']}", "description": "模拟告警和接口资产"},
            {"source": "PrometheusMock", "ref": f"metrics:{alert['alert_id']}", "description": f"检索到 {len(metrics)} 条模拟指标，来源为服务器/中间件 exporter"},
            {"source": "ElasticsearchMock", "ref": f"logs:{alert['alert_id']}", "description": f"检索到 {len(logs)} 条模拟应用日志"},
        ]
        report = {
            "assessment": assessment,
            "findings": findings,
            "recommended_actions": actions,
            "limitations": limitations,
            "evidence": evidence,
            "mode": "rule_based_demo",
        }
        return {"report": report}

    def persist_run(state: AnalysisState) -> dict[str, Any]:
        result = {
            "alert": state["alert"],
            "business_context": state["business_context"],
            "prometheus_metrics": state["prometheus_metrics"],
            "application_logs": state["application_logs"],
            "report": state["report"],
        }
        repository.complete(state["run_id"], result)
        return {}

    builder = StateGraph(AnalysisState)
    builder.add_node("load_business_context", load_business_context)
    builder.add_node("query_prometheus_metrics", query_prometheus_metrics)
    builder.add_node("query_elasticsearch_logs", query_elasticsearch_logs)
    builder.add_node("draft_report", draft_report)
    builder.add_node("persist_run", persist_run)
    builder.add_edge(START, "load_business_context")
    builder.add_edge("load_business_context", "query_prometheus_metrics")
    builder.add_edge("load_business_context", "query_elasticsearch_logs")
    builder.add_edge(["query_prometheus_metrics", "query_elasticsearch_logs"], "draft_report")
    builder.add_edge("draft_report", "persist_run")
    builder.add_edge("persist_run", END)
    return builder.compile()
