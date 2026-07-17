TEMPLATE_Q5 = """
SELECT
    nr.n_name,
    SUM(l.l_extendedprice * (1 - l.l_discount)) AS revenue
FROM
    lineitem l,
    {source2} ocs,
    {source1} nr
WHERE
    l.l_orderkey = ocs.o_orderkey
    AND l.l_suppkey = ocs.s_suppkey
    AND ocs.s_nationkey = nr.n_nationkey
    AND nr.r_name = '{region}'
    AND ocs.o_orderdate >= DATE '{date}'
    AND ocs.o_orderdate < DATE '{date}' + INTERVAL '1 year'
GROUP BY
    nr.n_name
ORDER BY
    revenue DESC;
"""
