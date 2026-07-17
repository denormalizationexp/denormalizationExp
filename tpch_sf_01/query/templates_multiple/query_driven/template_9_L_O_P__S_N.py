TEMPLATE_Q9 = """
SELECT
    profit.nation,
    profit.o_year,
    SUM(profit.amount) AS sum_profit
FROM
(
    SELECT
        sn.n_name AS nation,
        EXTRACT(YEAR FROM lop.o_orderdate) AS o_year,
        (lop.l_extendedprice * (1 - lop.l_discount)
         - ps.ps_supplycost * lop.l_quantity) AS amount
    FROM
        {source1} lop,
        {source2} sn,
        partsupp ps
    WHERE
        sn.s_suppkey = lop.l_suppkey
        AND ps.ps_suppkey = lop.l_suppkey
        AND ps.ps_partkey = lop.l_partkey
        AND lop.p_name LIKE '%{color}%'
) AS profit
GROUP BY
    profit.nation,
    profit.o_year
ORDER BY
    profit.nation,
    profit.o_year DESC;
"""
