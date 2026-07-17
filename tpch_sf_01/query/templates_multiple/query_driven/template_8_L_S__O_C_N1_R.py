TEMPLATE_Q8 = """
SELECT
    all_nations.o_year,
    SUM(CASE WHEN all_nations.nation = '{nation}' THEN all_nations.volume ELSE 0 END)
    / SUM(all_nations.volume) AS mkt_share
FROM
(
    SELECT
        EXTRACT(YEAR FROM ocn1r.o_orderdate) AS o_year,
        ls.l_extendedprice * (1 - ls.l_discount) AS volume,
        n2.n_name AS nation
    FROM
        {source1} ls,
        {source2} ocn1r,
        nation n2,
        part p
    WHERE
        p.p_partkey = ls.l_partkey
        AND ls.l_orderkey = ocn1r.o_orderkey
        AND ocn1r.r_name = '{region}'
        AND ls.s_nationkey = n2.n_nationkey
        AND ocn1r.o_orderdate BETWEEN DATE '1995-01-01' AND DATE '1996-12-31'
        AND p.p_type = '{ptype}'
) AS all_nations
GROUP BY all_nations.o_year
ORDER BY all_nations.o_year;
"""
