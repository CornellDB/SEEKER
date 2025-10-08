from __future__ import annotations

from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Dict, Iterable, List, Optional

from seeker.src.index_creation.dataset_model import DatasetModel


DEFAULT_CACHE_ROOT = Path("dist") / "suna"


@dataclass(frozen=True)
class BootstrapConfig:
    """Configuration for bootstrap sampling in the BCD loop."""

    n_samples: int = 100
    tau: float = 0.05  # quantile level used in Algorithm 1
    random_state: Optional[int] = 0


@dataclass(frozen=True)
class SketchConfig:
    """Configuration for sketch caching and storage."""

    cache_dir: Path = DEFAULT_CACHE_ROOT
    enable_cache: bool = True
    overwrite: bool = False

    def resolve(self, dataset_id: str) -> Path:
        """Return the concrete cache directory for a dataset."""
        return self.cache_dir / dataset_id


@dataclass(frozen=True)
class SunaConfig:
    """Top-level configuration for the Suna discovery pipeline."""

    dataset_name: str
    treatment: str
    outcome: str
    method: str = "bcd"
    candidate_covariates: Optional[List[str]] = None
    join_keys: Optional[List[List[str]]] = None
    mi_drop_threshold: float = 0.0
    device: str = "cpu"
    bootstrap: BootstrapConfig = field(default_factory=BootstrapConfig)
    sketch: SketchConfig = field(default_factory=SketchConfig)
    random_state: Optional[int] = 0

    def with_overrides(self, overrides: Dict[str, object]) -> "SunaConfig":
        """Return a new config with simple attribute overrides."""
        update_kwargs = {}
        nested_overrides: Dict[str, Dict[str, object]] = {}

        for key, value in overrides.items():
            if key.startswith("bootstrap."):
                nested_overrides.setdefault("bootstrap", {})[
                    key.split(".", 1)[1]
                ] = value
            elif key.startswith("sketch."):
                nested_overrides.setdefault("sketch", {})[
                    key.split(".", 1)[1]
                ] = value
            else:
                update_kwargs[key] = value

        config = replace(self, **update_kwargs) if update_kwargs else self

        if "bootstrap" in nested_overrides:
            config = replace(
                config,
                bootstrap=replace(config.bootstrap, **nested_overrides["bootstrap"]),
            )
        if "sketch" in nested_overrides:
            sketch_updates = nested_overrides["sketch"]
            if "cache_dir" in sketch_updates:
                cache_dir = Path(sketch_updates["cache_dir"])
                sketch_updates = {**sketch_updates, "cache_dir": cache_dir}
            config = replace(config, sketch=replace(config.sketch, **sketch_updates))
        return config

    @staticmethod
    def _metadata_block(metadata: Optional[Dict]) -> Dict:
        if not metadata:
            return {}
        return metadata.get("suna", {})

    @classmethod
    def from_metadata(
        cls,
        dataset_model: DatasetModel,
        *,
        overrides: Optional[Dict[str, object]] = None,
    ) -> "SunaConfig":
        overrides = overrides or {}
        metadata = dataset_model.metadata or {}
        suna_block = cls._metadata_block(metadata)

        treatment = suna_block.get("treatment_column")
        outcome = suna_block.get("outcome_column")
        if not treatment:
            treatment = overrides.get("treatment")
        if not outcome:
            outcome = overrides.get("outcome")
        if not treatment or not outcome:
            raise ValueError(
                "Dataset metadata must declare `suna.treatment_column` and "
                "`suna.outcome_column`, or they must be provided via overrides "
                "(treatment=<col>, outcome=<col>)."
            )

        bootstrap_block = suna_block.get("bootstrap", {})
        bootstrap = BootstrapConfig(
            n_samples=bootstrap_block.get("n_samples", suna_block.get("n_boot", 100)),
            tau=suna_block.get("tau", 0.05),
            random_state=bootstrap_block.get("random_state", 0),
        )

        sketch_block = suna_block.get("sketch", {})
        cache_dir = Path(sketch_block.get("cache_dir", DEFAULT_CACHE_ROOT))
        sketch = SketchConfig(
            cache_dir=cache_dir,
            enable_cache=sketch_block.get("enable_cache", True),
            overwrite=sketch_block.get("overwrite", False),
        )

        dataset_name = getattr(dataset_model, "dataset_name", None)
        if dataset_name is None:
            dataset_name = getattr(dataset_model, "name", "unknown_dataset")

        config = cls(
            dataset_name=dataset_name,
            treatment=treatment,
            outcome=outcome,
            method=suna_block.get("default_method", "bcd"),
            candidate_covariates=suna_block.get("candidate_covariates"),
            join_keys=suna_block.get("join_keys"),
            mi_drop_threshold=suna_block.get("mi_drop_threshold", 0.0),
            device=suna_block.get("device", "cpu"),
            bootstrap=bootstrap,
            sketch=sketch,
            random_state=suna_block.get("random_state", overrides.get("random_state", 0)),
        )

        if overrides:
            config = config.with_overrides(overrides)
        return config


def parse_cli_overrides(params: Iterable[str]) -> Dict[str, object]:
    """
    Convert colon-separated CLI parameters into a dictionary.

    Example:
        ["dataset=foo", "treatment=T", "bootstrap.n_samples=50"]
    """
    config_overrides: Dict[str, object] = {}
    for param in params:
        if "=" not in param:
            continue
        key, value = param.split("=", 1)
        key = key.strip()
        value = value.strip()
        if key == "candidate_covariates":
            config_overrides[key] = [part.strip() for part in value.split(",") if part.strip()]
        elif key == "join_keys":
            groups = []
            for segment in value.split(";"):
                cols = [col.strip() for col in segment.split(",") if col.strip()]
                if cols:
                    groups.append(cols)
            config_overrides[key] = groups
        elif value.lower() in {"true", "false"}:
            config_overrides[key] = value.lower() == "true"
        else:
            try:
                numeric = float(value)
                if numeric.is_integer():
                    config_overrides[key] = int(numeric)
                else:
                    config_overrides[key] = numeric
            except ValueError:
                config_overrides[key] = value
    return config_overrides
