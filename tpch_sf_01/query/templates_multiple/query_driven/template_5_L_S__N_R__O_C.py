TEMPLATE_Q5 = """
SELECT
    nr.n_name,
    SUM(ls.l_extendedprice * (1 - ls.l_discount)) AS revenue
FROM
    {source1} ls,
    {source2} nr,
    {source3} oc
WHERE
    ls.l_orderkey = oc.o_orderkey
    AND oc.c_nationkey = ls.s_nationkey
    AND ls.s_nationkey = nr.n_nationkey
    AND nr.r_name = '{region}'
    AND oc.o_orderdate >= DATE '{date}'
    AND oc.o_orderdate < DATE '{date}' + INTERVAL '1 year'
GROUP BY
    nr.n_name
ORDER BY
    revenue DESC;
"""
