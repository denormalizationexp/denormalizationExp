TEMPLATE_Q5 = """
SELECT
    nr.n_name,
    SUM(lo.l_extendedprice * (1 - lo.l_discount)) AS revenue
FROM
    customer c,
    {source1} lo,
    supplier s,
    {source2} nr
WHERE
    c.c_custkey = lo.o_custkey
    AND lo.l_suppkey = s.s_suppkey
    AND c.c_nationkey = s.s_nationkey
    AND s.s_nationkey = nr.n_nationkey
    AND nr.r_name = '{region}'
    AND lo.o_orderdate >= DATE '{date}'
    AND lo.o_orderdate < DATE '{date}' + INTERVAL '1 year'
GROUP BY
    nr.n_name
ORDER BY
    revenue DESC;
"""
