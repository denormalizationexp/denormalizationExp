TEMPLATE_Q5 = """
SELECT
    csnr.n_name,
    SUM(lo.l_extendedprice * (1 - lo.l_discount)) AS revenue
FROM
    {source1} csnr,
    {source2} lo
WHERE
    csnr.c_custkey = lo.o_custkey
    AND lo.l_suppkey = csnr.s_suppkey
    AND csnr.r_name = '{region}'
    AND lo.o_orderdate >= DATE '{date}'
    AND lo.o_orderdate < DATE '{date}' + INTERVAL '1 year'
GROUP BY
    csnr.n_name
ORDER BY
    revenue DESC;
"""
