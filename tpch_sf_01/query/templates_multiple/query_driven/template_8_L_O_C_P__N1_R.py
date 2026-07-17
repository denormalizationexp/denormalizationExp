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
        EXTRACT(YEAR FROM locp.o_orderdate) AS o_year,
        locp.l_extendedprice * (1 - locp.l_discount) AS volume,
        n2.n_name AS nation
    FROM
        {source1} locp,
        supplier s,
        {source2} n1r,
        nation n2
    WHERE
        s.s_suppkey = locp.l_suppkey
        AND locp.c_nationkey = n1r.n_nationkey
        AND n1r.r_name = '{region}'
        AND s.s_nationkey = n2.n_nationkey
        AND locp.o_orderdate BETWEEN DATE '1995-01-01' AND DATE '1996-12-31'
        AND locp.p_type = '{ptype}'
) AS all_nations
GROUP BY
    all_nations.o_year
ORDER BY
    all_nations.o_year;
"""
