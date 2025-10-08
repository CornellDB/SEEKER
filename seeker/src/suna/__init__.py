"""
Suna confounder discovery package.

This package refactors the standalone Suna prototype into SEEKER’s
service-oriented architecture. It exposes configuration factories,
discovery pipelines, and service bindings used by the interpreter.
"""

from .config import SunaConfig, BootstrapConfig, SketchConfig
from .service import (
    SunaConfounderDiscoveryService,
    SunaDataSeeker,
    OptionalDependencyUnavailable,
)
from .results import SunaDiscoveryResult, ConfounderFinding, BootstrapSummary
from .synthetic import (
    SYNTHETIC_DATASET_NAME,
    SyntheticDatasetSpec,
    ensure_synthetic_dataset,
)

__all__ = [
    "SunaConfig",
    "BootstrapConfig",
    "SketchConfig",
    "SunaConfounderDiscoveryService",
    "SunaDataSeeker",
    "OptionalDependencyUnavailable",
    "SunaDiscoveryResult",
    "ConfounderFinding",
    "BootstrapSummary",
    "SYNTHETIC_DATASET_NAME",
    "SyntheticDatasetSpec",
    "ensure_synthetic_dataset",
]
