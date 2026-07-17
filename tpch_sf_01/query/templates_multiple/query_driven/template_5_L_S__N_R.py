TEMPLATE_Q5 = """
SELECT
    nr.n_name,
    SUM(ls.l_extendedprice * (1 - ls.l_discount)) AS revenue
FROM
    customer c,
    orders o,
    {source1} ls,
    {source2} nr
WHERE
    c.c_custkey = o.o_custkey
    AND ls.l_orderkey = o.o_orderkey
    AND c.c_nationkey = ls.s_nationkey
    AND ls.s_nationkey = nr.n_nationkey
    AND nr.r_name = '{region}'
    AND o.o_orderdate >= DATE '{date}'
    AND o.o_orderdate < DATE '{date}' + INTERVAL '1 year'
GROUP BY
    nr.n_name
ORDER BY
    revenue DESC;
"""
