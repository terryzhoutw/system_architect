"""Generate deterministic, realistic-looking synthetic RAG examples.

All identities, systems, IPs, measurements, and events are fictional. The IPs
come from documentation-only ranges. This is not production or government data.
"""

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "knowledge" / "samples"
COUNT_PER_SCENARIO = 100

APIS = [
    ("/v1/permit/query", "许可服务", "许可服务组"),
    ("/v1/benefit/query", "福利服务", "福利服务组"),
    ("/v1/certificate/verify", "证书核验服务", "证书服务组"),
    ("/v1/person/search", "人口信息服务", "数据服务组"),
    ("/v1/company/registry", "企业登记服务", "企业服务组"),
    ("/v1/identity/token/verify", "身份认证服务", "身份平台组"),
    ("/v1/license/status", "电子证照服务", "证照服务组"),
    ("/v1/organization/detail", "组织信息服务", "基础数据组"),
    ("/v1/social/record/query", "社保查询服务", "社保服务组"),
    ("/v1/health/record/query", "健康信息服务", "健康数据组"),
]

JWT_ERRORS = [
    ("kid_not_found", "疑似签名密钥轮换后网关缓存未刷新"),
    ("issuer_mismatch", "Token 签发方与服务端配置不一致"),
    ("audience_mismatch", "Token audience 与 API 受众配置不一致"),
    ("token_expired", "请求使用的 Token 已过期，需核对客户端刷新逻辑"),
    ("jwks_fetch_timeout", "验证组件获取 JWKS 超时，需检查 SSO 可达性"),
    ("clock_skew_exceeded", "服务端与签发端时钟偏差超过允许范围"),
    ("signature_invalid", "签名校验失败，需核对公钥版本和签名算法配置"),
    ("claim_missing", "Token 缺少策略要求的身份声明"),
    ("client_secret_rotated", "客户端密钥变更可能未同步到调用方"),
    ("token_format_invalid", "调用方发送的 Token 格式不符合约定"),
]

TRAFFIC_PATTERNS = [
    ("重复分页游标", "相同分页游标被连续请求，可能是客户端重试或自动化遍历"),
    ("单客户端高频轮询", "请求集中在单一客户端，时间间隔接近固定周期"),
    ("多来源集中访问", "多个来源在短时间内访问同一查询接口"),
    ("业务批处理待确认", "请求时间接近批量作业窗口，但没有查到作业确认记录"),
    ("低错误率突增", "成功请求比例较高，仍需核对业务活动和授权身份"),
    ("限流后持续请求", "触发 429 后客户端仍持续重试"),
    ("参数组合重复", "多个请求使用高度相似的查询条件"),
    ("用户分布异常", "调用用户分布与近期基线不同"),
    ("网关重试放大", "入口重试可能放大了下游请求量"),
    ("定时任务可能重叠", "请求出现周期性峰值，需确认调度任务是否重复运行"),
]

LATENCY_ERRORS = [
    ("upstream_connect_timeout", "下游连接建立超时"),
    ("connection_pool_wait", "连接池等待时间升高"),
    ("slow_dependency_call", "依赖服务调用耗时升高"),
    ("thread_pool_rejected", "业务线程池出现拒绝记录"),
    ("database_query_slow", "日志记录到慢查询，需结合数据库指标确认"),
    ("gc_pause_observed", "出现较长 GC 暂停，需结合 JVM 指标确认影响"),
    ("downstream_5xx", "下游服务返回 5xx"),
    ("dns_resolution_delay", "下游域名解析耗时异常"),
    ("retry_amplification", "重试次数增加，可能放大请求耗时"),
    ("rate_limit_queueing", "下游限流导致请求排队"),
]

SCAN_PATHS = [
    ("/.env", 404, "未发现成功访问证据"),
    ("/swagger-ui/index.html", 404, "未发现成功访问证据"),
    ("/actuator/env", 403, "访问被拒绝；仍需确认拒绝策略和日志完整性"),
    ("/admin/login", 404, "未发现成功访问证据"),
    ("/v2/api-docs", 401, "需要认证；未发现成功访问证据"),
    ("/server-status", 404, "未发现成功访问证据"),
    ("/config.yml", 404, "未发现成功访问证据"),
    ("/debug/vars", 403, "访问被拒绝；仍需确认拒绝策略和日志完整性"),
    ("/wp-admin", 404, "未发现成功访问证据"),
    ("/api/internal/health", 200, "命中可访问路径；需核实该健康接口是否暴露敏感信息"),
]

