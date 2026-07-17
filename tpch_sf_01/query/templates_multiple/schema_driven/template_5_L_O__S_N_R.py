TEMPLATE_Q5 = """
SELECT
    snr.n_name,
    SUM(lo.l_extendedprice * (1 - lo.l_discount)) AS revenue
FROM
    customer c,
    {source1} lo,
    {source2} snr
WHERE
    c.c_custkey = lo.o_custkey
    AND lo.l_suppkey = snr.s_suppkey
    AND c.c_nationkey = snr.s_nationkey
    AND snr.r_name = '{region}'
    AND lo.o_orderdate >= DATE '{date}'
    AND lo.o_orderdate < DATE '{date}' + INTERVAL '1 year'
GROUP BY
    snr.n_name
ORDER BY
    revenue DESC;
"""
