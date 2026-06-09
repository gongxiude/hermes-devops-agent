"""Read-only Kubernetes query tools."""
from __future__ import annotations

from typing import Annotated

from ..utils import run_kubectl, run_kubectl_json, ok, ok_json


def k8s_get_resources(
    resource_type: Annotated[str, "Type of resource (pod, service, deployment, etc.)"],
    resource_name: Annotated[str, "Name of specific resource (optional)"] = "",
    namespace: Annotated[str, "Namespace to query (optional, omit for current context)"] = "",
    all_namespaces: Annotated[bool, "Query all namespaces"] = False,
    output: Annotated[str, "Output format: json, yaml, wide (default: wide)"] = "wide",
) -> dict:
    """Get Kubernetes resources using kubectl get."""
    args = ["get", resource_type]
    if resource_name:
        args.append(resource_name)
    if all_namespaces:
        args.append("--all-namespaces")
    elif namespace:
        args += ["-n", namespace]
    args += ["-o", output or "wide"]
    return ok(run_kubectl(*args))


def k8s_get_pod_logs(
    pod_name: Annotated[str, "Name of the pod"],
    namespace: Annotated[str, "Namespace of the pod"] = "default",
    container: Annotated[str, "Container name (for multi-container pods)"] = "",
    tail_lines: Annotated[int, "Number of lines from the end (default: 50)"] = 50,
) -> dict:
    """Get logs from a Kubernetes pod."""
    args = ["logs", pod_name, "-n", namespace]
    if container:
        args += ["-c", container]
    if tail_lines > 0:
        args += ["--tail", str(tail_lines)]
    return ok(run_kubectl(*args))


def k8s_get_events(
    namespace: Annotated[str, "Namespace to get events from (omit for all namespaces)"] = "",
) -> dict:
    """Get events from a Kubernetes namespace."""
    args = ["get", "events", "-o", "json"]
    if namespace:
        args += ["-n", namespace]
    else:
        args.append("--all-namespaces")
    return ok_json(run_kubectl_json(*args))


def k8s_get_available_api_resources() -> dict:
    """Get available Kubernetes API resources."""
    return ok(run_kubectl("api-resources"))


def k8s_get_cluster_configuration() -> dict:
    """Get cluster configuration details (kubectl config view)."""
    return ok_json(run_kubectl_json("config", "view", "-o", "json"))


def k8s_get_resource_yaml(
    resource_type: Annotated[str, "Type of resource (deployment, service, pod, etc.)"],
    resource_name: Annotated[str, "Name of the resource"],
    namespace: Annotated[str, "Namespace of the resource (optional)"] = "",
) -> dict:
    """Get the YAML representation of a Kubernetes resource."""
    args = ["get", resource_type, resource_name, "-o", "yaml"]
    if namespace:
        args += ["-n", namespace]
    return ok(run_kubectl(*args))


def k8s_describe_resource(
    resource_type: Annotated[str, "Type of resource (deployment, service, pod, node, etc.)"],
    resource_name: Annotated[str, "Name of the resource"],
    namespace: Annotated[str, "Namespace of the resource (optional)"] = "",
) -> dict:
    """Describe a Kubernetes resource in detail."""
    args = ["describe", resource_type, resource_name]
    if namespace:
        args += ["-n", namespace]
    return ok(run_kubectl(*args))
