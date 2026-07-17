TEMPLATE_Q5 = """
SELECT
    nr.n_name,
    SUM(los.l_extendedprice * (1 - los.l_discount)) AS revenue
FROM
    customer c,
    {source1} los,
    {source2} nr
WHERE
    c.c_custkey = los.o_custkey
    AND c.c_nationkey = los.s_nationkey
    AND los.s_nationkey = nr.n_nationkey
    AND nr.r_name = '{region}'
    AND los.o_orderdate >= DATE '{date}'
    AND los.o_orderdate < DATE '{date}' + INTERVAL '1 year'
GROUP BY
    nr.n_name
ORDER BY
    revenue DESC;
"""
