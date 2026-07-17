import json
import re
from collections import Counter
from contextlib import redirect_stdout
from datetime import datetime
from decimal import Decimal
from io import StringIO
from itertools import combinations
from pathlib import Path
from time import perf_counter

import psycopg2
from psycopg2 import sql
from psycopg2.extras import execute_values


SCRIPT_DIR = Path(__file__).resolve().parent
BASE_DIR = SCRIPT_DIR.parent
DATA_DIR = BASE_DIR / "tbl_sf_05_refresh" / "tbl_sf_05_insert"
OUTPUT_DIR = BASE_DIR / "result"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_JSON = OUTPUT_DIR / "mv_refresh_05.json"

DB_CONFIG = dict(
    host="localhost",
    dbname="tpch_sf_05_refresh",
    user="<your_postgres_username>", # Enter your user_name
    password="<your_postgres_password>", # Enter your password
    port=5432,
)

REPEATS = 1
MAX_ESTIMATED_ROWS = 20_000_000
BATCH_SIZE = 1000
EXPLAIN_ROWS_RE = re.compile(r"rows=(\d+)", re.IGNORECASE)

CUSTOMER_FILE = DATA_DIR / "customer.tbl.u1"
SUPPLIER_FILE = DATA_DIR / "supplier.tbl.u1"
PART_FILE = DATA_DIR / "part.tbl.u1"
PARTSUPP_FILE = DATA_DIR / "partsupp.tbl.u1"
ORDERS_FILE = DATA_DIR / "orders.tbl.u1"
LINEITEM_FILE = DATA_DIR / "lineitem.tbl.u1"

groups = [
    (2, [("P", "PS"), ("S", "PS"), ("S", "N"), ("N", "R")]),
    (3, [("L", "O"), ("O", "C")]),
    (4, [("L", "O")]),
    (5, [("L", "O"), ("O", "C"), ("C", "S"), ("L", "S"), ("S", "N"), ("N", "R")]),
    (7, [("L", "O"), ("O", "C"), ("C", "N2"), ("L", "S"), ("S", "N1")]),
    (8, [("L", "O"), ("L", "P"), ("O", "C"), ("C", "N1"), ("L", "S"), ("S", "N2"), ("N1", "R")]),
    (9, [("L", "O"), ("L", "P"), ("L", "PS"), ("L", "S"), ("S", "N")]),
    (10, [("L", "O"), ("O", "C"), ("C", "N")]),
    (11, [("PS", "S"), ("S", "N")]),
    (12, [("L", "O")]),
    (13, [("O", "C")]),
    (14, [("L", "P")]),
    (15, [("L", "S")]),
    (16, [("PS", "P"), ("PS", "S")]),
    (17, [("L", "P")]),
    (18, [("L", "O"), ("O", "C")]),
    (19, [("L", "P")]),
    (20, [("L", "PS"), ("PS", "P"), ("PS", "S"), ("S", "N")]),
    (21, [("L", "S"), ("L", "O"), ("S", "N")]),
    (22, [("O", "C")]),
]

TABLE_MAP = {
    "L": "lineitem",
    "O": "orders",
    "C": "customer",
    "S": "supplier",
    "N": "nation",
    "N1": "nation",
    "N2": "nation",
    "R": "region",
    "P": "part",
    "PS": "partsupp",
}

DISPLAY_NAME_MAP = {
    "L": "lineitem",
    "O": "orders",
    "C": "customer",
    "S": "supplier",
    "N": "nation",
    "N1": "nation1",
    "N2": "nation2",
    "R": "region",
    "P": "part",
    "PS": "partsupp",
}

MV_RULES = {
    ("L", "O"): ("l_orderkey", "o_orderkey"),
    ("O", "C"): ("o_custkey", "c_custkey"),
    ("C", "N"): ("c_nationkey", "n_nationkey"),
    ("S", "N"): ("s_nationkey", "n_nationkey"),
    ("N", "R"): ("n_regionkey", "r_regionkey"),
    ("C", "N1"): ("c_nationkey", "n_nationkey"),
    ("C", "N2"): ("c_nationkey", "n_nationkey"),
    ("S", "N1"): ("s_nationkey", "n_nationkey"),
    ("S", "N2"): ("s_nationkey", "n_nationkey"),
    ("N1", "R"): ("n_regionkey", "r_regionkey"),
    ("L", "S"): ("l_suppkey", "s_suppkey"),
    ("L", "P"): ("l_partkey", "p_partkey"),
    ("L", "PS"): (("l_partkey", "l_suppkey"), ("ps_partkey", "ps_suppkey")),
    ("PS", "S"): ("ps_suppkey", "s_suppkey"),
    ("PS", "P"): ("ps_partkey", "p_partkey"),
    ("C", "S"): ("c_nationkey", "s_nationkey"),
}

CANONICAL_ORDER = ["L", "O", "C", "PS", "S", "P", "N", "N1", "N2", "R"]

