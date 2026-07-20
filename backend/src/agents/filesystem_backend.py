"""Filesystem backend shared by LOOP deep agents (mirrors ProspectFinder)."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from deepagents import FilesystemPermission
from deepagents.backends import FilesystemBackend

# Same root as LOOP_agents/ProspectFinderAgent.py:
# TheOneEye-LinkedinAccount-Maintainer/AutonomousResearch/Agent
_MAINTAINER_ROOT = Path(__file__).resolve().parents[4]
_DEFAULT_WORKSPACE = _MAINTAINER_ROOT / "AutonomousResearch" / "Agent"


@lru_cache
def default_filesystem_backend() -> FilesystemBackend:
    """Return a process-wide FilesystemBackend rooted at ProspectFinder's workspace."""
    workspace = _DEFAULT_WORKSPACE
    workspace.mkdir(parents=True, exist_ok=True)
    return FilesystemBackend(root_dir=workspace, virtual_mode=True)


def default_filesystem_permissions() -> list[FilesystemPermission]:
    """Allow read/write anywhere under the virtual filesystem root."""
    return [
        FilesystemPermission(
            operations=["write", "read"],
            paths=["/**"],
        )
    ]
