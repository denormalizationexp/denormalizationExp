TEMPLATE_Q5 = """
SELECT
    sn.n_name,
    SUM(loc.l_extendedprice * (1 - loc.l_discount)) AS revenue
FROM
    {source1} loc,
    {source2} sn,
    region r
WHERE
    loc.l_suppkey = sn.s_suppkey
    AND loc.c_nationkey = sn.s_nationkey
    AND sn.n_regionkey = r.r_regionkey
    AND r.r_name = '{region}'
    AND loc.o_orderdate >= DATE '{date}'
    AND loc.o_orderdate < DATE '{date}' + INTERVAL '1 year'
GROUP BY
    sn.n_name
ORDER BY
    revenue DESC;
"""
