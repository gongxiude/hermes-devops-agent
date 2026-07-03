import importlib.util
import sys
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "plugins" / "devops_agent" / "fastpath.py"
spec = importlib.util.spec_from_file_location("devops_agent_fastpath_test", MODULE_PATH)
fastpath = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = fastpath
spec.loader.exec_module(fastpath)


def test_parse_intlsms_gateway_cpu_memory_request():
    parsed = fastpath.parse_observability_fastpath(
        "查看国际短信生产环境gateway服务近10分钟的内存和CPU"
    )

    assert parsed is not None
    assert parsed.service == "gateway"
    assert parsed.domain == "intlsms"
    assert parsed.environment == "production"
    assert parsed.request_type == "metrics_cpu_memory"
    assert parsed.window == "last_10_minutes"


def test_parse_ignores_incomplete_observability_request():
    assert fastpath.parse_observability_fastpath("查看国际短信生产环境gateway服务日志") is None
    assert fastpath.parse_observability_fastpath("查看生产环境gateway服务近10分钟的内存和CPU") is None
