"""
This file contains the implementation of the histogram computation for federated setting, where we use
histogram as the synopsis for datasets.
"""

import argparse
import os
import time
from functools import partial
from multiprocessing import Pool
from pathlib import Path
from typing import Any, List, Tuple

import numpy as np
import pandas as pd
from numpy.typing import NDArray
import zstandard as zstd
import pickle

Histogram = tuple[NDArray[np.uint32] | NDArray[np.float32], NDArray[np.float64]]
ROUNDING_PRECISION=4

def save_output(
    path: Path | str, data: Any, name: str | None = "output", threads: int | None = None
) -> None:
    if isinstance(path, str):
        path = Path(path)

    path.parent.mkdir(parents=True, exist_ok=True)
    path = path.with_suffix(".zst")

    cctx = None
    if threads:
        cctx = zstd.ZstdCompressor(threads=threads)

    with zstd.open(path, "wb", cctx=cctx) as file:
        pickle.dump(data, file, protocol=pickle.HIGHEST_PROTOCOL)
    if name:
        # logger.debug(f"Saved {name} to {path}")
        print(f"Saved {name} to {path}") #we use print first, then turn to logger later

# parser 的作用：定义哪些参数是合法的，并自动解析用户输入的命令行参数
# for example, we specify the required arguments for the function, and it will automatically parse the arguments from the command line, if missing, it will raise an error
def parse_args() -> argparse.Namespace:
    timestamp = time.strftime("%Y%m%d_%H%M%S", time.localtime())
    parser = argparse.ArgumentParser(
        description="Compute histograms from a collection of CSV files.",
        formatter_class=argparse.MetavarTypeHelpFormatter,
    )
    parser.add_argument(
        "-i",
        "--input",
        type=lambda s: Path(os.path.expandvars(s)),
        required=True,
        help="path to CSV dataset collection",
        metavar="SRC",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=lambda s: Path(os.path.expandvars(s)),
        required=True,
        help="path to the compressed histogram output",
        metavar="DEST",
    )
    parser.add_argument(
        "-f",
        "--scaling-factor",
        default=1,
        type=float,
        help="scaling factor to downsample or upsample the dataset (default: %(default)s)",
    )
    parser.add_argument(
        "--bin-range",
        nargs=2,
        default=None,
        type=int,
        help="range to randomly draw n_bins per histogram ('auto' if None, default: %(default)s)",
    )
    parser.add_argument(
        "--compute-frequencies",
        action="store_true",
        help="compute frequencies instead of densities",
    )
    parser.add_argument(
        "-w",
        "--workers",
        default=os.cpu_count(),
        type=int,
        help="number of worker processes (default: %(default)s)",
    )
    parser.add_argument(
        "--seed",
        default=42,
        type=int,
        help="random seed (default: %(default)s)",
    )
    parser.add_argument(
        "--log-file",
        type=lambda s: Path(os.path.expandvars(s)),
        default=Path(f"logs/hist_computation_{timestamp}.log"),
        help="path to log file (default: %(default)s)",
        metavar="LOG",
    )
    return parser.parse_args()


