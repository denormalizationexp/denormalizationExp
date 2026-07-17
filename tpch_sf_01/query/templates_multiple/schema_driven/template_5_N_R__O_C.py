TEMPLATE_Q5 = """
SELECT
    nr.n_name,
    SUM(l.l_extendedprice * (1 - l.l_discount)) AS revenue
FROM
    {source2} oc,
    lineitem l,
    supplier s,
    {source1} nr
WHERE
    l.l_orderkey = oc.o_orderkey
    AND l.l_suppkey = s.s_suppkey
    AND oc.c_nationkey = s.s_nationkey
    AND s.s_nationkey = nr.n_nationkey
    AND nr.r_name = '{region}'
    AND oc.o_orderdate >= DATE '{date}'
    AND oc.o_orderdate < DATE '{date}' + INTERVAL '1 year'
GROUP BY
    nr.n_name
ORDER BY
    revenue DESC;
"""
