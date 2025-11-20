import random
import numpy as np


def identify_group_query(
    new_col_lst,
    clusters,
    grp_size,
    likelihood_num,
    likelihood_den,
    queried_cand,
    max_attempts: int = 50,
):
    """
    Probability‑weighted group selection without Thompson sampling.
    Retries up to max_attempts to avoid duplicates and empty clusters.

    Args:
      new_col_lst      -- list of all JoinColumn objects (only .loc is used)
      clusters         -- List[List[JoinColumn]]; candidate clusters
      grp_size         -- how many columns to pick
      likelihood_num   -- List[int]; “success” counts per cluster
      likelihood_den   -- List[int]; “trial” counts per cluster
      queried_cand     -- set or dict of already‐seen repr strings
      max_attempts     -- how many times to retry before erroring

    Returns:
      (group, representation) where
        group          -- List[JoinColumn]
        representation -- str of sorted locs like "3|5|9"
    """
    # 1) compute raw success probabilities
    likelihood = [
        (n / d if d > 0 else 0.0)
        for n, d in zip(likelihood_num, likelihood_den)
    ]
    total = sum(likelihood)
    # 2) normalize (fallback to uniform if total is zero)
    if total > 0:
        probs = [l / total for l in likelihood]
    else:
        probs = [1.0 / len(likelihood)] * len(likelihood)

    for _ in range(max_attempts):
        group = []
        # 3) draw grp_size items, skipping empty clusters
        for _ in range(grp_size):
            while True:
                # sample a cluster index with Python or NumPy
                cidx = np.random.choice(len(clusters), p=probs)
                if clusters[cidx]:
                    break
            group.append(random.choice(clusters[cidx]))

        # 4) build a sorted‐loc representation for dedup
        sorted_locs = sorted(jc.loc for jc in group)
        rep = "|".join(str(loc) for loc in sorted_locs)

        if rep not in queried_cand:
            return group, rep

    raise RuntimeError(f"Could not find a new group in {max_attempts} attempts.")


def identify_group_query_thompson(
    new_col_lst,
    clusters,
    grp_size,
    likelihood_num,
    likelihood_den,
    queried_cand,
    max_attempts: int = 50,
):
    """
    Thompson Sampling–based group selection.
    Retries up to max_attempts to avoid duplicates and empty clusters.

    Args:
      new_col_lst      -- list of all JoinColumn objects (only .loc is used)
      clusters         -- List[List[JoinColumn]]; candidate clusters
      grp_size         -- how many columns to pick
      likelihood_num   -- List[int]; “success” counts per cluster
      likelihood_den   -- List[int]; “trial” counts per cluster
      queried_cand     -- set or dict of already‐seen repr strings
      max_attempts     -- how many times to retry before erroring

    Returns:
      (group, representation) where
        group          -- List[JoinColumn]
        representation -- str of sorted locs like "3|5|9"
    """
    # 1) Beta parameters
    successes = np.array(likelihood_num, dtype=float)
    failures  = np.array(likelihood_den, dtype=float) - successes
    alphas = successes + 1.0
    betas  = failures + 1.0

    # 2) draw one sample per cluster
    p_samples = np.random.beta(alphas, betas)
    total = p_samples.sum()
    if total > 0:
        probs = p_samples / total
    else:
        probs = np.ones_like(p_samples) / len(p_samples)

    for _ in range(max_attempts):
        group = []
        # 3) draw grp_size items, skipping empty clusters
        for _ in range(grp_size):
            while True:
                cidx = np.random.choice(len(clusters), p=probs)
                if clusters[cidx]:
                    break
            group.append(random.choice(clusters[cidx]))

        # 4) build a sorted‐loc representation for dedup
        sorted_locs = sorted(jc.loc for jc in group)
        rep = "|".join(str(loc) for loc in sorted_locs)

        if rep not in queried_cand:
            return group, rep

    raise RuntimeError(f"Could not find a new Thompson‐sampled group in {max_attempts} attempts.")