CUSTOMER_COLUMNS = (
    "c_custkey", "c_name", "c_address", "c_nationkey", "c_phone", "c_acctbal", "c_mktsegment", "c_comment"
)
SUPPLIER_COLUMNS = (
    "s_suppkey", "s_name", "s_address", "s_nationkey", "s_phone", "s_acctbal", "s_comment"
)
PART_COLUMNS = (
    "p_partkey", "p_name", "p_mfgr", "p_brand", "p_type", "p_size", "p_container", "p_retailprice", "p_comment"
)
PARTSUPP_COLUMNS = ("ps_partkey", "ps_suppkey", "ps_availqty", "ps_supplycost", "ps_comment")
ORDERS_COLUMNS = (
    "o_orderkey", "o_custkey", "o_orderstatus", "o_totalprice", "o_orderdate", "o_orderpriority",
    "o_clerk", "o_shippriority", "o_comment"
)
LINEITEM_COLUMNS = (
    "l_orderkey", "l_partkey", "l_suppkey", "l_linenumber", "l_quantity", "l_extendedprice", "l_discount",
    "l_tax", "l_returnflag", "l_linestatus", "l_shipdate", "l_commitdate", "l_receiptdate", "l_shipinstruct",
    "l_shipmode", "l_comment"
)


def run_quietly(func, *args, **kwargs):
    buffer = StringIO()
    with redirect_stdout(buffer):
        result = func(*args, **kwargs)
    return result, buffer.getvalue()


def print_experiment_header(target, repeat_index: int):
    print("")
    print("=" * 80)
    print(f"[experiment] MV: {target['mv_name']}")
    print(f"[experiment] Combo: {target['combo_name']}")
    print(f"[experiment] Repeat: {repeat_index}")
    print("=" * 80)


def print_stage(title: str):
    print("")
    print(f"[stage] {title}")


def print_info(label: str, value):
    print(f"  [info] {label}: {value}")


def print_time(label: str, seconds: float):
    print(f"  [time] {label}: {seconds:.6f}s")


def verify_mv_name(mv_name: str) -> str:
    if mv_name.startswith("mv_"):
        return "verify_" + mv_name[3:]
    return f"verify_{mv_name}"


def safe_ident(name: str) -> str:
    name = re.sub(r"[^a-zA-Z0-9_]", "_", name)
    if name and name[0].isdigit():
        name = "t_" + name
    return name


def sym_rank(x: str) -> int:
    return CANONICAL_ORDER.index(x) if x in CANONICAL_ORDER else 999


def canonical_edge(edge):
    a, b = edge
    return (a, b) if sym_rank(a) <= sym_rank(b) else (b, a)


def aliases_for_symbols(syms):
    return {s: s.lower() for s in syms}


def get_keys(a: str, b: str):
    if (a, b) in MV_RULES:
        return MV_RULES[(a, b)]
    if (b, a) in MV_RULES:
        k1, k2 = MV_RULES[(b, a)]
        return k2, k1
    raise KeyError(f"No rule for edge ({a},{b})")


def induced_edges(full_edges, node_set):
    edges = []
    for a, b in full_edges:
        a, b = canonical_edge((a, b))
        if a in node_set and b in node_set:
            edges.append((a, b))
    return sorted(set(edges), key=lambda x: (sym_rank(x[0]), sym_rank(x[1]), x[0], x[1]))


def canonical_nodes_from_edges(full_edges):
    nodes = set()
    for a, b in full_edges:
        a, b = canonical_edge((a, b))
        nodes.add(a)
        nodes.add(b)
    return sorted(nodes, key=lambda x: (sym_rank(x), x))


def is_connected(node_set, edges) -> bool:
    if len(node_set) < 2 or not edges:
        return False
    adj = {n: set() for n in node_set}
    for a, b in edges:
        adj[a].add(b)
        adj[b].add(a)
    start = next(iter(node_set))
    seen = {start}
    stack = [start]
    while stack:
        u = stack.pop()
        for v in adj.get(u, set()):
            if v not in seen:
                seen.add(v)
                stack.append(v)
    return seen == node_set


def enumerate_connected_node_sets(full_edges):
    nodes = canonical_nodes_from_edges(full_edges)
    out = []
    for k in range(2, len(nodes) + 1):
        for comb in combinations(nodes, k):
            node_set = set(comb)
            edges = induced_edges(full_edges, node_set)
            if is_connected(node_set, edges):
                out.append(node_set)
    return out


def required_edges_for_symbols(syms):
    node_set = set(syms)
    edges = induced_edges(list(MV_RULES.keys()), node_set)
    if not is_connected(node_set, edges):
        raise ValueError(f"Symbols do not form a connected join graph: {sorted(node_set)}")
    return edges


def build_join_predicate(a: str, b: str, alias):
    lk, rk = get_keys(a, b)
    aa, bb = alias[a], alias[b]
    if isinstance(lk, tuple):
        return "(" + " AND ".join([f'{aa}."{l}" = {bb}."{r}"' for l, r in zip(lk, rk)]) + ")"
    return f'({aa}."{lk}" = {bb}."{rk}")'


