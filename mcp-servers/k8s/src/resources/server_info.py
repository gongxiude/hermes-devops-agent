"""Static server info resource."""
from ..utils import Config
from ..tools import READONLY_TOOLS, WRITE_TOOLS


def server_info() -> dict:
    """Return server metadata, registered tools, and read-only mode status."""
    tools = [f.__name__ for f in READONLY_TOOLS]
    if not Config.READ_ONLY:
        tools += [f.__name__ for f in WRITE_TOOLS]
    return {
        "name": Config.SERVER_NAME,
        "version": Config.SERVER_VERSION,
        "read_only": Config.READ_ONLY,
        "kubectl_bin": Config.KUBECTL_BIN,
        "kubeconfig": Config.KUBECONFIG or "(default)",
        "tools": tools,
        "tool_count": len(tools),
    }