def compute_histogram(
    input_file: Path,
    seed: int,
    bin_range: tuple[int, int] | None,
    scaling_factor: float = 1,
    density: bool = True,
) -> tuple[list[Histogram], int] | str: #return the histogram when success, otherwise return the error message
    try:
        np.seterr(all="raise")
        hists: list[Histogram] = []
        rng = np.random.default_rng(seed)
        df = pd.read_csv(input_file)
        bin_counter = 0
        for _, values in df.items():
            if pd.api.types.is_numeric_dtype(values):
                values.dropna(inplace=True)
                # We filter out huge values to prevent overflows in the index (and since they
                # are unrealistic for percentile queries). Since multiple large integer values are
                # represented by the same float value, we cast them before counting unique values.
                values = values[(values > -(2**53)) & (values < 2**53)].astype(dtype=np.float64)
                values = values.round(ROUNDING_PRECISION)
                if values.nunique() > 1 and values.min() != values.max():
                    probability = scaling_factor
                    while probability > rng.random():
                        bins: int | str
                        if bin_range:
                            bins = min(
                                values.nunique() - 1,
                                rng.integers(low=bin_range[0], high=bin_range[1] + 1),
                            )
                            bin_counter += bins
                        else:
                            bins = "auto"
                        hist = np.histogram(
                            values,
                            bins=bins,
                            # Numpy computes density different than we need them
                            density=False,
                        )

                        # Histogram verification
                        assert (np.diff(hist[1]) == 0).sum() == 0
                        assert hist[1].dtype == np.float64
                        if density:
                            hist = (np.divide(hist[0], hist[0].sum(), dtype=np.float32), hist[1])
                            assert np.isclose(hist[0].sum(), 1)
                        else:
                            hist = (hist[0].astype(np.uint32, casting="safe"), hist[1])

                        hists.append(hist)

                        probability -= 1

                # newly added for categorical data
                elif pd.api.types.is_string_dtype(values) or pd.api.types.is_categorical_dtype(values):
                    counts = values.value_counts().sort_index()
                    bins = np.arange(len(counts)+1) #the bins are the indices of the categories
                    hist = (counts.values.astype(np.uint32, casting="safe"), bins.astype(np.float64))
                    hists.append(hist)
                    bin_counter += len(counts)

                else:
                    raise ValueError(f"Unsupported data type: {values.dtype}")

        return hists, bin_counter
    except AssertionError as e:
        raise AssertionError(input_file) from e
    except Exception as e:
        return f"{input_file}: {type(e)} {e}"


def load_archive(path: Path) -> tuple[str, Histogram]:
    archive = np.load(path)
    hist = (archive["values"], archive["bins"])
    archive.close()
    return path.stem, hist


def load_compressed_histograms(path: Path | str) -> List[Tuple[np.uint32, Histogram]]:
    """
    Load compressed histograms from a .zst file
    param path: path to the compressed histogram file
    return: list of (histogram_id, histogram) tuples
    """
    if isinstance(path, str):
        path = Path(path)

    with zstd.open(path, "rb") as file:
        return pickle.load(file)


def main() -> None:
    start = time.perf_counter()
    args = parse_args()
    # configure_run("INFO", args.log_file)
    # logger.debug(vars(args))

    if args.input.is_file():
        input_files = [args.input]
    else:
        input_files = list(args.input.iterdir())

    n_files = len(input_files)
    seeds = np.random.default_rng(args.seed).integers(10000, size=n_files)
    with Pool(processes=args.workers) as pool:
        fn = partial(
            compute_histogram,
            bin_range=args.bin_range,
            scaling_factor=args.scaling_factor,
            density=not args.compute_frequencies,
        )
        results = pool.starmap(fn, zip(input_files, seeds, strict=True))

    errors: list[str] = []
    hists: list[tuple[np.uint32, Histogram]] = []
    i = 0
    bin_counter = 0
    for result in results:
        if isinstance(result, str):
            errors.append(result)
        else:
            for hist in result[0]:
                hists.append((np.uint32(i), hist))
                i += 1
            bin_counter += result[1]

    save_output(args.output, hists, name="histograms")

    end = time.perf_counter()
    # logger.info(
    #     f"Parsed {n_files} files and generated {i} histograms with a total of {bin_counter} bins "
    #     f"in {end - start:.2f}s with {len(errors)} errors."
    # )
    # logger.trace(f"histogram_count, {i}")
    # logger.trace(f"bin_count, {bin_counter}")
    # logger.trace(f"error_count, {len(errors)}")
    # logger.trace(f"construction_time, {end - start}")
    # for error in errors:
    #     logger.debug(error)


if __name__ == "__main__":
    main()