PII_FIELDS = [
    ("idCardNo", "身份证号字段名"),
    ("mobile", "手机号字段名"),
    ("address", "住址字段名"),
    ("bankAccount", "银行账号字段名"),
    ("personalEmail", "个人邮箱字段名"),
    ("birthDate", "出生日期字段名"),
    ("faceImageUrl", "人脸图像链接字段名"),
    ("householdId", "家庭关联标识字段名"),
    ("healthRecordNo", "健康档案编号字段名"),
    ("licenseHolder", "证照持有人字段名"),
]

CERT_TARGETS = [
    ("api-gateway", "APISIX 网关证书"),
    ("sso-portal", "SSO 登录入口证书"),
    ("permit-service", "许可服务上游证书"),
    ("data-exchange", "数据交换域名证书"),
    ("benefit-api", "福利服务 API 证书"),
    ("certificate-service", "证书核验服务证书"),
    ("organization-api", "组织信息服务证书"),
    ("health-api", "健康数据服务证书"),
    ("registry-api", "企业登记服务证书"),
    ("identity-api", "身份认证服务证书"),
]

RUNBOOK_QA = [
    ("JWT 出现 kid_not_found 时先查什么？", "核对 Token 的 kid、SSO 当前 JWKS 密钥版本、APISIX 或验签组件的公钥缓存刷新状态，并关联密钥轮换时间。"),
    ("issuer_mismatch 如何排查？", "对比 Token 的 iss 声明与服务端允许的 issuer 配置，检查环境配置是否串用，并关联近期配置发布记录。"),
    ("接口请求量突增能直接判定攻击吗？", "不能。应结合调用身份、请求参数重复度、来源分布、业务活动、历史基线、错误率和限流情况综合判断。"),
    ("慢请求如何判断是不是下游依赖问题？", "先按 trace_id 拆分各段耗时，再关联下游服务错误率、连接池、线程池和近期变更；单条超时日志不足以确认根因。"),
    ("路径扫描告警如何判断是否造成影响？", "核对扫描路径是否命中真实 API、响应状态、认证是否成功、响应大小和敏感字段审计；大量 404 只能说明探测行为，不能证明数据泄露。"),
    ("日志里出现身份证字段名意味着泄露吗？", "不能仅凭字段名确认。应在授权审计流程下核对接口字段定义、脱敏情况、响应范围和调用权限，避免在分析结果中输出原始个人信息。"),
    ("证书到期前应怎么安排？", "确认资产和责任人、续期窗口、证书链和域名；先在测试环境验证，再按审批流程变更并回查 APISIX/服务实例加载状态。"),
    ("Prometheus 和 ES 分别用于什么排查？", "Prometheus 查询服务器及中间件 exporter 指标趋势；ES 查询应用日志和 trace_id 关联记录。两类证据按服务、实例和时间窗关联。"),
    ("出现 401 和 CPU 正常能说明什么？", "说明当前样本中主机资源压力不是明显伴随信号，但不能据此确定 SSO/JWT 根因；还需检查验签错误和密钥/配置状态。"),
    ("没有查到处置手册怎么办？", "应说明知识库未找到匹配依据，列出当前可确认的业务/监控证据，并转人工核查；不要让模型补写未引用的操作规范。"),
]


def doc_id(scenario: str, index: int) -> str:
    return f"SYN-{scenario.upper()}-{index:03d}"


