TEMPLATE_Q5 = """
SELECT
    sn.n_name,
    SUM(lo.l_extendedprice * (1 - lo.l_discount)) AS revenue
FROM
    customer c,
    {source1} lo,
    {source2} sn,
    region r
WHERE
    c.c_custkey = lo.o_custkey
    AND lo.l_suppkey = sn.s_suppkey
    AND c.c_nationkey = sn.s_nationkey
    AND sn.n_regionkey = r.r_regionkey
    AND r.r_name = '{region}'
    AND lo.o_orderdate >= DATE '{date}'
    AND lo.o_orderdate < DATE '{date}' + INTERVAL '1 year'
GROUP BY
    sn.n_name
ORDER BY
    revenue DESC;
"""
