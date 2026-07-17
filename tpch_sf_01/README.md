# TPC-H Benchmark Experiments

This directory contains all code for reproducing the TPC-H experiments presented in the paper.

The experiments are conducted on a PostgreSQL database populated with the TPC-H benchmark at **Scale Factor 0.5 (SF=0.5)**. 
They evaluate schema-driven and query-driven denormalization techniques by comparing the performance of:

- the normalized baseline,
- single materialized views,
- multiple materialized views,
- single standard PostgreSQL views, and
- multiple standard PostgreSQL views

across the 22 TPC-H benchmark queries. In addition to query execution performance, the repository also includes experiments for evaluating materialized-view refresh costs after database updates.

## Prepare the TPC-H Database

Before running any experiments, a TPC-H database must be generated and loaded into PostgreSQL. To generate the database, use the files under
[`tpch-dbgen-Mac-main/`](tpch-dbgen-Mac-main/) and follow the instructions in
[`tpch-dbgen-Mac-main/README.md`](tpch-dbgen-Mac-main/README.md).

> **Note**
>
> You may either:
> - use **multiple PostgreSQL databases** to organize different experiments; or
> - use **a single PostgreSQL database** containing all required materialized views and standard views.
>
> In either case, ensure that the `DB_CONFIG` settings in the corresponding
> Python scripts match the target PostgreSQL database before running the
> experiments.
> 


## Configure PostgreSQL Connection

Before running any experiment script, edit the `DB_CONFIG` block in the script
you want to run. For example:

```python
DB_CONFIG = dict(
    host="localhost",
    dbname="tpch_sf_05",
    user="<your_postgres_username>",
    password="<your_postgres_password>",
    port=5432,
)
```


The directory `tpch_sf_01/` is the experiment-code folder. The actual
database name is controlled by each script's `DB_CONFIG`. Make sure it matches
the database you loaded.


## Create Denormalized Sources

The scripts for generating denormalized sources are located in
[`join_table/`](join_table/).

Before running the benchmark experiments, generate the required PostgreSQL
objects. Depending on the experiment, the benchmark runners query either
materialized views (named `q*_mv_*`) or standard PostgreSQL views (named
`q*_view_*`).

| Source Type | Query-driven | Schema-driven |
|--------------|--------------|---------------|
| **Materialized views** | [`auto_mv_table_query.py`](join_table/auto_mv_table_query.py) | [`auto_mv_table_schema.py`](join_table/auto_mv_table_schema.py) |
| **Regular views** | [`auto_mv_table_query_view.py`](join_table/auto_mv_table_query_view.py) | [`auto_mv_table_schema_view.py`](join_table/auto_mv_table_schema_view.py) |

The generated materialized views and PostgreSQL views are automatically
referenced by the benchmark runners during query execution.

> **Note:** Before executing any of these scripts, update the `DB_CONFIG`
> settings to match your PostgreSQL configuration, including the database
> name, username, and password.

## Query Performance Experiments

The `query/` directory contains all code required to reproduce the TPC-H query
performance experiments.

### Query Templates

The SQL templates used in the experiments are organized as follows:

| Configuration | Location |
|---------------|----------|
| Query-driven (single template) | [`query/templates/query_driven/`](query/templates/query_driven/) |
| Schema-driven (single template) | [`query/templates/schema_driven/`](query/templates/schema_driven/) |
| Query-driven (multiple templates) | [`query/templates_multiple/query_driven/`](query/templates_multiple/query_driven/) |
| Schema-driven (multiple templates) | [`query/templates_multiple/schema_driven/`](query/templates_multiple/schema_driven/) |

### Benchmark Runners

All benchmark runners are located in:

[`query/execute/`](query/execute/)

| Configuration | Query-driven | Schema-driven |
|---------------|--------------|---------------|
| Materialized view (single) | [`run_benchmark_query.py`](query/execute/run_benchmark_query.py) | [`run_benchmark_schema.py`](query/execute/run_benchmark_schema.py) |
| Materialized view (multiple) | [`run_benchmark_query_multi.py`](query/execute/run_benchmark_query_multi.py) | [`run_benchmark_schema_multi.py`](query/execute/run_benchmark_schema_multi.py) |
| Regular view (single) | [`run_benchmark_query_view.py`](query/execute/run_benchmark_query_view.py) | [`run_benchmark_schema_view.py`](query/execute/run_benchmark_schema_view.py) |
| Regular view (multiple) | [`run_benchmark_query_view_multi.py`](query/execute/run_benchmark_query_view_multi.py) | [`run_benchmark_schema_view_multi.py`](query/execute/run_benchmark_schema_view_multi.py) |

