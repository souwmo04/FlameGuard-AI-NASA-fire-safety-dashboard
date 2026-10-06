"""NASA sources behind every number the API serves. Only sources actually used are listed."""

from __future__ import annotations

from app.schemas.common import SourceRef
from app.schemas.responses import Source

SOURCES: list[Source] = [
    Source(
        id="psi-69",
        title="Flame Extinguishment Experiment (FLEX) — NASA Physical Sciences Informatics PSI-69",
        kind="dataset",
        publisher="NASA Physical Sciences Informatics",
        url="https://psi.nasa.gov/physci/repo/data/investigations/PSI-69",
        doi="10.60555/mbq8-0451",
        license="CC0-1.0",
        citation="NASA Physical Sciences Informatics. Flame Extinguishment Experiment (FLEX), PSI-69. "
                 "https://doi.org/10.60555/mbq8-0451",
        used_for="All experiment records (274 ISS droplet-combustion tests) and model training data.",
    ),
    Source(
        id="nasa-tp-2015-216046",
        title="Detailed Results from the Flame Extinguishment Experiment (FLEX) March 2009 to December 2011",
        kind="report",
        publisher="NASA (Technical Publication NASA/TP-2015-216046)",
        url="https://ntrs.nasa.gov/citations/20150023456",
        doi=None,
        license=None,
        citation="Dietrich, D. L., Ferkul, P. V., Bryg, V. M., Nayagam, M. V., Hicks, M. C., Williams, F. A., "
                 "Dryer, F. L., Shaw, B. D., Choi, M. Y., Avedisian, C. T. (2015). Detailed Results from the Flame "
                 "Extinguishment Experiment (FLEX) March 2009 to December 2011. NASA/TP-2015-216046.",
        used_for="Column and outcome definitions (Extinction / Completion / Disruption), per-test notes.",
    ),
]

SOURCE_BY_ID = {s.id: s for s in SOURCES}


def source_ref(source_id: str) -> SourceRef:
    s = SOURCE_BY_ID[source_id]
    return SourceRef(id=s.id, title=s.title, url=s.url, doi=s.doi)
