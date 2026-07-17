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
        EXTRACT(YEAR FROM locsp.o_orderdate) AS o_year,
        locsp.l_extendedprice * (1 - locsp.l_discount) AS volume,
        n2.n_name AS nation
    FROM
        {source1} locsp,
        {source2} n1r,
        nation n2
    WHERE
        locsp.c_nationkey = n1r.n_nationkey
        AND n1r.r_name = '{region}'
        AND locsp.s_nationkey = n2.n_nationkey
        AND locsp.o_orderdate BETWEEN DATE '1995-01-01' AND DATE '1996-12-31'
        AND locsp.p_type = '{ptype}'
) AS all_nations
GROUP BY
    all_nations.o_year
ORDER BY
    all_nations.o_year;
"""
