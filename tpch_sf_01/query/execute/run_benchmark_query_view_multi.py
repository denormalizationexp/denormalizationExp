from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass
from pathlib import Path

import psycopg2

import baseline
import generate_params

from job_utils_view import SYM2TABLE, load_template_module


RUNS = 100
SEED = 20260101

DB_CONFIG = dict(
    host="localhost",
    dbname="tpch_sf_05",
    user="<your_postgres_username>", # Enter your user_name
    password="<your_postgres_password>", # Enter your password
    port=5432
)

# Query-driven multi-view templates use the superset: query-specific
# combinations plus copied schema-driven combinations.
TEMPLATES_DIR = Path(__file__).resolve().parents[1] / "templates_multiple" / "query_driven"
RESULTS_DIR = Path(__file__).resolve().parents[1] / "results_multi_view" / "query_driven"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)


conn = psycopg2.connect(**DB_CONFIG)
cur = conn.cursor()
print("Connected to PostgreSQL")


@dataclass(frozen=True)
class MultiViewJob:
    qid: int
    tag: str
    template_file: str
    source_map: dict[str, str]
    view_src: str


def build_view_source(qid: int, component_tag: str) -> str:
    try:
        table_parts = [SYM2TABLE[symbol] for symbol in component_tag.split("_")]
    except KeyError as exc:
        raise KeyError(f"Unknown symbol {exc} in multi-template tag {component_tag}.") from None
    return f"q{qid}_view_" + "_".join(table_parts)


def build_jobs_from_multi_templates(templates_dir: Path) -> list[MultiViewJob]:
    pattern = re.compile(r"^template_(\d+)_([A-Za-z0-9_]+(?:__[A-Za-z0-9_]+)*)\.py$")
    jobs: list[MultiViewJob] = []

    for path in sorted(templates_dir.glob("template_*.py")):
        match = pattern.match(path.name)
        if not match:
            continue

        qid = int(match.group(1))
        tag = match.group(2)
        component_tags = tag.split("__")
        source_map = {
            f"source{idx}": build_view_source(qid, component_tag)
            for idx, component_tag in enumerate(component_tags, start=1)
        }
        view_src = "__".join(
            source_map[f"source{idx}"]
            for idx in range(1, len(component_tags) + 1)
        )
        jobs.append(
            MultiViewJob(
                qid=qid,
                tag=tag,
                template_file=path.name,
                source_map=source_map,
                view_src=view_src,
            )
        )

    return jobs


def warmup(cur, name: str, query: str, warmup_runs: int = 10) -> None:
    for _ in range(warmup_runs):
        cur.execute(query)
        cur.fetchall()
    print(f"Warm-up for {name} completed")


def normalize_result(rows):
    return sorted(tuple(row) for row in rows)


def validate_equivalence(cur, name: str, query: str, golden_result) -> None:
    cur.execute(query)
    result = cur.fetchall()
    if normalize_result(result) != golden_result:
        print(f"❌ Result mismatch detected in {name}")
    else:
        print(f"✅ Result equivalence verified for {name}")


def format_query(template_sql: str, source_map: dict[str, str] | None, params: dict) -> str:
    payload = dict(params)
    if source_map:
        payload.update(source_map)
    return template_sql.format(**payload)


def benchmark(cur, name: str, source_map: dict[str, str] | None, template_sql: str, params_list: list[dict], trim_ratio: float = 0.2):
    query = format_query(template_sql, source_map, params_list[0])
    warmup(cur, name, query, warmup_runs=10)

    print("========================================================================")
    print(f"Running: {name}")
    print("------------------------------------------------------------------------")
    cur.execute(query)
    preview = cur.fetchall()
    print(f"Result preview ({len(preview)} rows):")
    for row in preview[:5]:
        print(row)
    print("------------------------------------------------------------------------")

    times = []
    slow_streak = 0
    stop_threshold = 1.5

    for i, params in enumerate(params_list):
        query = format_query(template_sql, source_map, params)
        start_time = time.time()
        cur.execute(query)
        cur.fetchall()
        end_time = time.time()

        elapsed = end_time - start_time
        times.append(elapsed)
        print(f"{name} Run {i + 1}/{len(params_list)}: {elapsed:.6f}s")

        if elapsed > stop_threshold:
            slow_streak += 1
        else:
            slow_streak = 0

        if slow_streak >= 10:
            print(f"🛑 Early stop: {name} exceeded {stop_threshold}s for 10 consecutive runs.")
            break

    if 0 < trim_ratio < 0.5:
        sorted_times = sorted(times)
        cut = int(len(sorted_times) * trim_ratio)
        trimmed = sorted_times[cut:-cut] if (cut > 0 and len(sorted_times) - 2 * cut > 0) else sorted_times
    else:
        trimmed = times

    avg_time = sum(trimmed) / len(trimmed)
    print(f"{name} ==> Avg(exclude top {trim_ratio * 100:.0f}% & bottom {trim_ratio * 100:.0f}%): {avg_time:.6f}s\n")
    return {"runs": times, "trimmed_runs": trimmed, "average_time": avg_time}


def main() -> None:
    TARGET_QIDS = [2, 3, 4, 5, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22]

    # Automatically generate all jobs
    jobs = build_jobs_from_multi_templates(TEMPLATES_DIR)

    # The query filtering logic is consistent with the original run_benchmark.py.
    jobs = [job for job in jobs if job.qid in TARGET_QIDS]
    jobs.sort(key=lambda job: (TARGET_QIDS.index(job.qid), job.tag))

    results = {}

    for job in jobs:
        qid = job.qid
        tag = job.tag

        print(f"\nStart Q{qid} - {tag}  (sources={job.view_src})")

        tpl_mod = load_template_module(TEMPLATES_DIR, job.template_file)
        baseline_sql = getattr(baseline, f"BASELINE_Q{qid}")
        template_sql = getattr(tpl_mod, f"TEMPLATE_Q{qid}")
        make_params = getattr(generate_params, f"make_params_q{qid}")
        params_list = make_params(SEED, RUNS)

        print("Validating result equivalence...")
        baseline_query = baseline_sql.format(**params_list[0])
        cur.execute(baseline_query)
        baseline_result = normalize_result(cur.fetchall())

        view_query = format_query(template_sql, job.source_map, params_list[0])
        validate_equivalence(cur, f"Multi-View Q{qid} ({tag})", view_query, baseline_result)

        key = f"Q{qid}_{tag}"
        results[key] = {}
        results[key]["baseline"] = benchmark(cur, f"Baseline Q{qid} ({tag})", None, baseline_sql, params_list)
        results[key]["view"] = benchmark(
            cur,
            f"Multi-View Q{qid} ({tag})",
            job.source_map,
            template_sql,
            params_list,
        )

        out_path = RESULTS_DIR / f"result_q{qid}_{tag}.json"
        out_path.write_text(json.dumps({key: results[key]}, indent=4), encoding="utf-8")
        print(f"✅ Saved -> {out_path}")

    all_path = RESULTS_DIR / "all_results_multi_view.json"
    all_path.write_text(json.dumps(results, indent=4), encoding="utf-8")
    print(f"✅ Saved -> {all_path}")


if __name__ == "__main__":
    main()
    cur.close()
    conn.close()
