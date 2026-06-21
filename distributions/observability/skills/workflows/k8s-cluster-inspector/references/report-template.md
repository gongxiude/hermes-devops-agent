# K8s 集群巡检报告模板

`k8s-cluster-inspector` 的标准报告模板。占位符 `{{...}}`，填充时删「示例」。
严格遵循 skill 约定：证据均来自 MCP；**No-evidence-no-healthy**；整改只写建议不执行。
字段（`risk_level`/`health_score`/`findings`/`evidence_gaps`/`diagnosis`/`next_human_action`）一一对应。

**风险图标**：🟢 healthy ｜ 🟡 warning ｜ 🔴 critical ｜ ⚪ unknown
**检查图标**：✅ 正常 ｜ ⚠️ 关注 ｜ ❌ 异常 ｜ 🚫 evidence_gap（无 MCP 数据）

---

## 一、飞书推送版（手机端友好，默认输出）

```
━━━━━━━━━━━━━━━━━━━━━━━━
☸️ K8s 集群巡检日报
🏷️ {{business}}（业务线，如 国际短信 / intlsms）
📅 {{date}}　🌐 {{cluster}} / {{environment}}
━━━━━━━━━━━━━━━━━━━━━━━━

📊 健康总览
· 风险 {{🟢|🟡|🔴|⚪}} {{risk_level}}　评分 {{health_score}}/100
· 覆盖 {{collected}}/{{expected}} 项　缺口 {{gap}} 项
· 窗口 {{cadence}}（{{time_range}}）

✅ 健康面
· {{节点 3/3 Ready · 0 重启 · 控制面正常}}
· {{CPU<3% · 内存<28% · 磁盘<23% · CoreDNS 0.6ms}}

🔴 P1 风险
· {{NetworkPolicy 全空（所有 ns 默认全通）}}

🟡 P2 待办
· {{6 工作负载无探针：dispatch/channel/deliver-worker…}}
· {{全部 prod 工作负载用 default ServiceAccount}}

📈 容量 & 异常（时序前瞻）
· 容量：{{磁盘约 N 天后达 80% / 根分区充足，无近期压力}}
· 配置：空闲率 {{X%}}（平均 req 利用率）· 简配 {{M}} 项可回收 {{≈N核/GGiB}}：{{top: worker-B(CPU 5%)、worker-D(mem 8%)}}；增配 {{K}} 项：{{worker-A(节流)}}；无 limit {{J}} 个
· 异常：{{检出 X 处偏离 baseline（如错误率同比放大）/ 无显著异常}}
· 前瞻风险：{{overall_risk，融合当前 + 趋势}}

🚫 数据缺口
· {{etcd WAL fsync（ACK 托管未暴露）}}
· {{PVC 容量（kubelet_volume_stats 未采集）}}

🛠️ 处置建议
· P0　{{无}}
· P1　{{为 prod 建 NetworkPolicy（默认拒入站）}}
· P2　{{补 TCP 探针 · ServiceAccount 独立化}}

━━━━━━━━━━━━━━━━━━━━━━━━
⏰ 下次巡检 {{next_run}}　🔗 {{trigger_id}}
━━━━━━━━━━━━━━━━━━━━━━━━
```

> 输出简洁清晰，适合飞书手机端阅读；某数据源失败不要中断，标 `evidence_gap` 后继续。
> **≤2000 字、单条投递**——完整 8 维度明细 + 证据放下面「完整版」存档 / comment，**不要塞进推送 summary**
> （>4000 字会被飞书拆成两条）。

---

## 二、完整版（存档 / Kanban）