def build_adjacency(edge_set):
    adj = {}
    for a, b in edge_set:
        adj.setdefault(a, set()).add(b)
        adj.setdefault(b, set()).add(a)
    return adj


def shortest_distances(start: str, adj, blocked=None):
    blocked = blocked or set()
    if start in blocked:
        return {}
    dist = {start: 0}
    queue = [start]
    idx = 0
    while idx < len(queue):
        u = queue[idx]
        idx += 1
        for v in sorted(adj.get(u, set()), key=lambda x: (sym_rank(x), x)):
            if v in blocked or v in dist:
                continue
            dist[v] = dist[u] + 1
            queue.append(v)
    return dist


def customer_preserving_nodes(syms, edge_set):
    if "C" not in syms or "O" not in syms:
        return set()
    adj = build_adjacency(edge_set)
    dist = shortest_distances("O", adj, blocked={"C"})
    return set(dist.keys())


def build_from_join_clause(syms, edge_set, alias):
    preserve_customer = "C" in syms and "O" in syms
    nullable_nodes = customer_preserving_nodes(syms, edge_set) if preserve_customer else set()
    root = "C" if preserve_customer else syms[0]
    adj = build_adjacency(edge_set)
    dist_from_root = shortest_distances(root, adj)
    dist_from_o = shortest_distances("O", adj, blocked={"C"}) if preserve_customer else {}
    joined = {root}
    clauses = [f"{TABLE_MAP[root]} {alias[root]}"]

    while len(joined) < len(syms):
        candidates = [s for s in syms if s not in joined and any(n in joined for n in adj.get(s, set()))]
        if not candidates:
            raise ValueError(f"Unable to build join tree for nodes={syms}, edges={edge_set}")

        def candidate_key(s):
            is_nullable = 0 if s in nullable_nodes else 1
            branch_dist = dist_from_o.get(s, 10**9) if s in nullable_nodes else dist_from_root.get(s, 10**9)
            return (is_nullable, branch_dist, sym_rank(s), s)

        child = min(candidates, key=candidate_key)
        joined_neighbors = sorted([n for n in adj.get(child, set()) if n in joined], key=lambda x: (sym_rank(x), x))

        if child in nullable_nodes:
            parent = min(
                joined_neighbors,
                key=lambda x: (0 if x in nullable_nodes else 1, dist_from_o.get(x, 10**9), sym_rank(x), x),
            )
            join_type = "LEFT JOIN"
        else:
            parent = min(joined_neighbors, key=lambda x: (dist_from_root.get(x, 10**9), sym_rank(x), x))
            join_type = "INNER JOIN"

        on_parts = [build_join_predicate(parent, child, alias)]
        extra_neighbors = [n for n in joined_neighbors if n != parent]
        for n in extra_neighbors:
            on_parts.append(build_join_predicate(n, child, alias))

        clauses.append(f'{join_type} {TABLE_MAP[child]} {alias[child]} ON ' + " AND ".join(on_parts))
        joined.add(child)

    return "\n            ".join(clauses)


def get_table_columns(cur, table_name: str, schema: str = "public"):
    cur.execute(
        """
        SELECT column_name
        FROM information_schema.columns
        WHERE table_schema=%s AND table_name=%s
        ORDER BY ordinal_position
        """,
        (schema, table_name),
    )
    return [row[0] for row in cur.fetchall()]


def strip_table_prefix(col: str, base_table: str) -> str:
    if base_table == "nation" and col.startswith("n_"):
        return col[2:]
    return col


def build_select_list_pretty_nation_only(cur, syms, alias, schema: str = "public"):
    base_tables = [TABLE_MAP[s] for s in syms]
    cnt = Counter(base_tables)
    parts = []
    for s in syms:
        tbl = TABLE_MAP[s]
        al = alias[s]
        if cnt[tbl] == 1:
            parts.append(f"{al}.*")
            continue
        cols = get_table_columns(cur, tbl, schema=schema)
        for col in cols:
            out_col = strip_table_prefix(col, tbl)
            parts.append(f'{al}."{col}" AS {al}_{out_col}')
    return ",\n        ".join(parts)


def estimate_rows_by_explain(cur, select_sql: str) -> int:
    cur.execute("EXPLAIN " + select_sql)
    lines = [row[0] for row in cur.fetchall()]
    max_rows = 0
    for line in lines:
        match = EXPLAIN_ROWS_RE.search(line)
        if match:
            max_rows = max(max_rows, int(match.group(1)))
    return max_rows


def combo_mv_name(node_set) -> str:
    syms = tuple(sorted(node_set, key=lambda x: (sym_rank(x), x)))
    tables_part = "_".join(DISPLAY_NAME_MAP[s] for s in syms)
    return safe_ident(f"mv_{tables_part}")


