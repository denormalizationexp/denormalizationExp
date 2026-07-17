TEMPLATE_Q8 = """
SELECT
    all_nations.o_year,
    SUM(
        CASE
            WHEN all_nations.nation = '{nation}' THEN all_nations.volume
            ELSE 0
        END
    ) / SUM(all_nations.volume) AS mkt_share
FROM
(
    SELECT
        EXTRACT(YEAR FROM lop.o_orderdate) AS o_year,
        lop.l_extendedprice * (1 - lop.l_discount) AS volume,
        n2.n_name AS nation
    FROM
        {source2} lop,
        {source1} cn1,
        supplier s,
        nation n2,
        region r
    WHERE
        s.s_suppkey = lop.l_suppkey
        AND lop.o_custkey = cn1.c_custkey 
        AND cn1.n_regionkey = r.r_regionkey
        AND r.r_name = '{region}'
        AND s.s_nationkey = n2.n_nationkey
        AND lop.o_orderdate BETWEEN DATE '1995-01-01' AND DATE '1996-12-31'
        AND lop.p_type = '{ptype}'
) AS all_nations
GROUP BY
    all_nations.o_year
ORDER BY
    all_nations.o_year;
"""
