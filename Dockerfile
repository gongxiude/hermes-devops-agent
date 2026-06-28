FROM yuexinhub-registry.cn-zhangjiakou.cr.aliyuncs.com/yuexin_devops/hermes-agent-base:v2026.6.19-tools

#checkov:skip=CKV_DOCKER_2:Hermes gateway health checks are defined by Kubernetes workloads.
USER root

COPY plugins /opt/hermes/plugins

RUN uv pip install --python /opt/hermes/.venv/bin/python3 --no-cache "nemoguardrails>=0.9.0"

USER hermes

ENV PYTHONPATH=/opt/hermes/plugins

WORKDIR /opt/hermes
