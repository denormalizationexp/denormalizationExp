TEMPLATE_Q5 = """
SELECT
    snr.n_name,
    SUM(loc.l_extendedprice * (1 - loc.l_discount)) AS revenue
FROM
    {source1} loc,
    {source2} snr
WHERE
    loc.l_suppkey = snr.s_suppkey
    AND loc.c_nationkey = snr.s_nationkey
    AND snr.r_name = '{region}'
    AND loc.o_orderdate >= DATE '{date}'
    AND loc.o_orderdate < DATE '{date}' + INTERVAL '1 year'
GROUP BY
    snr.n_name
ORDER BY
    revenue DESC;
"""
