#!/usr/bin/env python3
from __future__ import annotations

import logging
from typing import Annotated

from fastmcp import FastMCP

from utils import Config, run_aliyun

logging.basicConfig(
    level=getattr(logging, Config.LOG_LEVEL),
    format="%(asctime)s %(name)s %(levelname)s %(message)s",
)

mcp = FastMCP(name=Config.SERVER_NAME, version=Config.SERVER_VERSION)


@mcp.tool
def aliyun_ecs_describe_instances(
    region_id: Annotated[str, "Region ID"] = "",
    instance_name: Annotated[str, "Optional instance name"] = "",
    status: Annotated[str, "Optional instance status"] = "",
    page_size: Annotated[int, "Page size"] = 20,
) -> dict:
    args = ["ecs", "DescribeInstances"]
    region = region_id or Config.ALIYUN_REGION
    if region:
        args.extend(["--RegionId", region])
    if instance_name:
        args.extend(["--InstanceName", instance_name])
    if status:
        args.extend(["--Status", status])
    args.extend(["--PageSize", str(page_size)])
    return run_aliyun(*args)


@mcp.tool
def aliyun_ecs_describe_instance_types(
    region_id: Annotated[str, "Region ID"] = "",
    zone_id: Annotated[str, "Optional zone ID"] = "",
    instance_type_family: Annotated[str, "Optional instance family"] = "",
) -> dict:
    args = ["ecs", "DescribeInstanceTypes"]
    region = region_id or Config.ALIYUN_REGION
    if region:
        args.extend(["--RegionId", region])
    if zone_id:
        args.extend(["--ZoneId", zone_id])
    if instance_type_family:
        args.extend(["--InstanceTypeFamily", instance_type_family])
    return run_aliyun(*args)


@mcp.tool
def aliyun_cms_describe_metric_last(
    namespace: Annotated[str, "Metric namespace"],
    metric_name: Annotated[str, "Metric name"],
    dimensions: Annotated[str, "Dimensions JSON string"],
    region_id: Annotated[str, "Region ID"] = "",
) -> dict:
    args = ["cms", "DescribeMetricLast", "--Namespace", namespace, "--MetricName", metric_name, "--Dimensions", dimensions]
    region = region_id or Config.ALIYUN_REGION
    if region:
        args.extend(["--RegionId", region])
    return run_aliyun(*args)


@mcp.tool
def aliyun_cms_describe_metric_list(
    namespace: Annotated[str, "Metric namespace"],
    metric_name: Annotated[str, "Metric name"],
    start_time: Annotated[str, "Start time RFC3339"],
    end_time: Annotated[str, "End time RFC3339"],
    dimensions: Annotated[str, "Dimensions JSON string"],
    period: Annotated[str, "Metric period"] = "60",
    region_id: Annotated[str, "Region ID"] = "",
) -> dict:
    args = [
        "cms",
        "DescribeMetricList",
        "--Namespace",
        namespace,
        "--MetricName",
        metric_name,
        "--StartTime",
        start_time,
        "--EndTime",
        end_time,
        "--Dimensions",
        dimensions,
        "--Period",
        period,
    ]
    region = region_id or Config.ALIYUN_REGION
    if region:
        args.extend(["--RegionId", region])
    return run_aliyun(*args)


if __name__ == "__main__":
    import argparse
    import sys

    parser = argparse.ArgumentParser(description="Aliyun FastMCP server (stdio)")
    parser.add_argument("--test", action="store_true")
    args = parser.parse_args()
    if args.test:
        print(f"Server  : {Config.SERVER_NAME} v{Config.SERVER_VERSION}")
        print(f"CLI     : {Config.ALIYUN_BIN}")
        print(f"Profile : {Config.ALIYUN_PROFILE or '(default)'}")
        print(f"Region  : {Config.ALIYUN_REGION or '(not set)'}")
        print("Tools   : 4")
        print("Status  : OK")
        sys.exit(0)
    mcp.run()
