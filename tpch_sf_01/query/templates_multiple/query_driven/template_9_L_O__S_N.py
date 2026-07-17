TEMPLATE_Q9 = """
SELECT
    profit.nation,
    profit.o_year,
    SUM(profit.amount) AS sum_profit
FROM
(
    SELECT
        sn.n_name AS nation,
        EXTRACT(YEAR FROM lo.o_orderdate) AS o_year,
        (lo.l_extendedprice * (1 - lo.l_discount)
         - ps.ps_supplycost * lo.l_quantity) AS amount
    FROM
        {source1} lo,
        {source2} sn,
        partsupp ps,
        part p
    WHERE
        sn.s_suppkey = lo.l_suppkey
        AND ps.ps_suppkey = lo.l_suppkey
        AND ps.ps_partkey = lo.l_partkey
        AND p.p_partkey = lo.l_partkey
        AND p.p_name LIKE '%{color}%'
) AS profit
GROUP BY
    profit.nation,
    profit.o_year
ORDER BY
    profit.nation,
    profit.o_year DESC;
"""