def create_mv_from_definition(cur, conn, mv: str, syms, edges, label: str):
    alias = aliases_for_symbols(syms)
    from_join_clause = build_from_join_clause(syms, edges, alias)
    select_list = build_select_list_pretty_nation_only(cur, syms, alias, schema="public")
    select_sql = f"""
        SELECT
            {select_list}
        FROM {from_join_clause}
        """.strip()

    try:
        est_rows = estimate_rows_by_explain(cur, select_sql)
        if est_rows >= MAX_ESTIMATED_ROWS:
            return
    except Exception:
        pass

    drop_sql = sql.SQL("DROP MATERIALIZED VIEW IF EXISTS {} CASCADE").format(sql.Identifier(mv))
    create_sql_str = f"""
    CREATE MATERIALIZED VIEW "{mv}" AS
    {select_sql};
    """.strip()

    try:
        cur.execute(drop_sql)
        cur.execute(create_sql_str)
        conn.commit()
        cur.execute(sql.SQL("ANALYZE {}").format(sql.Identifier(mv)))
        conn.commit()
    except Exception:
        conn.rollback()
        raise


def create_mv_for_symbols(cur, conn, symbols, mv_name_override=None):
    syms = tuple(sorted(set(symbols), key=lambda x: (sym_rank(x), x)))
    edges = required_edges_for_symbols(syms)
    mv = mv_name_override or combo_mv_name(set(syms))
    create_mv_from_definition(cur, conn, mv, syms, edges, label="COMBO")


def all_mv_targets():
    deduped_targets = {}
    for _, full_edges in groups:
        canonical_edges = [canonical_edge(edge) for edge in full_edges]
        for node_set in enumerate_connected_node_sets(canonical_edges):
            syms = tuple(sorted(node_set, key=lambda x: (sym_rank(x), x)))
            join_edges = induced_edges(canonical_edges, set(syms))
            if not join_edges:
                continue
            deduped_targets[syms] = {
                "symbols": syms,
                "join_edges": join_edges,
                "mv_name": combo_mv_name(set(syms)),
                "combo_name": "_".join(syms),
            }
    targets = list(deduped_targets.values())
    targets.sort(key=lambda item: (len(item["symbols"]), item["symbols"]))
    return targets


def mv_exists(cur, mv_name: str):
    cur.execute(
        """
        SELECT 1
        FROM pg_matviews
        WHERE schemaname = 'public' AND matviewname = %s
        """,
        (mv_name,),
    )
    return cur.fetchone() is not None


def drop_mv_if_exists(cur, conn, mv_name: str):
    cur.execute(sql.SQL("DROP MATERIALIZED VIEW IF EXISTS {} CASCADE").format(sql.Identifier(mv_name)))
    conn.commit()


def create_mv_if_missing(cur, conn, target):
    if mv_exists(cur, target["mv_name"]):
        return {"created": False, "already_exists": True}
    start = perf_counter()
    run_quietly(create_mv_for_symbols, cur, conn, target["symbols"], mv_name_override=target["mv_name"])
    conn.commit()
    elapsed = perf_counter() - start
    return {"created": True, "already_exists": False, "create_seconds": elapsed}


def refresh_mv(cur, conn, mv_name: str):
    start = perf_counter()
    cur.execute(f'REFRESH MATERIALIZED VIEW "{mv_name}";')
    conn.commit()
    return perf_counter() - start


def create_verify_mv(cur, conn, target, verify_name: str):
    start = perf_counter()
    run_quietly(create_mv_for_symbols, cur, conn, target["symbols"], mv_name_override=verify_name)
    conn.commit()
    return perf_counter() - start


def fetch_scalar(cur, sql_text: str):
    cur.execute(sql_text)
    row = cur.fetchone()
    return row[0] if row else 0


def compare_mvs_match_only(cur, original_mv_name: str, verify_mv_name_value: str):
    missing_count = fetch_scalar(
        cur,
        f"""
        SELECT COUNT(*)
        FROM (
            SELECT * FROM {verify_mv_name_value}
            EXCEPT ALL
            SELECT * FROM {original_mv_name}
        ) AS missing_rows
        """.strip(),
    )
    extra_count = fetch_scalar(
        cur,
        f"""
        SELECT COUNT(*)
        FROM (
            SELECT * FROM {original_mv_name}
            EXCEPT ALL
            SELECT * FROM {verify_mv_name_value}
        ) AS extra_rows
        """.strip(),
    )
    return missing_count == 0 and extra_count == 0


def parse_date(value: str):
    return datetime.strptime(value, "%Y-%m-%d").date()


def parse_row(raw_line: str, expected_len: int):
    parts = raw_line.rstrip("\n").split("|")
    if parts and parts[-1] == "":
        parts.pop()
    if len(parts) != expected_len:
        raise ValueError(f"Invalid row with {len(parts)} columns: {raw_line!r}")
    return parts


def parse_customer_row(raw_line: str):
    parts = parse_row(raw_line, len(CUSTOMER_COLUMNS))
    return (int(parts[0]), parts[1], parts[2], int(parts[3]), parts[4], Decimal(parts[5]), parts[6], parts[7])


