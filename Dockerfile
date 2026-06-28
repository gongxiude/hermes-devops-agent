FROM nousresearch/hermes-agent:0.8.0

USER root

ARG KUBECTL_VERSION=v1.30.3

COPY plugins /opt/hermes/plugins

RUN python3 -m pip install --no-cache-dir "nemoguardrails>=0.9.0" \
 && python3 - <<'PY'
import os
import platform
import stat
import urllib.request

arch_map = {
    "x86_64": "amd64",
    "amd64": "amd64",
    "aarch64": "arm64",
    "arm64": "arm64",
}

arch = platform.machine().lower()
kubectl_arch = arch_map.get(arch)
if not kubectl_arch:
    raise SystemExit(f"unsupported architecture for kubectl download: {arch}")

version = os.environ["KUBECTL_VERSION"]
url = f"https://dl.k8s.io/release/{version}/bin/linux/{kubectl_arch}/kubectl"
target = "/usr/local/bin/kubectl"

with urllib.request.urlopen(url) as response, open(target, "wb") as fh:
    fh.write(response.read())

os.chmod(target, stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR | stat.S_IRGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH)
PY

ENV PYTHONPATH=/opt/hermes/plugins

WORKDIR /opt/hermes
