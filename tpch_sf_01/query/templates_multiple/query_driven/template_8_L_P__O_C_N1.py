TEMPLATE_Q8 = """
SELECT
    all_nations.o_year,
    SUM(CASE WHEN all_nations.nation = '{nation}' THEN all_nations.volume ELSE 0 END)
    / SUM(all_nations.volume) AS mkt_share
FROM
(
    SELECT
        EXTRACT(YEAR FROM ocn1.o_orderdate) AS o_year,
        lp.l_extendedprice * (1 - lp.l_discount) AS volume,
        n2.n_name AS nation
    FROM
        {source1} lp,
        {source2} ocn1,
        supplier s,
        nation n2,
        region r
    WHERE
        s.s_suppkey = lp.l_suppkey
        AND lp.l_orderkey = ocn1.o_orderkey
        AND ocn1.n_regionkey = r.r_regionkey
        AND r.r_name = '{region}'
        AND s.s_nationkey = n2.n_nationkey
        AND ocn1.o_orderdate BETWEEN DATE '1995-01-01' AND DATE '1996-12-31'
        AND lp.p_type = '{ptype}'
) AS all_nations
GROUP BY all_nations.o_year
ORDER BY all_nations.o_year;
"""
