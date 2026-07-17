import time
import json
from pathlib import Path

import psycopg2

import baseline
import generate_params

from job_utils_view import build_jobs_from_templates, load_template_module


# =========================
# Config
# =========================
RUNS = 100
SEED = 20260101

DB_CONFIG = dict(
    host="localhost",
    dbname="tpch_sf_05",
    user="<your_postgres_username>", # Enter your user_name
    password="<your_postgres_password>", # Enter your password
    port=5432
)

# Schema-driven templates contain only schema-defined edges and exclude the
# query-specific C-S, L-S, and L-P edges.
TEMPLATES_DIR = Path(__file__).resolve().parents[1] / "templates" / "schema_driven"
RESULTS_DIR = Path(__file__).resolve().parents[1] / "results_view" / "schema_driven"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)


# =========================
# DB Connect
# =========================
conn = psycopg2.connect(**DB_CONFIG)
cur = conn.cursor()
print("✅ Connected to PostgreSQL")


def warmup(name, query, warmup_runs=10):
    for _ in range(warmup_runs):
        cur.execute(query)
        cur.fetchall()
    print(f"✅ Warm-up for {name} completed")


def normalize_result(rows):
    return sorted(tuple(row) for row in rows)


def validate_equivalence(name, query, golden_result):
    cur.execute(query)
    result = cur.fetchall()
    if normalize_result(result) != golden_result:
        print(f"❌ Result mismatch detected in {name}")
    else:
        print(f"✅ Result equivalence verified for {name}")


def benchmark(name, source, template, params_list, trim_ratio=0.2):
    query = template.format(**params_list[0]) if source is None else template.format(source=source, **params_list[0])
    warmup(name, query, warmup_runs=10)

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
        query = template.format(**params) if source is None else template.format(source=source, **params)

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


def main():
    # Automatically generate all jobs
    jobs = build_jobs_from_templates(TEMPLATES_DIR)

    # 2,3,4 pass
    target_qids = [2,3,4,5,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22]
    jobs = [j for j in jobs if j.qid in target_qids]
    jobs.sort(key=lambda j: target_qids.index(j.qid))

    results = {}

    for job in jobs:
        qid = job.qid
        tag = job.tag
        view_src = job.view_src

        print(f"\n🚀 Start Q{qid} - {tag}  (source={view_src})")

        tpl_mod = load_template_module(TEMPLATES_DIR, job.template_file)

        BASELINE_SQL = getattr(baseline, f"BASELINE_Q{qid}")
        TEMPLATE_SQL = getattr(tpl_mod, f"TEMPLATE_Q{qid}")

        make_params = getattr(generate_params, f"make_params_q{qid}")
        params_list = make_params(SEED, RUNS)

        # Correctness check
        print("🔎 Validating result equivalence...")
        baseline_query = BASELINE_SQL.format(**params_list[0])
        cur.execute(baseline_query)
        baseline_result = normalize_result(cur.fetchall())

        view_query = TEMPLATE_SQL.format(source=view_src, **params_list[0])
        validate_equivalence(f"View Q{qid} ({tag})", view_query, baseline_result)

        # Benchmark
        key = f"Q{qid}_{tag}"
        results[key] = {}
        results[key]["baseline"] = benchmark(f"Baseline Q{qid} ({tag})", None, BASELINE_SQL, params_list)
        results[key]["view"] = benchmark(f"View Q{qid} ({tag})", view_src, TEMPLATE_SQL, params_list)

        # save per job
        out_path = RESULTS_DIR / f"result_{view_src}.json"
        with open(out_path, "w") as f:
            json.dump({key: results[key]}, f, indent=4)
        print(f"✅ Saved -> {out_path}")

    # optionally save all
    with open(RESULTS_DIR / "all_results.json", "w") as f:
        json.dump(results, f, indent=4)
    print(f"✅ Saved -> {RESULTS_DIR / 'all_results.json'}")


if __name__ == "__main__":
    main()
    cur.close()
    conn.close()