def parse_supplier_row(raw_line: str):
    parts = parse_row(raw_line, len(SUPPLIER_COLUMNS))
    return (int(parts[0]), parts[1], parts[2], int(parts[3]), parts[4], Decimal(parts[5]), parts[6])


def parse_part_row(raw_line: str):
    parts = parse_row(raw_line, len(PART_COLUMNS))
    return (int(parts[0]), parts[1], parts[2], parts[3], parts[4], int(parts[5]), parts[6], Decimal(parts[7]), parts[8])


def parse_partsupp_row(raw_line: str):
    parts = parse_row(raw_line, len(PARTSUPP_COLUMNS))
    return (int(parts[0]), int(parts[1]), int(parts[2]), Decimal(parts[3]), parts[4])


def parse_orders_row(raw_line: str):
    parts = parse_row(raw_line, len(ORDERS_COLUMNS))
    return (
        int(parts[0]), int(parts[1]), parts[2], Decimal(parts[3]), parse_date(parts[4]), parts[5], parts[6], int(parts[7]), parts[8]
    )


def parse_lineitem_row(raw_line: str):
    parts = parse_row(raw_line, len(LINEITEM_COLUMNS))
    return (
        int(parts[0]), int(parts[1]), int(parts[2]), int(parts[3]), Decimal(parts[4]), Decimal(parts[5]),
        Decimal(parts[6]), Decimal(parts[7]), parts[8], parts[9], parse_date(parts[10]), parse_date(parts[11]),
        parse_date(parts[12]), parts[13], parts[14], parts[15]
    )


def batched_file_rows(file_path: Path, parser, batch_size: int):
    batch = []
    with file_path.open("r", encoding="utf-8") as handle:
        for line_number, raw_line in enumerate(handle, start=1):
            if not raw_line.strip():
                continue
            try:
                batch.append(parser(raw_line))
            except Exception as exc:
                raise ValueError(f"Failed to parse {file_path.name} at line {line_number}") from exc
            if len(batch) >= batch_size:
                yield batch
                batch = []
    if batch:
        yield batch


def batched_key_rows(rows, batch_size: int):
    for start in range(0, len(rows), batch_size):
        yield rows[start:start + batch_size]


def insert_batches(cursor, table_name: str, columns, row_batches):
    sql_text = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES %s"
    inserted_rows = 0
    for batch in row_batches:
        execute_values(cursor, sql_text, batch, page_size=len(batch))
        inserted_rows += len(batch)
    return inserted_rows


def insert_optional_file(cursor, table_name: str, columns, file_path: Path, parser):
    if not file_path.exists():
        return 0
    return insert_batches(cursor, table_name, columns, batched_file_rows(file_path, parser, BATCH_SIZE))


def count_planned_rows(file_path: Path):
    if not file_path.exists():
        return 0
    count = 0
    with file_path.open("r", encoding="utf-8") as handle:
        for raw_line in handle:
            if raw_line.strip():
                count += 1
    return count


def load_unique_key_tuples_from_insert(file_path: Path, key_indexes):
    if not file_path.exists():
        return []
    keys = []
    seen = set()
    with file_path.open("r", encoding="utf-8") as handle:
        for line_number, raw_line in enumerate(handle, start=1):
            value = raw_line.strip()
            if not value:
                continue
            parts = value.split("|")
            if parts and parts[-1] == "":
                parts.pop()
            try:
                key = tuple(int(parts[idx]) for idx in key_indexes)
            except Exception as exc:
                raise ValueError(
                    f"Failed to parse primary key columns {key_indexes} from {file_path.name} at line {line_number}"
                ) from exc
            if key not in seen:
                keys.append(key)
                seen.add(key)
    return keys


def delete_by_keys(cursor, table_name: str, key_columns, rows):
    if not rows:
        return 0
    deleted_rows = 0
    key_list = ", ".join(key_columns)
    join_conditions = " AND ".join(f"t.{col} = v.{col}" for col in key_columns)
    sql_text = f"DELETE FROM {table_name} t USING (VALUES %s) AS v({key_list}) WHERE {join_conditions}"
    for batch in batched_key_rows(rows, BATCH_SIZE):
        execute_values(cursor, sql_text, batch, page_size=len(batch))
        deleted_rows += cursor.rowcount
    return deleted_rows


def fetch_table_count(cursor, table_name: str):
    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
    return cursor.fetchone()[0]


def _run_with_cursor(conn, cursor, action):
    if cursor is not None:
        return action(cursor)
    if conn is None:
        raise ValueError("insert_refresh_data/delete_refresh_data requires an existing conn or cursor")
    with conn.cursor() as cur:
        return action(cur)