```markdown
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
☸️ Kubernetes 集群巡检报告
🏷️ {{business}}（业务线，如 国际短信 / intlsms）
📅 {{collected_at}}　🌐 {{cluster}} / {{environment}}
🕐 {{cadence}} · 回看 {{time_range}}　🤖 k8s-cluster-inspector（只读·仅 MCP）
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📋 执行摘要（结论先行）
· 整体风险：{{🟢|🟡|🔴|⚪}} {{risk_level}}
· 健康评分：{{health_score}} / 100
· 一句话：{{基础设施健康；1 项 P1 + 2 项 P2 + 4 项 gap；无 P0}}
· 立即处理（P0）：{{N 项 / 无}}

📊 健康评分明细
| 等级 | 命中 | 扣分 | 小计 |
|---|---|---|---|
| 🔴 P0 | {{n}} | −30 | {{-}} |
| 🟠 P1 | {{n}} | −15 | {{-}} |
| 🟡 P2 | {{n}} | −5 | {{-}} |
| 🚫 gap | {{n}} | −5 | {{-}} |
| 总分 | | | {{health_score}} |
> ≥90 🟢 / 70–89 🟡 / <70 🔴；任一 P0 直接 🔴。

🔍 分维度结果（✅正常 ⚠️关注 ❌异常 🚫缺口）

🧭 控制面与核心组件
| 检查项 | 结果 | 实测 | 阈值 | 证据(MCP) |
|---|---|---|---|---|
| {{etcd 有主}} | ✅ | 1 | ==1 | prometheus `etcd_server_has_leader` |

🖥️ 节点健康
| 检查项 | 结果 | 实测 | 阈值 | 证据(MCP) |
|---|---|---|---|---|

📦 工作负载与 Pod
| 检查项 | 结果 | 实测 | 阈值 | 证据(MCP) |
|---|---|---|---|---|

💾 存储
| 检查项 | 结果 | 实测 | 阈值 | 证据(MCP) |
|---|---|---|---|---|

🌐 网络与服务
| 检查项 | 结果 | 实测 | 阈值 | 证据(MCP) |
|---|---|---|---|---|

⚙️ 配置巡检
| 检查项 | 结果 | 实测 | 阈值 | 证据(MCP) |
|---|---|---|---|---|

🔒 安全巡检
| 检查项 | 结果 | 实测 | 阈值 | 证据(MCP) |
|---|---|---|---|---|

🩺 探针配置审计
| 检查项 | 结果 | 实测 | 阈值 | 证据(MCP) |
|---|---|---|---|---|

📈 容量评估（时序外推，来自 capacity-forecast）
| 资源 | 当前 | 趋势 | 预测（达阈值） | 置信度 | 证据(MCP) |
|---|---|---|---|---|---|
| {{根分区}} | {{22%}} | {{平稳}} | {{>90 天 / 充足}} | {{中}} | prometheus `predict_linear(node_filesystem_avail_bytes…)` |

🧮 配置合理性 / Rightsizing（p95 over 7–30d vs requests/limits）

集群汇总：平均 request 利用率 {{X%}}　简配候选 {{M}}/{{总}} workload　可回收 {{≈N 核 / G GiB}}
Overcommit：CPU {{A%}} · 内存 {{B%}}（保守≤125% 激进≤150%）　无 limits 容器 {{K}} 个

| 工作负载 | 判定 | p95 用量 / request(limit) | 利用率 | 建议新值 | 证据(MCP) |
|---|---|---|---|---|---|
| {{示例 worker-A}} | 🔺 增配 | mem p95 94% of limit · CPU 节流 | 94% | limit 1Gi→1.5Gi | prometheus container_memory / cfs_throttled |
| {{示例 worker-B}} | 🔻 简配 | CPU p95 0.05 / req 1.0 | 5% | req 1.0→0.1 | prometheus container_cpu_usage |
| {{示例 worker-C}} | ⛔ 无 limit | CPU 高消耗无 limit（Top10） | — | 补 limit ≈ p99 | prometheus(unless limits) |

> 必须点名：分别列「简配候选」「增配候选」「无 limit Top10」，不许只写"配置合理/无问题"。

🚨 异常检测（偏离 baseline，来自 anomaly-detection）
| 指标 | 异常 | severity | baseline 对比 | 置信度 | 证据(MCP) |
|---|---|---|---|---|---|
| {{db-server 错误率}} | {{lock.init ~1/s}} | {{high}} | {{同比新增}} | {{高}} | loki `level=error` |

⚖️ 风险评估（来自 service-risk-summary）
· overall_risk：{{🟢|🟡|🔴}} {{融合当前 health_score + 前瞻容量/异常}}
· risk_factors：{{当前：配置债务；前瞻：容量充足、检出 1 处 high 异常}}

🩻 异常诊断（仅识别与建议，不执行）
| 对象 | 状态 | 归因 | 证据(MCP) | 建议 |
|---|---|---|---|---|
| {{ns/pod}} | {{Pending/CrashLoop…}} | {{根因}} | {{loki/events/yaml}} | {{文本建议}} |

🚫 证据缺口（evidence_gap）
| 检查项 | 缺失原因 | 建议采集途径 |
|---|---|---|
| {{etcd WAL fsync}} | {{ACK 托管未暴露}} | {{确认 metrics 暴露级别}} |
> 以上项未采集，不据此判 healthy；范围外项不降级到 SSH/exec。

🛠️ 处置建议（按优先级）
· 🔴 P0（立即）：{{… / 无}}
· 🟠 P1（当日）：{{… / 无}}
· 🟡 P2（计划）：{{… / 无}}

🧾 审计与元数据
· 自治级别：observe / recommend（只读，无变更）
· 数据源：{{MCP server 列表}}
· 脱敏：已经 secret-redaction（密钥/token/内网 IP → [REDACTED]）
· 覆盖率：{{X}}/{{Y}} 项　缺口 {{Z}} 项
· 追踪：{{trigger_id}}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```
