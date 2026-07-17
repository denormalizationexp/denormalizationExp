TEMPLATE_Q5 = """
SELECT
    lsnr.n_name,
    SUM(lsnr.l_extendedprice * (1 - lsnr.l_discount)) AS revenue
FROM
    {source1} lsnr,
    {source2} oc
WHERE
    lsnr.l_orderkey = oc.o_orderkey
    AND oc.c_nationkey = lsnr.s_nationkey
    AND lsnr.r_name = '{region}'
    AND oc.o_orderdate >= DATE '{date}'
    AND oc.o_orderdate < DATE '{date}' + INTERVAL '1 year'
GROUP BY
    lsnr.n_name
ORDER BY
    revenue DESC;
"""
