TEMPLATE_Q5 = """
SELECT
    sn.n_name,
    SUM(l.l_extendedprice * (1 - l.l_discount)) AS revenue
FROM
    {source1} oc,
    lineitem l,
    {source2} sn,
    region r
WHERE
    l.l_orderkey = oc.o_orderkey
    AND l.l_suppkey = sn.s_suppkey
    AND oc.c_nationkey = sn.s_nationkey
    AND sn.n_regionkey = r.r_regionkey
    AND r.r_name = '{region}'
    AND oc.o_orderdate >= DATE '{date}'
    AND oc.o_orderdate < DATE '{date}' + INTERVAL '1 year'
GROUP BY
    sn.n_name
ORDER BY
    revenue DESC;
"""
