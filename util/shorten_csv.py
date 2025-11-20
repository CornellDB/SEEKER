import csv
import random
from pathlib import Path

def reservoir_sample_csv(file_path: str, n: int = 5000, random_state: int = None) -> None:
    if random_state is not None:
        random.seed(random_state)

    src = Path(file_path)
    out = src.with_name(src.stem + "_shortened" + src.suffix)

    reservoir = []
    with src.open(newline='', encoding='utf-8') as f_in:
        reader = csv.reader(f_in)
        header = next(reader)
        # Fill initial reservoir
        for i, row in enumerate(reader, start=1):
            if i <= n:
                reservoir.append(row)
            else:
                # Replace with decreasing probability
                j = random.randint(1, i)
                if j <= n:
                    reservoir[j-1] = row

    # Write sampled rows
    with out.open('w', newline='', encoding='utf-8') as f_out:
        writer = csv.writer(f_out)
        writer.writerow(header)
        writer.writerows(reservoir)

    print(f"Reservoir-sampled {n} rows to {out}")

# Example usage:
reservoir_sample_csv("/home/hans/Downloads/train.csv", n=100000, random_state=1)
