TEMPLATE_Q5 = """
SELECT
    n.n_name,
    SUM(lo.l_extendedprice * (1 - lo.l_discount)) AS revenue
FROM
    {source1} cs,
    {source2} lo,
    nation n,
    region r
WHERE
    cs.c_custkey = lo.o_custkey
    AND lo.l_suppkey = cs.s_suppkey
    AND cs.s_nationkey = n.n_nationkey
    AND n.n_regionkey = r.r_regionkey
    AND r.r_name = '{region}'
    AND lo.o_orderdate >= DATE '{date}'
    AND lo.o_orderdate < DATE '{date}' + INTERVAL '1 year'
GROUP BY
    n.n_name
ORDER BY
    revenue DESC;
"""
