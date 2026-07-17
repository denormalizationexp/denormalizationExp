-- =========================================
-- PostgreSQL TPC-H Schema (with Foreign Keys)
-- =========================================

-- -----------------------------------------
-- Drop tables (PostgreSQL way)
-- -----------------------------------------
DROP TABLE IF EXISTS lineitem  CASCADE;
DROP TABLE IF EXISTS orders    CASCADE;
DROP TABLE IF EXISTS customer  CASCADE;
DROP TABLE IF EXISTS partsupp  CASCADE;
DROP TABLE IF EXISTS supplier  CASCADE;
DROP TABLE IF EXISTS part      CASCADE;
DROP TABLE IF EXISTS nation    CASCADE;
DROP TABLE IF EXISTS region    CASCADE;

-- -----------------------------------------
-- Create REGION
-- -----------------------------------------
CREATE TABLE region (
    r_regionkey  INTEGER PRIMARY KEY,
    r_name       CHAR(25) NOT NULL,
    r_comment    VARCHAR(152),
    _dummy       TEXT
);

-- -----------------------------------------
-- Create NATION
-- -----------------------------------------
CREATE TABLE nation (
    n_nationkey  INTEGER PRIMARY KEY,
    n_name       CHAR(25) NOT NULL,
    n_regionkey  INTEGER NOT NULL,
    n_comment    VARCHAR(152),
    _dummy       TEXT
);

-- -----------------------------------------
-- Create PART
-- -----------------------------------------
CREATE TABLE part (
    p_partkey     INTEGER PRIMARY KEY,
    p_name        VARCHAR(55) NOT NULL,
    p_mfgr        CHAR(25) NOT NULL,
    p_brand       CHAR(10) NOT NULL,
    p_type        VARCHAR(25) NOT NULL,
    p_size        INTEGER NOT NULL,
    p_container   CHAR(10) NOT NULL,
    p_retailprice NUMERIC(15,2) NOT NULL,
    p_comment     VARCHAR(23) NOT NULL,
    _dummy        TEXT
);

-- -----------------------------------------
-- Create SUPPLIER
-- -----------------------------------------
CREATE TABLE supplier (
    s_suppkey     INTEGER PRIMARY KEY,
    s_name        CHAR(25) NOT NULL,
    s_address     VARCHAR(40) NOT NULL,
    s_nationkey   INTEGER NOT NULL,
    s_phone       CHAR(15) NOT NULL,
    s_acctbal     NUMERIC(15,2) NOT NULL,
    s_comment     VARCHAR(101) NOT NULL,
    _dummy        TEXT
);

-- -----------------------------------------
-- Create PARTSUPP
-- -----------------------------------------
CREATE TABLE partsupp (
    ps_partkey     INTEGER NOT NULL,
    ps_suppkey     INTEGER NOT NULL,
    ps_availqty    INTEGER NOT NULL,
    ps_supplycost  NUMERIC(15,2) NOT NULL,
    ps_comment     VARCHAR(199) NOT NULL,
    _dummy         TEXT,
    PRIMARY KEY (ps_partkey, ps_suppkey)
);

-- -----------------------------------------
-- Create CUSTOMER
-- -----------------------------------------
CREATE TABLE customer (
    c_custkey     INTEGER PRIMARY KEY,
    c_name        VARCHAR(25) NOT NULL,
    c_address     VARCHAR(40) NOT NULL,
    c_nationkey   INTEGER NOT NULL,
    c_phone       CHAR(15) NOT NULL,
    c_acctbal     NUMERIC(15,2) NOT NULL,
    c_mktsegment  CHAR(10) NOT NULL,
    c_comment     VARCHAR(117) NOT NULL,
    _dummy        TEXT
);

-- -----------------------------------------
-- Create ORDERS
-- -----------------------------------------
CREATE TABLE orders (
    o_orderkey       INTEGER PRIMARY KEY,
    o_custkey        INTEGER NOT NULL,
    o_orderstatus    CHAR(1) NOT NULL,
    o_totalprice     NUMERIC(15,2) NOT NULL,
    o_orderdate      DATE NOT NULL,
    o_orderpriority  CHAR(15) NOT NULL,
    o_clerk          CHAR(15) NOT NULL,
    o_shippriority   INTEGER NOT NULL,
    o_comment        VARCHAR(79) NOT NULL,
    _dummy           TEXT
);

-- -----------------------------------------
-- Create LINEITEM
-- -----------------------------------------
CREATE TABLE lineitem (
    l_orderkey       INTEGER NOT NULL,
    l_partkey        INTEGER NOT NULL,
    l_suppkey        INTEGER NOT NULL,
    l_linenumber     INTEGER NOT NULL,
    l_quantity       NUMERIC(15,2) NOT NULL,
    l_extendedprice  NUMERIC(15,2) NOT NULL,
    l_discount       NUMERIC(15,2) NOT NULL,
    l_tax            NUMERIC(15,2) NOT NULL,
    l_returnflag     CHAR(1) NOT NULL,
    l_linestatus     CHAR(1) NOT NULL,
    l_shipdate       DATE NOT NULL,
    l_commitdate     DATE NOT NULL,
    l_receiptdate    DATE NOT NULL,
    l_shipinstruct   CHAR(25) NOT NULL,
    l_shipmode       CHAR(10) NOT NULL,
    l_comment        VARCHAR(44) NOT NULL,
    _dummy           TEXT,
    PRIMARY KEY (l_orderkey, l_linenumber)
);

-- -----------------------------------------
-- Foreign keys and supporting indexes
-- -----------------------------------------
ALTER TABLE nation
ADD CONSTRAINT nation_region_fk
FOREIGN KEY (n_regionkey)
REFERENCES region (r_regionkey);

CREATE INDEX idx_nation_region_fk
ON nation (n_regionkey);

ALTER TABLE supplier
ADD CONSTRAINT supplier_nation_fk
FOREIGN KEY (s_nationkey)
REFERENCES nation (n_nationkey);

CREATE INDEX idx_supplier_nation_fk
ON supplier (s_nationkey);

ALTER TABLE customer
ADD CONSTRAINT customer_nation_fk
FOREIGN KEY (c_nationkey)
REFERENCES nation (n_nationkey);

CREATE INDEX idx_customer_nation_fk
ON customer (c_nationkey);

ALTER TABLE orders
ADD CONSTRAINT orders_customer_fk
FOREIGN KEY (o_custkey)
REFERENCES customer (c_custkey);

CREATE INDEX idx_orders_customer_fk
ON orders (o_custkey);

ALTER TABLE partsupp
ADD CONSTRAINT partsupp_part_fk
FOREIGN KEY (ps_partkey)
REFERENCES part (p_partkey);

CREATE INDEX idx_partsupp_part_fk
ON partsupp (ps_partkey);

ALTER TABLE partsupp
ADD CONSTRAINT partsupp_supplier_fk
FOREIGN KEY (ps_suppkey)
REFERENCES supplier (s_suppkey);

CREATE INDEX idx_partsupp_supplier_fk
ON partsupp (ps_suppkey);

ALTER TABLE lineitem
ADD CONSTRAINT lineitem_order_fk
FOREIGN KEY (l_orderkey)
REFERENCES orders (o_orderkey);

CREATE INDEX idx_lineitem_order_fk
ON lineitem (l_orderkey);

ALTER TABLE lineitem
ADD CONSTRAINT lineitem_partsupp_fk
FOREIGN KEY (l_partkey, l_suppkey)
REFERENCES partsupp (ps_partkey, ps_suppkey);

CREATE INDEX idx_lineitem_partsupp_fk
ON lineitem (l_partkey, l_suppkey);
