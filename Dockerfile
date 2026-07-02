FROM yuexinhub-registry.cn-zhangjiakou.cr.aliyuncs.com/yuexin_devops/hermes-agent-base:v2026.6.19-tools

#checkov:skip=CKV_DOCKER_2:Hermes gateway health checks are defined by Kubernetes workloads.
USER root

RUN curl -fsSLo /tmp/aliyun-cli-linux-latest-amd64.tgz \
    https://aliyuncli.alicdn.com/aliyun-cli-linux-latest-amd64.tgz \
    && tar -xzf /tmp/aliyun-cli-linux-latest-amd64.tgz -C /tmp \
    && install -m 0755 /tmp/aliyun /usr/local/bin/aliyun \
    && rm -f /tmp/aliyun /tmp/aliyun-cli-linux-latest-amd64.tgz

RUN uv pip install --python /opt/hermes/.venv/bin/python \
    --default-index https://pypi.tuna.tsinghua.edu.cn/simple \
    --no-cache-dir \
    lark-oapi \
    fastmcp

COPY --chown=hermes:hermes plugins /opt/hermes/plugins

COPY --chown=hermes:hermes mcp-servers /opt/mcp-servers

COPY --chown=hermes:hermes distributions /opt/distributions

USER hermes

WORKDIR /opt/hermes