### Recommended Workflow

#### Materialized-view Experiments

1. Prepare the TPC-H database by following
   [`../tpch-dbgen-Mac-main/README.md`](../tpch-dbgen-Mac-main/README.md).
2. Update the `DB_CONFIG` settings in the required scripts.
3. Generate the materialized views:
   - [`join_table/auto_mv_table_query.py`](join_table/auto_mv_table_query.py)
   - [`join_table/auto_mv_table_schema.py`](join_table/auto_mv_table_schema.py)
4. Execute the desired benchmark runner from
   [`query/execute/`](query/execute/).

#### Regular-view Experiments

1. Prepare the TPC-H database by following
   [`../tpch-dbgen-Mac-main/README.md`](../tpch-dbgen-Mac-main/README.md).
2. Update the `DB_CONFIG` settings in the required scripts.
3. Generate the PostgreSQL views:
   - [`join_table/auto_mv_table_query_view.py`](join_table/auto_mv_table_query_view.py)
   - [`join_table/auto_mv_table_schema_view.py`](join_table/auto_mv_table_schema_view.py)
4. Execute the desired benchmark runner from
   [`query/execute/`](query/execute/).

> **Note:** To reproduce only a subset of the experiments (e.g., only
> query-driven or only schema-driven), generate only the corresponding
> denormalized sources and execute the matching benchmark runner(s).
### Benchmark Results

Each benchmark runner writes its results to the corresponding output directory.
The directories are created automatically when the experiments are executed.

| Experiment | Output Directory |
|------------|------------------|
| Materialized views (single) | [`query/results/`](query/results/) |
| Materialized views (multiple) | [`query/results_multiple/`](query/results_multiple/) |
| Regular views (single) | [`query/results_view/`](query/results_view/) |
| Regular views (multiple) | [`query/results_multi_view/`](query/results_multi_view/) |

The generated JSON files contain the benchmark results used for the performance
analysis in the paper.

## Materialized-View Refresh Experiments

The `refresh/` directory contains all code required to reproduce the
materialized-view refresh experiments. These experiments evaluate the cost of
refreshing materialized views after incremental updates to the TPC-H base
tables.

### Refresh Script

The refresh experiment is implemented by:

[`refresh/scripts/refresh_run_05.py`](refresh/scripts/refresh_run_05.py)

This script performs the complete refresh workflow, including:

- inserting incremental TPC-H tuples into the base tables;
- executing `REFRESH MATERIALIZED VIEW`;
- verifying the refreshed materialized views against rebuilt reference views;
- deleting the inserted tuples; and
- refreshing the materialized views again to measure deletion costs.

### Refresh Data

The incremental update files are located in:

[`refresh/tbl_sf_05_refresh/tbl_sf_05_insert/`](refresh/tbl_sf_05_refresh/tbl_sf_05_insert/)

These `.tbl.u1` files contain the incremental tuples inserted during the
refresh experiments.

### Recommended Workflow

1. Prepare the base TPC-H database by following
   [`../tpch-dbgen-Mac-main/README.md`](../tpch-dbgen-Mac-main/README.md).
2. Create a dedicated PostgreSQL database for the refresh experiments (e.g.,
   `tpch_sf_05_refresh`) and load the TPC-H base tables.
3. Ensure that the incremental `.tbl.u1` files are located in
   [`refresh/tbl_sf_05_refresh/tbl_sf_05_insert/`](refresh/tbl_sf_05_refresh/tbl_sf_05_insert/).
4. Update the `DB_CONFIG` settings in
   [`refresh/scripts/refresh_run_05.py`](refresh/scripts/refresh_run_05.py).
5. Execute the refresh script.

> **Note:** The refresh experiment modifies the base tables by inserting and
> deleting tuples during execution. It is therefore recommended to perform the
> experiment on a dedicated PostgreSQL database rather than on the database
> used for the query performance benchmarks.

### Refresh Results

The refresh results are written automatically to:

[`refresh/result/mv_refresh_05.json`](refresh/result/mv_refresh_05.json)

The JSON file is generated when the experiment is executed and contains the
measured materialized-view refresh costs.