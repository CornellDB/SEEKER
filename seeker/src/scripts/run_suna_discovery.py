import argparse
import json
from pathlib import Path

from seeker.src.metadata_dataset_separation.data_import import DataLoader
from seeker.src.suna.service import SunaConfounderDiscoveryService
from seeker.src.suna.synthetic import (
    SYNTHETIC_DATASET_NAME,
    SyntheticDatasetSpec,
    ensure_synthetic_dataset,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run Suna confounder discovery on a dataset loaded by SEEKER.",
    )
    parser.add_argument(
        "--data-dir",
        default="dataset_examples",
        help="Directory containing CSV datasets and metadata JSON files.",
    )
    parser.add_argument(
        "--dataset",
        required=True,
        help="Dataset name (without .csv) to run discovery on.",
    )
    parser.add_argument(
        "--tau",
        type=float,
        default=None,
        help="Override quantile threshold tau (default from metadata).",
    )
    parser.add_argument(
        "--n-samples",
        type=int,
        default=None,
        help="Override number of bootstrap samples.",
    )
    parser.add_argument(
        "--disable-cache",
        action="store_true",
        help="Disable local sketch caching for this run.",
    )
    parser.add_argument(
        "--generate-synthetic",
        action="store_true",
        help=(
            "Regenerate the synthetic Suna demo dataset before running discovery. "
            "Only applies when --dataset is set to 'suna_synthetic'."
        ),
    )
    parser.add_argument(
        "--synthetic-samples",
        type=int,
        default=None,
        help=(
            "Override the number of rows used when generating the synthetic "
            "dataset (requires --dataset suna_synthetic)."
        ),
    )
    parser.add_argument(
        "--synthetic-seed",
        type=int,
        default=None,
        help=(
            "Override the RNG seed used for the synthetic dataset generation "
            "(requires --dataset suna_synthetic)."
        ),
    )
    return parser.parse_args()


def build_overrides(args: argparse.Namespace):
    overrides = {}
    if args.tau is not None:
        overrides["bootstrap.tau"] = args.tau
    if args.n_samples is not None:
        overrides["bootstrap.n_samples"] = args.n_samples
    if args.disable_cache:
        overrides["sketch.enable_cache"] = False
    return overrides


def main():
    args = parse_args()
    data_loader = DataLoader()

    if args.dataset == SYNTHETIC_DATASET_NAME:
        spec_kwargs = {}
        if args.synthetic_samples is not None:
            spec_kwargs["n_samples"] = args.synthetic_samples
        if args.synthetic_seed is not None:
            spec_kwargs["seed"] = args.synthetic_seed
        spec = SyntheticDatasetSpec(**spec_kwargs) if spec_kwargs else None
        ensure_synthetic_dataset(
            args.data_dir,
            spec=spec,
            force=args.generate_synthetic,
        )

    dataset_models = data_loader.upload_multiple(args.data_dir, include_metadata=True)
    if args.dataset not in dataset_models:
        raise ValueError(f"Dataset '{args.dataset}' not found in {args.data_dir}.")

    overrides = build_overrides(args)
    dataset_model = dataset_models[args.dataset]
    service = SunaConfounderDiscoveryService.from_dataset(
        dataset_model,
        overrides=overrides,
    )
    result = service.discover()

    df = result.to_dataframe()
    if df.empty:
        print("No confounders selected for the supplied configuration.")
    else:
        print(df.to_string(index=False))
    if result.ate is not None:
        print(
            f"\nEstimated ATE ({result.treatment} -> {result.outcome}): "
            f"{result.ate:.4f}"
            + (
                f" ± {result.ate_std_err:.4f}"
                if result.ate_std_err is not None
                else ""
            )
        )

    report_path = Path("dist") / "suna" / f"{args.dataset}_latest.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        json.dumps(
            {
                "dataset": result.dataset_name,
                "treatment": result.treatment,
                "outcome": result.outcome,
                "method": result.method,
                "findings": df.to_dict(orient="records"),
                "ate": result.ate,
                "ate_std_err": result.ate_std_err,
                "metadata": result.metadata,
            },
            indent=2,
        )
    )
    print(f"\nDiscovery report saved to {report_path}")


if __name__ == "__main__":
    main()
