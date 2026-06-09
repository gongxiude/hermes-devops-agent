"""Write (mutating) Kubernetes tools — only registered when K8S_READ_ONLY=false."""
from __future__ import annotations

import os
from typing import Annotated

from ..utils import (
    run_kubectl, run_kubectl_json,
    write_temp_manifest,
    validate_k8s_name, validate_namespace, validate_yaml_content, validate_command,
    ok,
)


def k8s_scale(
    name: Annotated[str, "Name of the deployment"],
    replicas: Annotated[int, "Desired number of replicas"],
    namespace: Annotated[str, "Namespace of the deployment"] = "default",
) -> dict:
    """Scale a Kubernetes deployment."""
    return ok(run_kubectl("scale", "deployment", name,
                          "--replicas", str(replicas), "-n", namespace))


def k8s_patch_resource(
    resource_type: Annotated[str, "Type of resource (deployment, service, etc.)"],
    resource_name: Annotated[str, "Name of the resource"],
    patch: Annotated[str, "JSON strategic merge patch to apply"],
    namespace: Annotated[str, "Namespace of the resource"] = "default",
) -> dict:
    """Patch a Kubernetes resource using strategic merge patch."""
    validate_k8s_name(resource_name)
    validate_namespace(namespace)
    validate_yaml_content(patch)
    return ok(run_kubectl("patch", resource_type, resource_name,
                          "-p", patch, "-n", namespace))


def k8s_patch_status(
    resource_type: Annotated[str, "Type of resource (deployment, service, etc.)"],
    resource_name: Annotated[str, "Name of the resource"],
    patch: Annotated[str, "JSON/YAML status subresource patch"],
    namespace: Annotated[str, "Namespace of the resource"] = "default",
) -> dict:
    """Patch the status subresource of a Kubernetes resource."""
    validate_k8s_name(resource_name)
    validate_namespace(namespace)
    validate_yaml_content(patch)
    return ok(run_kubectl("patch", resource_type, resource_name,
                          "--subresource=status", "--type=merge",
                          "-p", patch, "-n", namespace))


def k8s_apply_manifest(
    manifest: Annotated[str, "YAML manifest content to apply"],
) -> dict:
    """Apply a YAML manifest to the Kubernetes cluster (kubectl apply -f)."""
    validate_yaml_content(manifest)
    path = write_temp_manifest(manifest)
    try:
        return ok(run_kubectl("apply", "-f", path))
    finally:
        os.unlink(path)


def k8s_create_resource(
    yaml_content: Annotated[str, "YAML content of the resource to create"],
) -> dict:
    """Create a Kubernetes resource from YAML content (kubectl create -f)."""
    validate_yaml_content(yaml_content)
    path = write_temp_manifest(yaml_content)
    try:
        return ok(run_kubectl("create", "-f", path))
    finally:
        os.unlink(path)


def k8s_create_resource_from_url(
    url: Annotated[str, "URL pointing to a YAML manifest"],
    namespace: Annotated[str, "Namespace to create the resource in (optional)"] = "",
) -> dict:
    """Create a Kubernetes resource from a URL pointing to a YAML manifest."""
    args = ["create", "-f", url]
    if namespace:
        args += ["-n", namespace]
    return ok(run_kubectl(*args))


def k8s_delete_resource(
    resource_type: Annotated[str, "Type of resource (pod, service, deployment, etc.)"],
    resource_name: Annotated[str, "Name of the resource"],
    namespace: Annotated[str, "Namespace of the resource"] = "default",
) -> dict:
    """Delete a Kubernetes resource."""
    return ok(run_kubectl("delete", resource_type, resource_name, "-n", namespace))


def k8s_rollout(
    action: Annotated[str, "Rollout action: history, pause, restart, resume, status, undo"],
    resource_type: Annotated[str, "Resource type (e.g. deployment)"],
    resource_name: Annotated[str, "Resource name"],
    namespace: Annotated[str, "Namespace of the resource (optional)"] = "",
) -> dict:
    """Perform rollout operations on Kubernetes resources."""
    ALLOWED_ACTIONS = {"history", "pause", "restart", "resume", "status", "undo"}
    if action not in ALLOWED_ACTIONS:
        raise ValueError(f"action must be one of {sorted(ALLOWED_ACTIONS)}, got {action!r}")
    args = ["rollout", action, f"{resource_type}/{resource_name}"]
    if namespace:
        args += ["-n", namespace]
    return ok(run_kubectl(*args))


