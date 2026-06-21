# 时序分析方法与 Prompt 模板（容量 / 异常 / 风险）

把 *LLM-powered time series analysis* 的方法落到本 skill。文章核心不是"喂原始数据让 LLM 端到端预测"，
而是 **结构化 prompt + 分阶段方法（识别 → 估计/投影 → 验证 → 量化 → 迭代）**。

**适配本 skill（MCP-only，只读）**：不训练 ARIMA/LSTM（无 code_execution）。数据经
`prometheus_query_range`（MCP）取得 → **降采样**后喂 LLM，让 LLM 按下面的分阶段法做趋势/异常/外推
推理；统计外推借 Prometheus `predict_linear`。

> **执行方式**：本分析由 `k8s-cluster-inspector` **经 `delegate_task` 并行批**运行——
> **容量评估 ∥ 异常检测** 两个 leaf 子 agent 并行（彼此独立）；**风险评估**依赖前两者结果，
> 由主 agent 在它们返回后 fan-in 综合（或再委派一次），**不与前两者并行**。
> 子 agent 用本文件的结构化 prompt 与分阶段法，**只回结构化 JSON**；主 agent 合入报告，
> 子结果不得直接当最终输出。

## 一、给 LLM 的结构化输入（每条序列都带齐）

文章强调用占位符把数据"描述清楚"而非裸喂。每条序列提供：

- **Dataset**：指标含义 + 业务背景（如 "root fs avail bytes · intlsms prod · node-A"）
- **Frequency / 采样**：降采样后的粒度（如 1 点/小时）
- **History / Horizon**：如 history 30d、forecast 7d
- **Known seasonality**：日周期 / 周周期（业务流量节律）
- **Data**：降采样样本 `[ts, value]`（按小时/天聚合，取 `max_over_time` / `quantile_over_time`）

## 二、分阶段方法（对每条关键序列）

1. **识别 (describe)**：趋势方向与斜率、季节性、是否平稳、有无 level shift / changepoint。
2. **投影 (project，容量)**：基于斜率 / `predict_linear` 外推到阈值 →「约 N 天后达 X%」。
3. **配置合理性 (rightsizing)**：按 **workload owner** 聚合，p95 用量 vs `requests`/`limits`——
   `用量/limit>0.8` 或节流 → **增配**；`p95/request<0.3` → **简配**（request 调到≈均值 85–115%，limit≈p99/max）。
   **必须点名 workload + 给可回收量**；另算集群 Overcommit（Σlimits/容量，保守≤125%）与无 limit Top10。
   ⚠️ 不许用「用量<X% limit→无问题」收尾——那正是过度配置。
4. **异常 (detect)**：与 baseline（`offset 1d/7d`）或分位带比较，标 spike / drift / 错误率放大；
   关注持续偏离、方差变化（文章的残差/诊断思路）。
5. **验证 (validate，文章重点)**：**walk-forward / 多预测起点**自检——用历史多个起点验证外推一致性，
   避免单点外推误导；时间序列切分**不打乱**。
6. **量化 (quantify)**：给 `confidence`（high/med/low）+ 误差直觉（近段 MAPE 量级）；不确定就降置信。
7. **迭代 (iterate)**：先粗后细（先基础趋势，再加季节性/变点）；**token 效率**——只喂降采样样本，
   不灌原始全分辨率序列。

## 三、Prompt 模板（容量 + 异常 + 风险一体）

```
## System
You are an SRE doing READ-ONLY time-series analysis for [business] [service] on Kubernetes.
Analyze the provided DOWNSAMPLED metric series. Project capacity, detect anomalies vs baseline,
and assess forward risk. Observe and recommend only — never propose scale/restart/rollback.
Method: identify → project → detect → walk-forward validate → quantify confidence → iterate.

## User
Metric: [name + 含义]
Business / Env: [business] / [environment]
Frequency: [如 1/h]   History: [window]   Forecast horizon: [horizon]
Known seasonality: [日 / 周 / 无]
Baseline series (offset [1d|7d]): [downsampled samples]
Current series: [downsampled samples]

Provided also: requests/limits/replicas for each workload, and p95 usage over [history_window].

Do:
1. Trend, seasonality, changepoints (level shift / drift).
2. Capacity projection to threshold: ~N days to X%, with method (slope/predict_linear) + confidence.
3. Rightsizing: compare p95 usage vs requests/limits/replicas →
   under-provisioned (near/over limit, throttled) → recommend SCALE-UP;
   long-idle (p95 << request, e.g. <30%) → recommend SCALE-DOWN; otherwise keep.
4. Anomalies vs baseline: spike / drift / error-rate amplification, each with severity + confidence.
5. Walk-forward sanity check across ≥3 historical origins; flag if projections disagree.
6. Forward risk (overall) + recommended human actions (text only).

Return JSON:
{ "trend": "...", "projection": {"days_to_threshold": N, "confidence": "high|med|low"},
  "rightsizing": [{"workload":"...","verdict":"scale_up|scale_down|keep","reason":"p95 vs req/limit","evidence":"..."}],
  "anomalies": [{"signal":"...","severity":"critical|high|med","confidence":"..."}],
  "risk": "healthy|warning|critical", "actions": ["..."] }

If history insufficient or metric not collected → set evidence_gap, do NOT fabricate.
```

## 四、与三个能力 skill 的关系

本文件是 `capacity-forecast`（投影/瓶颈）与 `anomaly-detection`（偏离 baseline 分类）的**时序内核**：
它们的结构化 prompt 套用本模板，数据源固定为 `prometheus_query_range`（MCP），不引外部建模库；
`service-risk-summary` 消费本分析的 `risk` + `projection` 做前瞻风险聚合。

## 五、注意

- **No-evidence-no-fabrication**：历史不足 / 指标未采集 → `evidence_gap`，不臆造预测。
- **绝对时间戳**：`prometheus_query_range` 的 start/end 用绝对 Unix 秒（相对值 HTTP 400）。
- **只观察**：所有结论是建议文本，受 skill 的 Hard Denies 约束。