def ip_for(index: int) -> str:
    # RFC 5737 documentation-only addresses; no production host is represented.
    blocks = [(192, 0, 2), (198, 51, 100), (203, 0, 113)]
    a, b, c = blocks[(index // 240) % len(blocks)]
    return f"{a}.{b}.{c}.{(index % 240) + 1}"


def timestamp(index: int, hour: int = 14) -> str:
    day = 1 + (index % 27)
    minute = (index * 7) % 60
    second = (index * 13) % 60
    return f"2026-10-{day:02d}T{hour:02d}:{minute:02d}:{second:02d}+08:00"


def base_record(scenario: str, name: str, index: int, api: tuple[str, str, str]) -> dict:
    path, system, owner = api
    return {
        "id": doc_id(scenario, index),
        "scenario_id": scenario,
        "scenario_name": name,
        "record_type": "synthetic_case",
        "title": "",
        "source_name": f"脱敏模拟案例集/{name}",
        "source_version": "demo-v1",
        "effective_from": "2026-01-01",
        "department_scope": owner,
        "security_level": "内部模拟",
        "api_path": path,
        "system_name": system,
        "user_query": "",
        "content": "",
        "reference_conclusion": "",
        "recommended_actions": [],
        "synthetic": True,
        "data_warning": "完全合成的演示数据；不含真实政府业务数据、个人信息、域名或生产日志。",
    }


def jwt_case(i: int) -> dict:
    api = APIS[i % len(APIS)]
    code, cause = JWT_ERRORS[i % len(JWT_ERRORS)]
    ratio = 42 + ((i * 11) % 39)
    clients = 1 + (i % 6)
    t = timestamp(i, 14)
    r = base_record("jwt_401", "401与SSO_JWT验签异常", i, api)
    r.update({
        "title": f"JWT 验签失败案例 {i + 1:03d}",
        "user_query": f"{api[0]} 在 {t[11:16]} 出现 401 激增，日志有 {code}，应先检查什么？",
        "content": (f"{t}，{api[1]} 接口 {api[0]} 的 401 比例由 2% 升至 {ratio}%，影响 {clients} 个调用客户端。"
                    f"ES 应用日志出现 {code}。Prometheus 中 APISIX 5xx 为 0.4%，网关主机 CPU 为 {35 + i % 35}%，"
                    f"JVM 堆使用率为 {45 + i % 30}%。这组证据更支持验签配置、密钥同步或客户端 Token 问题；"
                    f"Prometheus 资源指标未显示明显主机压力。线索：{cause}。需核对 SSO 变更和实际 Token 声明后才能确认根因。"),
        "reference_conclusion": f"401 激增伴随 {code}；优先核对对应的 JWT/SSO 配置线索，尚不能仅凭该样本确认根因。",
        "recommended_actions": ["核对 Token 的 kid、iss、aud 和 exp（仅在授权环境读取必要声明）", "关联 SSO/JWKS 密钥轮换记录", "检查 APISIX/验签组件公钥缓存", "按调用客户端和时间窗比较错误比例"],
        "metric_facts": {"http_401_ratio_percent": ratio, "client_count": clients, "gateway_5xx_percent": 0.4, "host_cpu_percent": 35 + i % 35},
        "log_facts": {"error_code": code, "time": t, "client_ip": ip_for(i)},
    })
    return r


def traffic_case(i: int) -> dict:
    api = APIS[(i + 1) % len(APIS)]
    label, pattern = TRAFFIC_PATTERNS[i % len(TRAFFIC_PATTERNS)]
    multiplier = round(3.0 + (i % 51) / 10, 1)
    sources = 1 + (i * 3 % 90)
    t = timestamp(i, 10)
    r = base_record("traffic_spike", "API异常流量", i, api)
    r.update({
        "title": f"API 请求量突增案例 {i + 1:03d}",
        "user_query": f"{api[0]} 在 {t[11:16]} 请求量达到基线 {multiplier} 倍，是否属于攻击？",
        "content": (f"{t}，{api[1]} 接口 {api[0]} 的 Prometheus 请求速率约为近期基线 {multiplier} 倍，"
                    f"来源数约 {sources}。ES 应用日志特征为“{label}”：{pattern}。"
                    f"样本中 2xx 比例为 {70 + i % 25}%，429 比例为 {i % 12}%；node-exporter CPU 为 {45 + i % 48}%。"
                    f"应关联 SSO 调用身份、业务批次/活动记录和历史基线。请求量增高本身不足以认定攻击，也不应自动封禁。"),
        "reference_conclusion": f"存在流量异常，表现为{label}；结合授权身份与业务活动进一步研判，当前不能单凭 QPS 确认攻击。",
        "recommended_actions": ["核对调用客户端、用户和组织授权", "检查请求参数重复度与固定轮询周期", "向业务负责人确认批量任务或活动", "与历史同时间段基线对比", "按审批流程决定是否调整限流"],
        "metric_facts": {"request_rate_ratio": multiplier, "source_count": sources, "cpu_percent": 45 + i % 48},
        "log_facts": {"pattern": label, "sample_source_ip": ip_for(i + 100), "time": t},
    })
    return r


def latency_case(i: int) -> dict:
    api = APIS[(i + 2) % len(APIS)]
    code, clue = LATENCY_ERRORS[i % len(LATENCY_ERRORS)]
    p95 = 1500 + (i * 173 % 5200)
    err = 5 + (i * 7 % 21)
    t = timestamp(i, 11)
    r = base_record("latency_5xx", "慢请求与5xx", i, api)
    r.update({
        "title": f"接口慢请求与 5xx 案例 {i + 1:03d}",
        "user_query": f"{api[0]} P95 达到 {p95}ms、5xx 为 {err}%，怎样定位？",
        "content": (f"{t}，{api[1]} 接口 {api[0]} 的 Prometheus APISIX 上游 P95 为 {p95}ms，"
                    f"上游 5xx 比例为 {err}%。jmx-exporter 堆使用率为 {50 + i % 40}%，"
                    f"node-exporter CPU 为 {40 + i % 55}%。ES 应用日志出现 {code}（{clue}）。"
                    f"需使用 trace_id 拆分入口、业务服务和下游耗时，再关联线程池、连接池、依赖实例及变更记录。"
                    f"单条日志不能单独确认根因。"),
        "reference_conclusion": f"接口性能异常；ES 出现 {code}，Prometheus 上游 P95/5xx 同步异常，应先定位对应依赖链路。",
        "recommended_actions": ["按 trace_id 拆分各服务耗时", "查看下游服务实例和错误率", "核对 JVM、线程池、连接池指标", "关联告警前后发布与配置变更", "观察恢复后 P95 和 5xx 是否同步回落"],
        "metric_facts": {"upstream_p95_ms": p95, "upstream_5xx_percent": err, "jvm_heap_percent": 50 + i % 40},
        "log_facts": {"error_code": code, "time": t, "trace_id": f"tr-lat-{i + 1:04d}"},
    })
    return r


def scan_case(i: int) -> dict:
    api = APIS[(i + 3) % len(APIS)]
    path, status, impact = SCAN_PATHS[i % len(SCAN_PATHS)]
    paths = 80 + (i * 17 % 950)
    auth_success = (i % 10 == 9)
    t = timestamp(i, 9)
    r = base_record("path_scan", "路径扫描与探测", i, api)
    r.update({
        "title": f"API 路径探测案例 {i + 1:03d}",
        "user_query": f"来源 {ip_for(i + 400)} 在短时间内探测 {paths} 个路径，其中 {path} 返回 {status}，是否有影响？",
        "content": (f"{t}，ES 应用日志记录来源 {ip_for(i + 400)} 在 3 分钟内请求 {paths} 个不同路径，"
                    f"示例路径 {path} 返回 HTTP {status}；{impact}。认证成功记录：{'发现一条需核查的成功认证' if auth_success else '未发现'}。"
                    f"Prometheus APISIX 指标应补充同窗口请求速率、状态码分布和上游响应情况。"
                    f"需检查是否命中已登记 API、响应体大小和敏感数据审计；扫描特征不等于数据已泄露。"),
        "reference_conclusion": f"存在路径探测特征；示例路径返回 {status}。是否造成影响需核查真实 API 命中、认证和响应证据。",
        "recommended_actions": ["核对探测路径与登记 API 资产", "检查 2xx 路径的响应和敏感字段审计", "关联认证成功事件及后续 API 调用", "按现有安全流程评估封禁或取证"],
        "metric_facts": {"distinct_paths_3m": paths, "sampled_path_status": status},
        "log_facts": {"sample_path": path, "source_ip": ip_for(i + 400), "auth_success_seen": auth_success},
    })
    return r


def pii_case(i: int) -> dict:
    api = APIS[(i + 4) % len(APIS)]
    field, field_label = PII_FIELDS[i % len(PII_FIELDS)]
    size_ratio = round(1.5 + (i % 45) / 10, 1)
    t = timestamp(i, 13)
    r = base_record("pii_exposure", "个人信息返回风险", i, api)
    r.update({
        "title": f"个人信息字段暴露核查案例 {i + 1:03d}",
        "user_query": f"{api[0]} 日志出现字段 {field} 且响应体增大 {size_ratio} 倍，是否能认定泄露？",
        "content": (f"{t}，ES 脱敏应用日志出现字段名 {field}（{field_label}），Prometheus/APISIX 观测到"
                    f"响应体大小约为基线 {size_ratio} 倍。接口资产标记为个人信息相关接口，允许字段范围需从业务接口定义核实。"
                    f"当前样例不包含该字段的真实值，也没有未经授权的原始响应体。仅凭字段名和响应大小不能确认泄露。"
                    f"应在授权审计流程下核对字段范围、脱敏规则、调用身份和查询条件。"),
        "reference_conclusion": f"存在个人信息超范围返回的核查必要；当前证据仅确认出现字段名 {field}，不足以认定实际泄露。",
        "recommended_actions": ["核对接口允许返回字段和数据最小化规则", "在授权审计下验证脱敏效果", "核实调用身份、组织和查询范围", "保存审计证据并按隐私事件流程升级"],
        "metric_facts": {"response_size_ratio": size_ratio},
        "log_facts": {"field_name": field, "raw_value_included": False, "time": t},
    })
    return r


def cert_case(i: int) -> dict:
    target, label = CERT_TARGETS[i % len(CERT_TARGETS)]
    days = 1 + (i * 7 % 30)
    api = APIS[(i + 5) % len(APIS)]
    expiry = (datetime(2026, 10, 22, tzinfo=timezone.utc) + timedelta(days=days)).date().isoformat()
    r = base_record("cert_expiry", "证书与密钥到期", i, api)
    r.update({
        "title": f"证书到期影响分析案例 {i + 1:03d}",
        "user_query": f"{label}将在 {days} 天后到期，影响什么服务，续期前要检查什么？",
        "content": (f"资产登记中 {target}（{label}）的模拟到期日为 {expiry}，距离样例基准日 2026-10-22 还有 {days} 天。"
                    f"关联系统为 {api[1]}，责任组为 {api[2]}。应通过资产目录确认绑定域名、证书链、关联 API 和实际责任人；"
                    f"续期后先在测试环境验证，再按既有变更审批更新网关或服务实例并回查加载状态。"
                    f"该记录不代表已创建真实证书或实际通知任务。"),
        "reference_conclusion": f"该模拟证书在 {days} 天内到期，应优先核实资产绑定关系和责任人，并按审批流程安排续期验证。",
        "recommended_actions": ["确认资产目录和域名绑定关系", "核对证书链、私钥保管和责任人", "安排测试环境续期验证", "按审批流程更新 APISIX/服务实例", "变更后回查证书加载与接口健康"],
        "metric_facts": {"days_to_expiry": days, "expiry_date": expiry},
        "log_facts": {"target_id": target, "renewal_event_found": False},
    })
    return r


def qa_case(i: int) -> dict:
    question, answer = RUNBOOK_QA[i % len(RUNBOOK_QA)]
    r = base_record("runbook_qa", "处置手册知识问答", i, APIS[i % len(APIS)])
    r.update({
        "title": f"运维知识问答样例 {i + 1:03d}",
        "record_type": "synthetic_qa_example",
        "source_name": "脱敏模拟知识问答集/运维处置",
        "source_version": "demo-v1",
        "user_query": question,
        "content": (f"问题：{question}\n参考处置说明：{answer}\n"
                    f"适用范围：政务 API 安全运营学习 Demo。执行前应核对本单位有效制度、实际配置和审批流程。"),
        "reference_conclusion": answer,
        "recommended_actions": [answer],
        "knowledge_topic": ["JWT/SSO", "异常流量", "慢请求", "路径扫描", "个人信息", "证书", "监控数据源"][i % 7],
    })
    return r


SCENARIOS = [
    ("jwt_401", "401与SSO/JWT异常", jwt_case),
    ("traffic_spike", "API异常流量", traffic_case),
    ("latency_5xx", "慢请求与5xx", latency_case),
    ("path_scan", "路径扫描与探测", scan_case),
    ("pii_exposure", "个人信息返回风险", pii_case),
    ("cert_expiry", "证书与密钥到期", cert_case),
    ("runbook_qa", "处置手册知识问答", qa_case),
]


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    manifest = []
    for scenario_id, scenario_name, factory in SCENARIOS:
        path = OUT / f"{scenario_id}.jsonl"
        records = [factory(index) for index in range(COUNT_PER_SCENARIO)]
        with path.open("w", encoding="utf-8", newline="\n") as f:
            for record in records:
                f.write(json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n")
        manifest.append({"scenario_id": scenario_id, "scenario_name": scenario_name, "count": len(records), "file": path.name})
        print(f"{path.name}: {len(records)} records")
    manifest_path = OUT / "manifest.json"
    manifest_path.write_text(json.dumps({
        "dataset": "government-api-agent-synthetic-demo-v1",
        "generated_at": "2026-10-22",
        "synthetic": True,
        "total_records": sum(item["count"] for item in manifest),
        "scenarios": manifest,
        "warning": "All records are generated examples, not production or government source data.",
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"manifest.json: {sum(item['count'] for item in manifest)} total records")


if __name__ == "__main__":
    main()
