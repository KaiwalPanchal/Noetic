"""Generated, thin per-agent adapters over one canonical, provider-neutral source."""

from .base import Adapter, Canonical, OutFile
from .sync import REGISTRY, FileResult, SyncReport, load_canonical, sync

__all__ = ["Adapter", "Canonical", "OutFile", "REGISTRY", "FileResult", "SyncReport", "load_canonical", "sync"]
