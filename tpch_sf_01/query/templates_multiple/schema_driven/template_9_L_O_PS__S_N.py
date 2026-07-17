TEMPLATE_Q9 = """
SELECT
    profit.nation,
    profit.o_year,
    SUM(profit.amount) AS sum_profit
FROM
(
    SELECT
        sn.n_name AS nation,
        EXTRACT(YEAR FROM lops.o_orderdate) AS o_year,
        (lops.l_extendedprice * (1 - lops.l_discount)
         - lops.ps_supplycost * lops.l_quantity) AS amount
    FROM
        {source1} lops,
        {source2} sn,
        part p
    WHERE
        sn.s_suppkey = lops.l_suppkey
        AND p.p_partkey = lops.l_partkey
        AND p.p_name LIKE '%{color}%'
) AS profit
GROUP BY
    profit.nation,
    profit.o_year
ORDER BY
    profit.nation,
    profit.o_year DESC;
"""
