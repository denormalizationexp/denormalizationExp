TEMPLATE_Q5 = """
SELECT
    n.n_name,
    SUM(ls.l_extendedprice * (1 - ls.l_discount)) AS revenue
FROM
    {source1} ls,
    {source2} oc,
    nation n,
    region r
WHERE
    ls.l_orderkey = oc.o_orderkey
    AND oc.c_nationkey = ls.s_nationkey
    AND ls.s_nationkey = n.n_nationkey
    AND n.n_regionkey = r.r_regionkey
    AND r.r_name = '{region}'
    AND oc.o_orderdate >= DATE '{date}'
    AND oc.o_orderdate < DATE '{date}' + INTERVAL '1 year'
GROUP BY
    n.n_name
ORDER BY
    revenue DESC;
"""