def k8s_label_resource(
    resource_type: Annotated[str, "Type of resource"],
    resource_name: Annotated[str, "Name of the resource"],
    labels: Annotated[str, "Space-separated key=value pairs, e.g. 'env=prod version=v2'"],
    namespace: Annotated[str, "Namespace of the resource (optional)"] = "",
) -> dict:
    """Add or update labels on a Kubernetes resource."""
    args = ["label", resource_type, resource_name] + labels.split()
    if namespace:
        args += ["-n", namespace]
    return ok(run_kubectl(*args))


def k8s_annotate_resource(
    resource_type: Annotated[str, "Type of resource"],
    resource_name: Annotated[str, "Name of the resource"],
    annotations: Annotated[str, "Space-separated key=value pairs, e.g. 'owner=team-a ticket=JIRA-123'"],
    namespace: Annotated[str, "Namespace of the resource (optional)"] = "",
) -> dict:
    """Add or update annotations on a Kubernetes resource."""
    args = ["annotate", resource_type, resource_name] + annotations.split()
    if namespace:
        args += ["-n", namespace]
    return ok(run_kubectl(*args))


def k8s_remove_label(
    resource_type: Annotated[str, "Type of resource"],
    resource_name: Annotated[str, "Name of the resource"],
    label_key: Annotated[str, "Label key to remove"],
    namespace: Annotated[str, "Namespace of the resource (optional)"] = "",
) -> dict:
    """Remove a label from a Kubernetes resource."""
    args = ["label", resource_type, resource_name, f"{label_key}-"]
    if namespace:
        args += ["-n", namespace]
    return ok(run_kubectl(*args))


def k8s_remove_annotation(
    resource_type: Annotated[str, "Type of resource"],
    resource_name: Annotated[str, "Name of the resource"],
    annotation_key: Annotated[str, "Annotation key to remove"],
    namespace: Annotated[str, "Namespace of the resource (optional)"] = "",
) -> dict:
    """Remove an annotation from a Kubernetes resource."""
    args = ["annotate", resource_type, resource_name, f"{annotation_key}-"]
    if namespace:
        args += ["-n", namespace]
    return ok(run_kubectl(*args))


def k8s_execute_command(
    pod_name: Annotated[str, "Name of the pod"],
    command: Annotated[str, "Command to execute inside the pod"],
    namespace: Annotated[str, "Namespace of the pod"] = "default",
    container: Annotated[str, "Container name (for multi-container pods)"] = "",
) -> dict:
    """Execute a command in a Kubernetes pod (kubectl exec)."""
    validate_k8s_name(pod_name, "pod_name")
    validate_namespace(namespace)
    validate_command(command)
    args = ["exec", pod_name, "-n", namespace]
    if container:
        args += ["-c", container]
    args += ["--"] + command.split()
    return ok(run_kubectl(*args))


def k8s_check_service_connectivity(
    service_name: Annotated[str, "Service to test, e.g. my-svc.my-ns.svc.cluster.local:80"],
    namespace: Annotated[str, "Namespace to run the check from"] = "default",
) -> dict:
    """Check connectivity to a service using a temporary curl pod."""
    import random
    pod_name = f"curl-test-{random.randint(1000, 9999)}"
    try:
        run_kubectl("run", pod_name, "--image=curlimages/curl",
                    "-n", namespace, "--restart=Never", "--", "sleep", "3600")
        run_kubectl("wait", "--for=condition=ready", f"pod/{pod_name}",
                    "-n", namespace, "--timeout=60s")
        return ok(run_kubectl("exec", pod_name, "-n", namespace,
                              "--", "curl", "-s", service_name))
    finally:
        try:
            run_kubectl("delete", "pod", pod_name, "-n", namespace, "--ignore-not-found")
        except Exception:
            pass
