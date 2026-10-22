from copy import deepcopy


_ALERTS = {
    "SEC-2026-1012": {
        "alert_id": "SEC-2026-1012",
        "alert_type": "jwt_401_spike",
        "severity": "high",
        "api_id": "api-permit-query",
        "api_path": "/v1/permit/query",
        "start_time": "2026-10-22T14:05:00+08:00",
        "end_time": "2026-10-22T14:20:00+08:00",
        "summary": "HTTP 401 比例从约 2% 升至 68%",
        "owner": "许可服务组",
    },
    "SEC-2026-1026": {
        "alert_id": "SEC-2026-1026",
        "alert_type": "traffic_spike",
        "severity": "medium",
        "api_id": "api-benefit-query",
        "api_path": "/v1/benefit/query",
        "start_time": "2026-10-22T10:00:00+08:00",
        "end_time": "2026-10-22T10:10:00+08:00",
        "summary": "请求量在 10 分钟内升至近期基线的约 5 倍",
        "owner": "福利服务组",
    },
    "OPS-2026-1103": {
        "alert_id": "OPS-2026-1103",
        "alert_type": "latency_5xx",
        "severity": "high",
        "api_id": "api-certificate-verify",
        "api_path": "/v1/certificate/verify",
        "start_time": "2026-10-22T11:03:00+08:00",
        "end_time": "2026-10-22T11:18:00+08:00",
        "summary": "P95 从 300ms 升至 4.2s，5xx 比例达到 12%",
        "owner": "证书服务组",
    },
}

_ASSETS = {
    "api-permit-query": {
        "api_id": "api-permit-query",
        "api_path": "/v1/permit/query",
        "auth_type": "SSO JWT",
        "system_name": "许可服务",
        "owner": "许可服务组",
        "sensitivity": "内部",
    },
    "api-benefit-query": {
        "api_id": "api-benefit-query",
        "api_path": "/v1/benefit/query",
        "auth_type": "SSO JWT",
        "system_name": "福利服务",
        "owner": "福利服务组",
        "sensitivity": "内部",
    },
    "api-certificate-verify": {
        "api_id": "api-certificate-verify",
        "api_path": "/v1/certificate/verify",
        "auth_type": "SSO JWT",
        "system_name": "证书核验服务",
        "owner": "证书服务组",
        "sensitivity": "内部",
        "dependencies": ["身份服务", "证书服务"],
    },
}


class JavaBusinessMock:
    """Local fixture replacing read-only Java business APIs in the demo."""

    def list_alerts(self) -> list[dict]:
        return [deepcopy(item) for item in _ALERTS.values()]

    def get_alert(self, alert_id: str) -> dict:
        if alert_id not in _ALERTS:
            raise KeyError(f"未找到模拟告警: {alert_id}")
        return deepcopy(_ALERTS[alert_id])

    def get_api_asset(self, api_id: str) -> dict:
        if api_id not in _ASSETS:
            raise KeyError(f"未找到模拟 API 资产: {api_id}")
        return deepcopy(_ASSETS[api_id])
