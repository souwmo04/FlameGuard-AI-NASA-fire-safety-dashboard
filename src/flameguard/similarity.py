"""Similar-experiment search over the tested FLEX conditions (observed data only).

Distance = Euclidean distance in standardised (O2, CO2, He, droplet diameter) space,
within the same fuel, using the scales stored in the final model's applicability
domain. Similarity = 100 * exp(-distance / support_radius): 100 for an identical
condition and about 37 at the typical spacing between distinct tested atmospheres.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from flameguard.prediction import DOMAIN_FEATURES, ApplicabilityDomain


def nearest_tests(tests: pd.DataFrame, domain: ApplicabilityDomain, query: dict, k: int = 5) -> pd.DataFrame:
    """The k tested conditions most similar to `query` (keys: fuel, x_o2, x_co2, x_he, d0_mm).

    `tests` needs columns fuel + DOMAIN_FEATURES; any other columns are carried through.
    Returns a copy sorted by distance with `distance` and `similarity` columns added.
    """
    if k < 1:
        raise ValueError("k must be >= 1")
    fuel = query["fuel"]
    if fuel not in domain.scale and fuel not in domain.support_radius:
        raise ValueError(f"Unknown fuel {fuel!r}")
    same = tests[tests["fuel"] == fuel].dropna(subset=DOMAIN_FEATURES).copy()
    if same.empty:
        return same.assign(distance=[], similarity=[])
    d2 = sum(((same[c].astype(float) - float(query[c])) / domain.scale[c]) ** 2 for c in DOMAIN_FEATURES)
    same["distance"] = np.sqrt(d2)
    radius = domain.support_radius[fuel]
    if radius > 0:
        same["similarity"] = 100.0 * np.exp(-same["distance"] / radius)
    else:  # no typical spacing known: only identical conditions count as similar
        same["similarity"] = np.where(same["distance"] == 0, 100.0, 0.0)
    return same.nsmallest(k, "distance")
