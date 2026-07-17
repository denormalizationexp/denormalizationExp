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
        EXTRACT(YEAR FROM o.o_orderdate) AS o_year,
        lsp.l_extendedprice * (1 - lsp.l_discount) AS volume,
        n2.n_name AS nation
    FROM
        {source2} lsp,
        {source1} cn1,
        orders o,
        nation n2,
        region r
    WHERE
        lsp.l_orderkey = o.o_orderkey
        AND o.o_custkey = cn1.c_custkey
        AND cn1.n_regionkey = r.r_regionkey       
        AND r.r_name = '{region}'
        AND lsp.s_nationkey = n2.n_nationkey
        AND o.o_orderdate BETWEEN DATE '1995-01-01' AND DATE '1996-12-31'
        AND lsp.p_type = '{ptype}'
) AS all_nations
GROUP BY
    all_nations.o_year
ORDER BY
    all_nations.o_year;
"""
