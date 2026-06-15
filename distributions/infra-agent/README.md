# infra-agent

Infrastructure agent for Alibaba Cloud resource inspection, K8s cluster analysis,
network topology, security compliance, and cost optimization.

## Install

```bash
hermes profile install distributions/infra-agent
```

## Setup

```bash
cp .env.EXAMPLE .env
# Fill in ALIYUN_ACCESS_KEY_ID and ALIYUN_ACCESS_KEY_SECRET
# Optionally set KUBECONFIG_READONLY for ACK cluster access
```

## Usage

```bash
hermes -p infra-agent chat -q "巡检阿里云杭州 region 的 ECS 资源容量"
hermes -p infra-agent chat -q "检查 ACK 集群健康状态"
hermes -p infra-agent chat -q "审计 RAM 权限合规性"
hermes -p infra-agent chat -q "分析本月云资源成本"
```