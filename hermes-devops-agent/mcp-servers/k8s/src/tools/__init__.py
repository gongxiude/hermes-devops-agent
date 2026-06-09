"""Tools package — re-exports all tool functions."""
from .readonly import (
    k8s_get_resources,
    k8s_get_pod_logs,
    k8s_get_events,
    k8s_get_available_api_resources,
    k8s_get_cluster_configuration,
    k8s_get_resource_yaml,
    k8s_describe_resource,
)
from .write import (
    k8s_scale,
    k8s_patch_resource,
    k8s_patch_status,
    k8s_apply_manifest,
    k8s_create_resource,
    k8s_create_resource_from_url,
    k8s_delete_resource,
    k8s_rollout,
    k8s_label_resource,
    k8s_annotate_resource,
    k8s_remove_label,
    k8s_remove_annotation,
    k8s_execute_command,
    k8s_check_service_connectivity,
)

READONLY_TOOLS = [
    k8s_get_resources,
    k8s_get_pod_logs,
    k8s_get_events,
    k8s_get_available_api_resources,
    k8s_get_cluster_configuration,
    k8s_get_resource_yaml,
    k8s_describe_resource,
]

WRITE_TOOLS = [
    k8s_scale,
    k8s_patch_resource,
    k8s_patch_status,
    k8s_apply_manifest,
    k8s_create_resource,
    k8s_create_resource_from_url,
    k8s_delete_resource,
    k8s_rollout,
    k8s_label_resource,
    k8s_annotate_resource,
    k8s_remove_label,
    k8s_remove_annotation,
    k8s_execute_command,
    k8s_check_service_connectivity,
]
