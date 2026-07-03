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

# 通用方法论 skill 的 canonical 真源 + 分发脚本。
# 构建时把 skills/skills-map.yaml 声明的 skill 物理复制进各 distribution/skills/
# （hermes profile install 接受真实目录、拒绝软连接），随后删除真源与脚本，
# 使镜像内每个 profile 自带 vendored skill，且不残留重复真源。
COPY --chown=hermes:hermes skills /opt/skills
COPY --chown=hermes:hermes scripts /opt/scripts

USER hermes

RUN /opt/hermes/.venv/bin/python /opt/scripts/sync-shared-skills.py \
    && rm -rf /opt/skills /opt/scripts

WORKDIR /opt/hermes
