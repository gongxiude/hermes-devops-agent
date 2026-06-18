"""_fleet_core — shared kernel for the DevOps capability-plugin fleet.

A non-plugin package (no plugin.yaml) deployed alongside the domain plugins
(``observability``, ``kubernetes``, ``argocd`` …). Domain plugins put their
parent dir on ``sys.path`` and ``from _fleet_core import catalog, selectors``.

It provides the machinery every domain shares:
- ``catalog``   — load/resolve/list multi-target catalogs from config.yaml,
  generic over a ``section`` (e.g. "observability", "kubernetes") and a
  ``backend`` (e.g. "prometheus", "k8s").
- ``selectors`` — the common selector schema (business_line/environment/
  cluster/target) + enum injection, so prompt-routing is identical across
  domains.
- ``runners``   — connection runners reused by domains: ``http`` (read-only
  HTTP for prometheus/loki/argocd-api) and ``kubectl`` (subprocess for k8s).
"""

from . import catalog, selectors  # noqa: F401
