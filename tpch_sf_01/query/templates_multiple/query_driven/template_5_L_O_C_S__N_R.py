TEMPLATE_Q5 = """
SELECT
    nr.n_name,
    SUM(locs.l_extendedprice * (1 - locs.l_discount)) AS revenue
FROM
    {source1} locs,
    {source2} nr
WHERE
    locs.s_nationkey = nr.n_nationkey
    AND nr.r_name = '{region}'
    AND locs.o_orderdate >= DATE '{date}'
    AND locs.o_orderdate < DATE '{date}' + INTERVAL '1 year'
GROUP BY
    nr.n_name
ORDER BY
    revenue DESC;
"""
