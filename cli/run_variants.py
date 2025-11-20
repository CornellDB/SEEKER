"""
Run METAM variants from the command line.

This script mirrors the GUI workflow while allowing power users to execute or
compare variants programmatically.  Variants are described in a JSON file using
the same schema the frontend sends to the Flask backend.

Example (using bundled sample data):
    python -m cli.run_variants

Example (custom inputs):
    python -m cli.run_variants \\
        --query-path /path/to/base.csv \\
        --data-dir /path/to/external_tables \\
        --join-path /path/to/join_paths.csv \\
        --variants /path/to/variants.json
"""

from __future__ import annotations

import argparse
import json
import os
import queue
import re
import threading
from pathlib import Path
from typing import Any, Dict, Iterable, List

from metam import Config, MetamResult, run_metam

DEFAULT_DATA_ROOT = Path(__file__).resolve().parent / "data"
DEFAULT_QUERY_PATH = DEFAULT_DATA_ROOT / "dataset_file" / "train.csv"
DEFAULT_DATA_DIR = DEFAULT_DATA_ROOT / "folder"
DEFAULT_JOIN_PATH = DEFAULT_DATA_ROOT / "joinpath" / "join_paths.csv"
DEFAULT_OUTPUT_DIR = DEFAULT_DATA_ROOT / "outputs"
DEFAULT_VARIANTS = Path(__file__).resolve().parent / "variants.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run METAM variants from the command line.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--query-path",
        type=Path,
        default=DEFAULT_QUERY_PATH,
        help="Path to the main CSV file (relative to the cli/data layout by default).",
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=DEFAULT_DATA_DIR,
        help="Directory containing candidate auxiliary tables.",
    )
    parser.add_argument(
        "--join-path",
        type=Path,
        default=DEFAULT_JOIN_PATH,
        help="CSV file listing join paths.",
    )
    parser.add_argument(
        "--variants",
        type=Path,
        help="JSON file describing variants (same format produced by the frontend).",
        default=DEFAULT_VARIANTS,
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        help="Directory used to store augmented CSVs.",
        default=DEFAULT_OUTPUT_DIR,
    )
    parser.add_argument(
        "--summary-json",
        type=Path,
        help="Optional path to persist a JSON summary of all runs.",
    )
    return parser.parse_args()


def load_variants(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(f"Variants file not found: {path}")
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, list):
        raise ValueError("Variants JSON must contain a list of variant objects.")
    if not data:
        raise ValueError("No variants specified.")
    return data


def build_config(
    query_path: Path,
    data_dir: Path,
    join_path_file: Path,
    output_dir: Path,
    variant: Dict[str, Any],
) -> Config:
    if not query_path.exists():
        raise FileNotFoundError(f"Query dataset not found: {query_path}")
    if not join_path_file.exists():
        raise FileNotFoundError(f"Join path file not found: {join_path_file}")
    if not data_dir.exists():
        raise FileNotFoundError(f"Auxiliary data directory not found: {data_dir}")

    cfg = Config()
    cfg.DATA_PATH = str(data_dir)
    cfg.QUERY_PATH = str(query_path)
    cfg.QUERY_DATA = query_path.name
    cfg.JOIN_PATH_FILE = str(join_path_file)
    cfg.OUTPUT_PATH = str(output_dir)

    metric = variant.get("metric")
    task = variant.get("task")
    attribute = variant.get("attribute")
    if not all([metric, task, attribute]):
        raise ValueError("Variant must specify 'metric', 'task', and 'attribute'.")

    cfg.UTILITY_METRIC = metric
    cfg.PRED_COL = attribute
    cfg.MODEL = cfg.get_model_for_task(task)

    _apply_variant_profiler(cfg, variant.get("profilers"))
    _apply_variant_query_method(cfg, variant.get("queryMethod"))
    _apply_variant_quality_scorer(cfg, variant.get("qualityScorers"))

    variant_name = variant.get("name") or f"{task}_{attribute}_{metric}"
    safe_name = _slugify(variant_name)
    output_dir.mkdir(parents=True, exist_ok=True)
    cfg.OUTPUT_FILE = os.path.join(str(output_dir), f"{safe_name}.csv")
    return cfg


def _apply_variant_profiler(config: Config, profiler_names: Iterable[str] | None) -> None:
    if not profiler_names:
        return
    available = {cls.__name__: cls for cls in Config.SHARED_PROFILER_LIST}
    selected = [available[name] for name in profiler_names if name in available]
    if selected:
        config.PROFILER_LIST = selected


