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
        (lp.l_extendedprice * (1 - lp.l_discount)
         - ps.ps_supplycost * lp.l_quantity) AS amount
    FROM
        {source1} lp,
        {source2} sn,
        orders o,
        partsupp ps
    WHERE
        sn.s_suppkey = lp.l_suppkey
        AND ps.ps_suppkey = lp.l_suppkey
        AND ps.ps_partkey = lp.l_partkey
        AND o.o_orderkey = lp.l_orderkey
        AND lp.p_name LIKE '%{color}%'
) AS profit
GROUP BY
    profit.nation,
    profit.o_year
ORDER BY
    profit.nation,
    profit.o_year DESC;
"""
