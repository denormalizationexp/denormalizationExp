TEMPLATE_Q5 = """
SELECT
    snr.n_name,
    SUM(l.l_extendedprice * (1 - l.l_discount)) AS revenue
FROM
    {source1} oc,
    lineitem l,
    {source2} snr
WHERE
    l.l_orderkey = oc.o_orderkey
    AND l.l_suppkey = snr.s_suppkey
    AND oc.c_nationkey = snr.s_nationkey
    AND snr.r_name = '{region}'
    AND oc.o_orderdate >= DATE '{date}'
    AND oc.o_orderdate < DATE '{date}' + INTERVAL '1 year'
GROUP BY
    snr.n_name
ORDER BY
    revenue DESC;
"""