def _apply_variant_query_method(config: Config, helper_name: str | None) -> None:
    if not helper_name:
        return
    for fn in Config.SHARED_GRP_HELPER_LIST:
        if fn.__name__ == helper_name:
            config.GRP_QUERY = fn
            break


def _apply_variant_quality_scorer(config: Config, scorer_name: str | None) -> None:
    if not scorer_name:
        return
    for fn in Config.SHARED_QUALITYSCORERLIST:
        if fn.__name__ == scorer_name:
            config.QUALITYSCORER = fn
            break


def run_variant(config: Config, variant_name: str) -> MetamResult:
    progress_q: "queue.Queue[dict[str, Any]]" = queue.Queue()
    stop_event = threading.Event()

    def consume_progress():
        while not stop_event.is_set():
            try:
                msg = progress_q.get(timeout=0.5)
            except queue.Empty:
                continue
            if not isinstance(msg, dict):
                continue
            _print_progress_event(variant_name, msg)
            if msg.get("type") in {"complete", "error"}:
                break
        stop_event.set()

    consumer = threading.Thread(target=consume_progress, daemon=True)
    consumer.start()

    try:
        result = run_metam(config, event_queue=progress_q)
    finally:
        stop_event.set()
        # ensures consumer exits even if complete wasn't received
        progress_q.put({"type": "complete"})
        consumer.join(timeout=1.0)

    result.dataframe.to_csv(config.OUTPUT_FILE, index=False)
    return result


def format_summary_row(
    idx: int,
    variant: Dict[str, Any],
    result: MetamResult,
    config: Config,
) -> str:
    name = variant.get("name") or f"variant_{idx}"
    delta = result.final_metric - result.initial_metric
    return (
        f"{idx:>3} | {name:<20} | {variant.get('task','-'):<14} | "
        f"{variant.get('metric','-'):<10} | {result.initial_metric:>10.4f} | "
        f"{result.final_metric:>10.4f} | {delta:>+10.4f} | "
        f"{result.total_queries:>6} | {result.iterations:>3} | "
        f"{Path(config.OUTPUT_FILE).name}"
    )


def print_summary_header() -> None:
    header = (
        " idx | variant              | task           | metric     | "
        "initial   | final      | delta      | queries | it | output"
    )
    print(header)
    print("-" * len(header))


def _slugify(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]", "_", value)


def _print_progress_event(variant_name: str, msg: Dict[str, Any]) -> None:
    msg_type = msg.get("type")
    prefix = f"[{variant_name}]"
    if msg_type == "update":
        score = msg.get("score")
        if isinstance(score, (int, float)):
            score_text = f"{score:.4f}"
        else:
            score_text = str(score)
        iteration = msg.get("iteration")
        print(f"{prefix} iteration {iteration} score={score_text}")
    elif msg_type == "augmentation":
        augmentation = msg.get("augmentation")
        score = msg.get("score")
        print(f"{prefix} augmentation {augmentation} -> {score}")
    elif msg_type == "error":
        print(f"{prefix} ERROR: {msg.get('message')}")
    elif msg_type == "complete":
        print(f"{prefix} complete")
    else:
        print(f"{prefix} {msg}")


def main():
    args = parse_args()
    variants = load_variants(args.variants)

    summaries: List[Dict[str, Any]] = []
    print_summary_header()
    for idx, variant in enumerate(variants, start=1):
        config = build_config(
            args.query_path,
            args.data_dir,
            args.join_path,
            args.output_dir,
            variant,
        )
        variant_name = variant.get("name") or f"variant_{idx}"
        print(f"\n=== Running {variant_name} ===")
        result = run_variant(config, variant_name)
        print(format_summary_row(idx, variant, result, config))
        summaries.append(
            {
                "index": idx,
                "name": variant.get("name") or f"variant_{idx}",
                "task": variant.get("task"),
                "metric": variant.get("metric"),
                "attribute": variant.get("attribute"),
                "initial_metric": result.initial_metric,
                "final_metric": result.final_metric,
                "delta": result.final_metric - result.initial_metric,
                "total_queries": result.total_queries,
                "iterations": result.iterations,
                "output_file": config.OUTPUT_FILE,
                "candidate_indices": list(result.candidate_indices),
            }
        )

    if args.summary_json:
        args.summary_json.parent.mkdir(parents=True, exist_ok=True)
        with args.summary_json.open("w", encoding="utf-8") as handle:
            json.dump(summaries, handle, indent=2)


if __name__ == "__main__":
    main()
