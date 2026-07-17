TEMPLATE_Q5 = """
SELECT
    csn.n_name,
    SUM(lo.l_extendedprice * (1 - lo.l_discount)) AS revenue
FROM
    {source1} csn,
    {source2} lo,
    region r
WHERE
    csn.c_custkey = lo.o_custkey
    AND lo.l_suppkey = csn.s_suppkey
    AND csn.n_regionkey = r.r_regionkey
    AND r.r_name = '{region}'
    AND lo.o_orderdate >= DATE '{date}'
    AND lo.o_orderdate < DATE '{date}' + INTERVAL '1 year'
GROUP BY
    csn.n_name
ORDER BY
    revenue DESC;
"""
