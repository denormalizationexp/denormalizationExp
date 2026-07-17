# TPC-H data download and generation workflow

We will explain how to obtain the TPC-H data used in this experiment, how to generate the SF=0.5 base data, how to load it into PostgreSQL, and how to use the prepared refresh data.

## Data source

Choose one of the following paths based on your environment:

- Mac users: use the DBGEN files included in this experiment under `tpch-dbgen-Mac-main/dbgen/` to generate the base `.tbl` files.
- Non-Mac users: download the official TPC-H tools directly from the TPC website, then use the `dbgen` included in the downloaded package.

Official TPC download page:

https://www.tpc.org/tpc_documents_current_versions/current_specifications5.asp

On that page, find `TPC-H` in the Active Benchmarks table and use the Source Code link. It is currently listed as `Download TPC-H_Tools_v3.0.1.zip`. The TPC download flow may require registration and license acceptance.

## Generate the SF=0.5 base data

First, use dbgen to build the generator and create TPC-H .tbl files.

```bash
make clean 2>/dev/null || true

make -f makefile.suite \
  CC=clang \
  CFLAGS="-O -std=gnu89 -DLINUX -DTPCH -DINFORMIX"
```

Generate data with:
```bash
./dbgen -s 05
```

This generates the `.tbl` data files. In practice, these `.tbl` files are usually created inside the dbgen directory.

It is often convenient to create a separate folder, for example, tbl_sf_05, and move all generated .tbl files into it:

```bash
mkdir -p dbgen/tbl_sf_05
mv dbgen/*.tbl dbgen/tbl_sf_05/
```

After that, use the new folder path when preparing the PostgreSQL load commands. Then, use the files in `dbgen_for_psql` to load the generated data into PostgreSQL.


## Load the base data into PostgreSQL

Create the SF=0.5 database:

```bash
createdb tpch_sf_05
```

Create the PostgreSQL schema by running the script in `dbgen_for_sql`:

```bash
psql -U <user> -d tpch_sf_05 -f create_table_psql_with_dummy_pk_fk.sql
```

Edit `tpch-dbgen-Mac-main/dbgen_for_psql/add_data.txt` so every `\copy` path points to your generated `tbl_sf_05` directory. If you used the commands above, the data directory is:

```text
tpch-dbgen-Mac-main/dbgen/tbl_sf_05/
```

Load the generated `.tbl` data using the commends in:

```bash
add_data.txt
```

After the data is loaded, remove the dummy columns by running:

```bash
psql -U <user> -d tpch_sf_05 -f tpch_drop_dummy_columns.sql
```

Connect to the database with:

```bash
psql -d tpch_sf_05
```

Or for a remote server:

```bash
psql -h <host> -U <user> -d tpch_sf_05
```


## Generate and use the SF=0.5 refresh data

The files under `dbgen_for_refresh` are a modified version of DBGEN that can
generate refresh rows for individual TPC-H tables. Build this version of DBGEN
from the project root:

```bash
cd tpch-dbgen-Mac-main/dbgen_for_refresh

make -f makefile.suite clean 2>/dev/null || true
make -f makefile.suite \
  CC=clang \
  CFLAGS="-O -std=gnu89 -DLINUX -DTPCH -DINFORMIX"
```

Generate the first refresh set for SF=0.5. The table arguments used below are
`c` for customer, `P` for part, `S` for partsupp, and `o` for the
orders/lineitem pair:

```bash
./dbgen -s 0.5 -U 1 -T c -f
./dbgen -s 0.5 -U 1 -T P -f
./dbgen -s 0.5 -U 1 -T S -f
./dbgen -s 0.5 -U 1 -T o -f
```

Here, `-s 0.5` selects SF=0.5, `-U 1` generates one refresh set, and `-f`
allows existing output files to be overwritten. The insert files required by
the experiment are generated in:

```text
tpch_sf_01/refresh/tbl_sf_05_refresh/tbl_sf_05_insert/
```

This directory contains:

| file | rows |
|---|---:|
| `customer.tbl.u1` | 70 |
| `part.tbl.u1` | 100 |
| `partsupp.tbl.u1` | 400 |
| `orders.tbl.u1` | 750 |
| `lineitem.tbl.u1` | 2,981 |

DBGEN also generates files named `delete.<table>.1`. These delete files are
not used in this experiment. The experiment first inserts the rows from the
five `*.tbl.u1` files, then performs the delete phase by deleting those same
inserted rows from the database in reverse table order.

These files are used by `tpch_sf_01/refresh/scripts/refresh_run_05.py`. The script reads the refresh files, inserts the update rows into the base tables, refreshes the materialized views, verifies the refreshed results, deletes the inserted update rows, refreshes again, and writes timing results to:

```text
tpch_sf_01/refresh/result/mv_refresh_05.json
```

Before running the script, prepare a PostgreSQL database named `tpch_sf_05_refresh` and load the SF=0.5 base data into it. Then update `DB_CONFIG` in:

```text
tpch_sf_01/refresh/scripts/refresh_run_05.py
```

Run the refresh experiment from the project root:

```bash
python tpch_sf_01/refresh/scripts/refresh_run_05.py
```

The script uses this insert order internally:

```text
customer -> part -> partsupp -> orders -> lineitem
```

It deletes the refresh rows in the reverse order.
