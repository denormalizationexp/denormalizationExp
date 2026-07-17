TEMPLATE_Q10 = """
SELECT
    cn.c_custkey,
    cn.c_name,
    SUM(lo.l_extendedprice * (1 - lo.l_discount)) AS revenue,
    cn.c_acctbal,
    cn.n_name,
    cn.c_address,
    cn.c_phone,
    cn.c_comment
FROM
    {source1} cn,
    {source2} lo
WHERE
    cn.c_custkey = lo.o_custkey
    AND lo.o_orderdate >= DATE '{date}'
    AND lo.o_orderdate < DATE '{date}' + INTERVAL '3 month'
    AND lo.l_returnflag = 'R'
GROUP BY
    cn.c_custkey,
    cn.c_name,
    cn.c_acctbal,
    cn.c_phone,
    cn.n_name,
    cn.c_address,
    cn.c_comment
ORDER BY
    revenue DESC
LIMIT 20;
"""
