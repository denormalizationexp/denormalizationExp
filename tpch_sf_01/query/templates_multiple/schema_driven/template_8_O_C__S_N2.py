TEMPLATE_Q8 = """
SELECT
    all_nations.o_year,
    SUM(CASE WHEN all_nations.nation = '{nation}' THEN all_nations.volume ELSE 0 END)
    / SUM(all_nations.volume) AS mkt_share
FROM
(
    SELECT
        EXTRACT(YEAR FROM oc.o_orderdate) AS o_year,
        l.l_extendedprice * (1 - l.l_discount) AS volume,
        sn2.n_name AS nation
    FROM
        {source1} oc,
        {source2} sn2,
        lineitem l,
        nation n1,
        part p,
        region r
    WHERE
        p.p_partkey = l.l_partkey
        AND sn2.s_suppkey = l.l_suppkey
        AND oc.o_orderkey = l.l_orderkey
        AND oc.c_nationkey = n1.n_nationkey
        AND n1.n_regionkey = r.r_regionkey
        AND r.r_name = '{region}'
        AND oc.o_orderdate BETWEEN DATE '1995-01-01' AND DATE '1996-12-31'
        AND p.p_type = '{ptype}'
) AS all_nations
GROUP BY all_nations.o_year
ORDER BY all_nations.o_year;
"""
