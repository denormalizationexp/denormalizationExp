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
        EXTRACT(YEAR FROM losp.o_orderdate) AS o_year,
        losp.l_extendedprice * (1 - losp.l_discount) AS volume,
        n2.n_name AS nation
    FROM
        {source1} losp,
        customer c,
        {source2} n1r,
        nation n2
    WHERE
        losp.o_custkey = c.c_custkey
        AND c.c_nationkey = n1r.n_nationkey
        AND n1r.r_name = '{region}'
        AND losp.s_nationkey = n2.n_nationkey
        AND losp.o_orderdate BETWEEN DATE '1995-01-01' AND DATE '1996-12-31'
        AND losp.p_type = '{ptype}'
) AS all_nations
GROUP BY
    all_nations.o_year
ORDER BY
    all_nations.o_year;
"""
