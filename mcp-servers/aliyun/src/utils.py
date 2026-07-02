from __future__ import annotations

import json
import os
import subprocess


class Config:
    SERVER_NAME = os.getenv("MCP_SERVER_NAME", "aliyun")
    SERVER_VERSION = "1.0.0"
    LOG_LEVEL = os.getenv("MCP_LOG_LEVEL", "INFO")
    REQUEST_TIMEOUT = int(os.getenv("MCP_REQUEST_TIMEOUT", "30"))
    ALIYUN_BIN = os.getenv("ALIYUN_BIN", "aliyun")
    ALIYUN_PROFILE = os.getenv("ALIYUN_PROFILE", "").strip()
    ALIYUN_REGION = os.getenv("ALIYUN_REGION", "").strip()


def run_aliyun(*args: str) -> dict:
    cmd = [Config.ALIYUN_BIN]
    if Config.ALIYUN_PROFILE:
        cmd.extend(["--profile", Config.ALIYUN_PROFILE])
    cmd.extend(args)
    cmd.extend(["--output", "json"])
    env = os.environ.copy()
    if os.getenv("ALIYUN_ACCESS_KEY_ID") and not env.get("ALIBABA_CLOUD_ACCESS_KEY_ID"):
        env["ALIBABA_CLOUD_ACCESS_KEY_ID"] = os.getenv("ALIYUN_ACCESS_KEY_ID", "")
    if os.getenv("ALIYUN_ACCESS_KEY_SECRET") and not env.get("ALIBABA_CLOUD_ACCESS_KEY_SECRET"):
        env["ALIBABA_CLOUD_ACCESS_KEY_SECRET"] = os.getenv("ALIYUN_ACCESS_KEY_SECRET", "")
    result = subprocess.run(
        cmd,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=Config.REQUEST_TIMEOUT,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or f"aliyun exited {result.returncode}")
    return json.loads(result.stdout)