def insert_refresh_data(conn=None, cursor=None, emit_summary: bool = True):
    start_time = perf_counter()
    planned_counts = {
        "customer": count_planned_rows(CUSTOMER_FILE),
        "supplier": count_planned_rows(SUPPLIER_FILE),
        "part": count_planned_rows(PART_FILE),
        "partsupp": count_planned_rows(PARTSUPP_FILE),
        "orders": count_planned_rows(ORDERS_FILE),
        "lineitem": count_planned_rows(LINEITEM_FILE),
    }

    def do_insert(cur):
        before_counts = {}
        after_counts = {}
        for table_name in ("customer", "supplier", "part", "partsupp", "orders", "lineitem"):
            before_counts[table_name] = fetch_table_count(cur, table_name)
        customer_rows = insert_optional_file(cur, "customer", CUSTOMER_COLUMNS, CUSTOMER_FILE, parse_customer_row)
        supplier_rows = insert_optional_file(cur, "supplier", SUPPLIER_COLUMNS, SUPPLIER_FILE, parse_supplier_row)
        part_rows = insert_optional_file(cur, "part", PART_COLUMNS, PART_FILE, parse_part_row)
        partsupp_rows = insert_optional_file(cur, "partsupp", PARTSUPP_COLUMNS, PARTSUPP_FILE, parse_partsupp_row)
        orders_rows = insert_batches(cur, "orders", ORDERS_COLUMNS, batched_file_rows(ORDERS_FILE, parse_orders_row, BATCH_SIZE))
        lineitem_rows = insert_batches(cur, "lineitem", LINEITEM_COLUMNS, batched_file_rows(LINEITEM_FILE, parse_lineitem_row, BATCH_SIZE))
        for table_name in ("customer", "supplier", "part", "partsupp", "orders", "lineitem"):
            after_counts[table_name] = fetch_table_count(cur, table_name)
        return {
            "before_counts": before_counts,
            "after_counts": after_counts,
            "customer_rows": customer_rows,
            "supplier_rows": supplier_rows,
            "part_rows": part_rows,
            "partsupp_rows": partsupp_rows,
            "orders_rows": orders_rows,
            "lineitem_rows": lineitem_rows,
        }

    stats = _run_with_cursor(conn, cursor, do_insert)
    elapsed_seconds = perf_counter() - start_time
    table_stats = {
        "customer": {"before": stats["before_counts"].get("customer", 0), "planned": planned_counts["customer"], "inserted": stats["customer_rows"], "after": stats["after_counts"].get("customer", 0)},
        "supplier": {"before": stats["before_counts"].get("supplier", 0), "planned": planned_counts["supplier"], "inserted": stats["supplier_rows"], "after": stats["after_counts"].get("supplier", 0)},
        "part": {"before": stats["before_counts"].get("part", 0), "planned": planned_counts["part"], "inserted": stats["part_rows"], "after": stats["after_counts"].get("part", 0)},
        "partsupp": {"before": stats["before_counts"].get("partsupp", 0), "planned": planned_counts["partsupp"], "inserted": stats["partsupp_rows"], "after": stats["after_counts"].get("partsupp", 0)},
        "orders": {"before": stats["before_counts"].get("orders", 0), "planned": planned_counts["orders"], "inserted": stats["orders_rows"], "after": stats["after_counts"].get("orders", 0)},
        "lineitem": {"before": stats["before_counts"].get("lineitem", 0), "planned": planned_counts["lineitem"], "inserted": stats["lineitem_rows"], "after": stats["after_counts"].get("lineitem", 0)},
    }
    result = {
        "tables": table_stats,
        "customer_inserted": stats["customer_rows"],
        "supplier_inserted": stats["supplier_rows"],
        "part_inserted": stats["part_rows"],
        "partsupp_inserted": stats["partsupp_rows"],
        "orders_inserted": stats["orders_rows"],
        "lineitem_inserted": stats["lineitem_rows"],
        "total_inserted": stats["customer_rows"] + stats["supplier_rows"] + stats["part_rows"] + stats["partsupp_rows"] + stats["orders_rows"] + stats["lineitem_rows"],
        "elapsed_seconds": elapsed_seconds,
    }
    if emit_summary:
        print("RF1 insert completed")
        for table_name in ("customer", "supplier", "part", "partsupp", "orders", "lineitem"):
            summary = table_stats[table_name]
            print(f"{table_name}: before={summary['before']}, planned={summary['planned']}, inserted={summary['inserted']}, after={summary['after']}")
        print(f"total inserted: {result['total_inserted']}")
        print(f"elapsed seconds: {elapsed_seconds:.4f}")
    return result


