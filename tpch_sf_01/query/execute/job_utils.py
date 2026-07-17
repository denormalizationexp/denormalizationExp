from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import importlib.util
import re
from typing import Dict, List, Optional


# TPCH symbol -> table name mapping
SYM2TABLE: Dict[str, str] = {
    "N": "nation",
    "R": "region",
    "S": "supplier",
    "C": "customer",
    "O": "orders",
    "L": "lineitem",
    "P": "part",
    "PS": "partsupp",
    "N1": "nation1",
    "N2": "nation2",
}


@dataclass(frozen=True)
class Job:
    qid: int
    tag: str
    template_file: str
    mv_src: str


def build_jobs_from_templates(
    templates_dir: Path,
    sym2table: Dict[str, str] = SYM2TABLE,
    mv_override: Optional[Dict[str, str]] = None,
) -> List[Job]:
    """
    Recursively scan templates_dir for files named: template_<qid>_<TAG>.py.
    Duplicate qid/tag pairs are skipped, which lets category directories keep
    copied templates without double-running them from the parent directory.
    Example: template_2_PS_S_N_R.py -> qid=2, tag=PS_S_N_R

    mv_src default rule:
        q{qid}_mv_<table names joined by underscore>
        e.g., template_2_PS_S.py -> q2_mv_partsupp_supplier
    """
    mv_override = mv_override or {}

    pat = re.compile(r"^template_(\d+)_([A-Za-z0-9_]+)\.py$")
    jobs: List[Job] = []
    seen = set()

    for p in sorted(templates_dir.rglob("template_*.py")):
        m = pat.match(p.name)
        if not m:
            continue

        qid = int(m.group(1))
        tag = m.group(2)
        key = (qid, tag)
        if key in seen:
            continue
        seen.add(key)

        syms = tag.split("_")

        # tag -> table list
        try:
            table_parts = [sym2table[s] for s in syms]
        except KeyError as e:
            raise KeyError(f"Unknown symbol {e} in {p.name}. Add it into SYM2TABLE.") from None

        mv_src = f"q{qid}_mv_" + "_".join(table_parts)
        mv_src = mv_override.get(p.name, mv_src)

        template_file = p.relative_to(templates_dir).as_posix()
        jobs.append(Job(qid=qid, tag=tag, template_file=template_file, mv_src=mv_src))

    return jobs


def load_template_module(templates_dir: Path, template_filename: str):
    """
    Load a python figures as a module by figures path.
    This avoids package/sys.path issues and works well for scripts.
    """
    tpl_path = templates_dir / template_filename
    if not tpl_path.exists():
        raise FileNotFoundError(f"Template figures not found: {tpl_path}")

    module_name = tpl_path.stem  # e.g. template_2_PS_S
    spec = importlib.util.spec_from_file_location(module_name, tpl_path)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod
