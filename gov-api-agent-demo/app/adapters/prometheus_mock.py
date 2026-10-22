from copy import deepcopy


_METRICS = {
    "SEC-2026-1012": [
        {"exporter": "apisix-exporter", "instance": "gateway-01", "metric": "http_5xx_ratio_percent", "value": 0.4, "unit": "%", "note": "网关 5xx 未同步升高"},
        {"exporter": "node-exporter", "instance": "gateway-host-01", "metric": "node_cpu_utilization_percent", "value": 42, "unit": "%", "note": "主机 CPU 正常"},
        {"exporter": "jmx-exporter", "instance": "permit-service-01", "metric": "jvm_heap_used_percent", "value": 58, "unit": "%", "note": "JVM 堆使用率正常"},
    ],
    "SEC-2026-1026": [
        {"exporter": "apisix-exporter", "instance": "gateway-01", "metric": "http_requests_per_second_ratio_to_baseline", "value": 5.1, "unit": "倍", "note": "入口请求速率约为近期基线的 5.1 倍"},
        {"exporter": "node-exporter", "instance": "gateway-host-01", "metric": "node_cpu_utilization_percent", "value": 71, "unit": "%", "note": "主机 CPU 升高但未达到模拟阈值"},
    ],
    "OPS-2026-1103": [
        {"exporter": "apisix-exporter", "instance": "gateway-01", "metric": "upstream_latency_p95_ms", "value": 4200, "unit": "ms", "note": "上游 P95 延迟升高"},
        {"exporter": "apisix-exporter", "instance": "gateway-01", "metric": "upstream_5xx_ratio_percent", "value": 12, "unit": "%", "note": "上游 5xx 比例升高"},
        {"exporter": "jmx-exporter", "instance": "certificate-service-01", "metric": "jvm_heap_used_percent", "value": 63, "unit": "%", "note": "JVM 堆使用率未明显异常"},
    ],
}


class PrometheusMock:
    """Local fixture representing Prometheus metrics from server/middleware exporters."""

    def query_metrics(self, alert_id: str) -> list[dict]:
        return deepcopy(_METRICS.get(alert_id, []))