def delete_refresh_data(conn=None, cursor=None, emit_summary: bool = True):
    start_time = perf_counter()
    customer_keys = load_unique_key_tuples_from_insert(CUSTOMER_FILE, [0])
    supplier_keys = load_unique_key_tuples_from_insert(SUPPLIER_FILE, [0])
    part_keys = load_unique_key_tuples_from_insert(PART_FILE, [0])
    partsupp_keys = load_unique_key_tuples_from_insert(PARTSUPP_FILE, [0, 1])
    orders_keys = load_unique_key_tuples_from_insert(ORDERS_FILE, [0])
    lineitem_keys = load_unique_key_tuples_from_insert(LINEITEM_FILE, [0, 3])
    planned_counts = {
        "customer": len(customer_keys),
        "supplier": len(supplier_keys),
        "part": len(part_keys),
        "partsupp": len(partsupp_keys),
        "orders": len(orders_keys),
        "lineitem": len(lineitem_keys),
    }

    def do_delete(cur):
        before_counts = {}
        after_counts = {}
        for table_name in ("customer", "supplier", "part", "partsupp", "orders", "lineitem"):
            before_counts[table_name] = fetch_table_count(cur, table_name)
        deleted_lineitem = delete_by_keys(cur, "lineitem", ["l_orderkey", "l_linenumber"], lineitem_keys)
        deleted_orders = delete_by_keys(cur, "orders", ["o_orderkey"], orders_keys)
        deleted_partsupp = delete_by_keys(cur, "partsupp", ["ps_partkey", "ps_suppkey"], partsupp_keys)
        deleted_part = delete_by_keys(cur, "part", ["p_partkey"], part_keys)
        deleted_supplier = delete_by_keys(cur, "supplier", ["s_suppkey"], supplier_keys)
        deleted_customer = delete_by_keys(cur, "customer", ["c_custkey"], customer_keys)
        for table_name in ("customer", "supplier", "part", "partsupp", "orders", "lineitem"):
            after_counts[table_name] = fetch_table_count(cur, table_name)
        return {
            "before_counts": before_counts,
            "after_counts": after_counts,
            "deleted_customer": deleted_customer,
            "deleted_supplier": deleted_supplier,
            "deleted_part": deleted_part,
            "deleted_partsupp": deleted_partsupp,
            "deleted_orders": deleted_orders,
            "deleted_lineitem": deleted_lineitem,
        }

    stats = _run_with_cursor(conn, cursor, do_delete)
    elapsed_seconds = perf_counter() - start_time
    table_stats = {
        "customer": {"before": stats["before_counts"].get("customer", 0), "planned": planned_counts["customer"], "deleted": stats["deleted_customer"], "after": stats["after_counts"].get("customer", 0)},
        "supplier": {"before": stats["before_counts"].get("supplier", 0), "planned": planned_counts["supplier"], "deleted": stats["deleted_supplier"], "after": stats["after_counts"].get("supplier", 0)},
        "part": {"before": stats["before_counts"].get("part", 0), "planned": planned_counts["part"], "deleted": stats["deleted_part"], "after": stats["after_counts"].get("part", 0)},
        "partsupp": {"before": stats["before_counts"].get("partsupp", 0), "planned": planned_counts["partsupp"], "deleted": stats["deleted_partsupp"], "after": stats["after_counts"].get("partsupp", 0)},
        "orders": {"before": stats["before_counts"].get("orders", 0), "planned": planned_counts["orders"], "deleted": stats["deleted_orders"], "after": stats["after_counts"].get("orders", 0)},
        "lineitem": {"before": stats["before_counts"].get("lineitem", 0), "planned": planned_counts["lineitem"], "deleted": stats["deleted_lineitem"], "after": stats["after_counts"].get("lineitem", 0)},
    }
    result = {
        "tables": table_stats,
        "customer_deleted": stats["deleted_customer"],
        "supplier_deleted": stats["deleted_supplier"],
        "part_deleted": stats["deleted_part"],
        "partsupp_deleted": stats["deleted_partsupp"],
        "orders_deleted": stats["deleted_orders"],
        "lineitem_deleted": stats["deleted_lineitem"],
        "total_deleted": stats["deleted_customer"] + stats["deleted_supplier"] + stats["deleted_part"] + stats["deleted_partsupp"] + stats["deleted_orders"] + stats["deleted_lineitem"],
        "elapsed_seconds": elapsed_seconds,
    }
    if emit_summary:
        print("RF2 delete completed")
        for table_name in ("customer", "supplier", "part", "partsupp", "orders", "lineitem"):
            summary = table_stats[table_name]
            print(f"{table_name}: before={summary['before']}, planned={summary['planned']}, deleted={summary['deleted']}, after={summary['after']}")
        print(f"total deleted: {result['total_deleted']}")
        print(f"elapsed seconds: {elapsed_seconds:.4f}")
    return result


def timed_insert(cur, conn):
    start = perf_counter()
    result, _ = run_quietly(insert_refresh_data, conn=conn, cursor=cur, emit_summary=False)
    return perf_counter() - start, result


def timed_delete(cur, conn):
    start = perf_counter()
    result, _ = run_quietly(delete_refresh_data, conn=conn, cursor=cur, emit_summary=False)
    return perf_counter() - start, result


def ensure_base_state(cur, conn):
    result, _ = run_quietly(delete_refresh_data, conn=conn, cursor=cur, emit_summary=False)
    return result


