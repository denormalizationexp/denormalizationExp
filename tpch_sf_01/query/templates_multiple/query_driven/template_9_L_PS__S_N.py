TEMPLATE_Q9 = """
SELECT
    profit.nation,
    profit.o_year,
    SUM(profit.amount) AS sum_profit
FROM
(
    SELECT
        sn.n_name AS nation,
        EXTRACT(YEAR FROM o.o_orderdate) AS o_year,
        (lps.l_extendedprice * (1 - lps.l_discount)
         - lps.ps_supplycost * lps.l_quantity) AS amount
    FROM
        {source1} lps,
        {source2} sn,
        orders o,
        part p
    WHERE
        sn.s_suppkey = lps.l_suppkey
        AND p.p_partkey = lps.l_partkey
        AND o.o_orderkey = lps.l_orderkey
        AND p.p_name LIKE '%{color}%'
) AS profit
GROUP BY
    profit.nation,
    profit.o_year
ORDER BY
    profit.nation,
    profit.o_year DESC;
"""
