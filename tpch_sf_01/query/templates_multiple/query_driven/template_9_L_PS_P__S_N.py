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
        (lpsp.l_extendedprice * (1 - lpsp.l_discount)
         - lpsp.ps_supplycost * lpsp.l_quantity) AS amount
    FROM
        {source1} lpsp,
        {source2} sn,
        orders o
    WHERE
        sn.s_suppkey = lpsp.l_suppkey
        AND o.o_orderkey = lpsp.l_orderkey
        AND lpsp.p_name LIKE '%{color}%'
) AS profit
GROUP BY
    profit.nation,
    profit.o_year
ORDER BY
    profit.nation,
    profit.o_year DESC;
"""
