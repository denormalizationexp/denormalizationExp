TEMPLATE_Q5 = """
SELECT
    nr.n_name,
    SUM(lo.l_extendedprice * (1 - lo.l_discount)) AS revenue
FROM
    {source1} cs,
    {source2} lo,
    {source3} nr
WHERE
    cs.c_custkey = lo.o_custkey
    AND lo.l_suppkey = cs.s_suppkey
    AND cs.s_nationkey = nr.n_nationkey
    AND nr.r_name = '{region}'
    AND lo.o_orderdate >= DATE '{date}'
    AND lo.o_orderdate < DATE '{date}' + INTERVAL '1 year'
GROUP BY
    nr.n_name
ORDER BY
    revenue DESC;
"""