def verify_refreshed_mv(cur, conn, target, verify_name: str):
    drop_mv_if_exists(cur, conn, verify_name)
    verify_create_seconds = create_verify_mv(cur, conn, target, verify_name)
    verify_matches = compare_mvs_match_only(cur, target["mv_name"], verify_name)
    drop_mv_if_exists(cur, conn, verify_name)
    return {
        "verify_mv_name": verify_name,
        "matches": verify_matches,
        "verify_create_seconds": verify_create_seconds,
    }


def run_single_iteration(cur, conn, target, repeat_index: int):
    ensure_base_state(cur, conn)
    conn.commit()
    verify_name = verify_mv_name(target["mv_name"])

    print_experiment_header(target, repeat_index)

    print_stage("Ensure existing MV")
    create_status = create_mv_if_missing(cur, conn, target)
    print_info("create status", create_status)

    print_stage("Insert into base tables")
    insert_seconds, insert_result = timed_insert(cur, conn)
    print_time("insert", insert_seconds)
    print_info("insert result", insert_result)

    print_stage("Refresh existing MV after insert")
    refresh_after_insert_seconds = refresh_mv(cur, conn, target["mv_name"])
    print_time("refresh after insert", refresh_after_insert_seconds)

    print_stage("Verify refreshed MV with rebuilt verify MV")
    verify_after_insert = verify_refreshed_mv(cur, conn, target, verify_name)
    print_time("create verify MV", verify_after_insert["verify_create_seconds"])
    print_info("verify matches", verify_after_insert["matches"])

    print_stage("Delete inserted refresh data from base tables")
    delete_seconds, delete_result = timed_delete(cur, conn)
    print_time("delete", delete_seconds)
    print_info("delete result", delete_result)

    print_stage("Refresh existing MV after delete")
    refresh_after_delete_seconds = refresh_mv(cur, conn, target["mv_name"])
    print_time("refresh after delete", refresh_after_delete_seconds)

    verify_after_delete = {"verify_mv_name": verify_name, "matches": None, "verify_create_seconds": 0.0, "skipped": verify_after_insert["matches"]}
    if verify_after_insert["matches"]:
        print_stage("Skip delete verify because insert verify already passed")
        print_info("delete verify skipped", True)
    else:
        print_stage("Verify refreshed MV after delete with rebuilt verify MV")
        verify_after_delete = verify_refreshed_mv(cur, conn, target, verify_name)
        verify_after_delete["skipped"] = False
        print_time("create verify MV", verify_after_delete["verify_create_seconds"])
        print_info("verify matches", verify_after_delete["matches"])

    print("")
    print(f"[done] {target['mv_name']} repeat {repeat_index}")

    return {
        "repeat": repeat_index,
        "status": "ok",
        "create_status": create_status,
        "steps": {
            "insert_seconds": insert_seconds,
            "refresh_after_insert_seconds": refresh_after_insert_seconds,
            "verify_after_insert_create_seconds": verify_after_insert["verify_create_seconds"],
            "delete_seconds": delete_seconds,
            "refresh_after_delete_seconds": refresh_after_delete_seconds,
            "verify_after_delete_create_seconds": verify_after_delete["verify_create_seconds"],
        },
        "insert_result": insert_result,
        "delete_result": delete_result,
        "verify": {
            "after_insert": verify_after_insert,
            "after_delete": verify_after_delete,
        },
    }


def run_experiment():
    targets = all_mv_targets()
    results = {
        "config": {
            "repeats": REPEATS,
            "db_name": DB_CONFIG["dbname"],
            "target_count": len(targets),
            "mode": "refresh_existing_mv_all",
        },
        "targets": [],
    }

    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    try:
        print(f"Running existing-MV refresh experiment on database: {DB_CONFIG['dbname']}")
        print(f"Targets: {len(targets)}, repeats per target: {REPEATS}")
        cur.execute("SET statement_timeout = 0;")
        conn.commit()

        for target in targets:
            target_result = {
                "combo_name": target["combo_name"],
                "mv_name": target["mv_name"],
                "symbols": list(target["symbols"]),
                "join_edges": [list(edge) for edge in target["join_edges"]],
                "repeats": [],
            }
            results["targets"].append(target_result)

            for repeat_index in range(1, REPEATS + 1):
                try:
                    repeat_result = run_single_iteration(cur, conn, target, repeat_index)
                except Exception as exc:
                    conn.rollback()
                    try:
                        ensure_base_state(cur, conn)
                        conn.commit()
                    except Exception:
                        conn.rollback()
                    repeat_result = {
                        "repeat": repeat_index,
                        "status": "failed",
                        "error_type": type(exc).__name__,
                        "error_message": str(exc),
                    }

                target_result["repeats"].append(repeat_result)
                OUTPUT_JSON.write_text(json.dumps(results, indent=2), encoding="utf-8")
    finally:
        print("")
        cur.close()
        conn.close()

    OUTPUT_JSON.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"Saved experiment results to {OUTPUT_JSON}")


if __name__ == "__main__":
    run_experiment()
