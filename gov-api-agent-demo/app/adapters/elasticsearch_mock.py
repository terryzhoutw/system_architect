from copy import deepcopy


_APPLICATION_LOGS = {
    "SEC-2026-1012": [
        {"time": "2026-10-22T14:06:12+08:00", "level": "WARN", "service": "permit-service", "message": "JWT validation failed: kid_not_found", "trace_id": "tr-1012-001"},
        {"time": "2026-10-22T14:07:03+08:00", "level": "WARN", "service": "permit-service", "message": "JWT validation failed: issuer_mismatch", "trace_id": "tr-1012-002"},
        {"time": "2026-10-22T14:08:45+08:00", "level": "INFO", "service": "permit-service", "message": "request completed", "trace_id": "tr-1012-003"},
    ],
    "SEC-2026-1026": [
        {"time": "2026-10-22T10:03:11+08:00", "level": "INFO", "service": "benefit-service", "message": "repeated page cursor", "trace_id": "tr-1026-001"},
        {"time": "2026-10-22T10:04:19+08:00", "level": "WARN", "service": "benefit-service", "message": "query rate above baseline", "trace_id": "tr-1026-002"},
        {"time": "2026-10-22T10:06:31+08:00", "level": "WARN", "service": "benefit-service", "message": "request rate limited", "trace_id": "tr-1026-003"},
    ],
    "OPS-2026-1103": [
        {"time": "2026-10-22T11:04:12+08:00", "level": "ERROR", "service": "certificate-service", "message": "upstream certificate-service timeout", "trace_id": "tr-1103-001"},
        {"time": "2026-10-22T11:07:40+08:00", "level": "ERROR", "service": "certificate-service", "message": "dependency call slow", "trace_id": "tr-1103-002"},
        {"time": "2026-10-22T11:10:08+08:00", "level": "INFO", "service": "certificate-service", "message": "request completed", "trace_id": "tr-1103-003"},
    ],
}


class ElasticsearchMock:
    """Local fixture representing application logs indexed in Elasticsearch."""

    def search_application_logs(self, alert_id: str) -> list[dict]:
        return deepcopy(_APPLICATION_LOGS.get(alert_id, []))
