FROM yuexinhub-registry.cn-zhangjiakou.cr.aliyuncs.com/yuexin_devops/hermes-agent-base:v2026.6.19-tools

#checkov:skip=CKV_DOCKER_2:Hermes gateway health checks are defined by Kubernetes workloads.
USER root

COPY --chown=hermes:hermes plugins /opt/hermes/plugins

COPY --chown=hermes:hermes distributions /opt/distributions

USER hermes

WORKDIR /opt/hermes
