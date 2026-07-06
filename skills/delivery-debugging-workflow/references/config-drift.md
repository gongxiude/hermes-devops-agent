# Config Drift

配置漂移诊断顺序：

1. refresh GitOps 仓库。
2. 渲染目标 overlay。
3. 采集运行态只读资源。
4. 对比 `apiVersion/kind/name/namespace/spec`。
5. 区分 expected drift、runtime-only fields 和实际配置漂移。

输出必须包含漂移字段、Git 来源文件、运行态证据和建议动作。
