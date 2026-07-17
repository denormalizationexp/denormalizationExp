TEMPLATE_Q5 = """
SELECT
    nr.n_name,
    SUM(l.l_extendedprice * (1 - l.l_discount)) AS revenue
FROM
    {source1} cs,
    orders o,
    lineitem l,
    {source2} nr
WHERE
    cs.c_custkey = o.o_custkey
    AND l.l_orderkey = o.o_orderkey
    AND l.l_suppkey = cs.s_suppkey
    AND cs.s_nationkey = nr.n_nationkey
    AND nr.r_name = '{region}'
    AND o.o_orderdate >= DATE '{date}'
    AND o.o_orderdate < DATE '{date}' + INTERVAL '1 year'
GROUP BY
    nr.n_name
ORDER BY
    revenue DESC;
"""
