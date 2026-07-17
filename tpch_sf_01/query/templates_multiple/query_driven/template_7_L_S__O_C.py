TEMPLATE_Q7 = """
SELECT
    shipping.supp_nation,
    shipping.cust_nation,
    shipping.l_year,
    SUM(shipping.volume) AS revenue
FROM
(
    SELECT
        n1.n_name AS supp_nation,
        n2.n_name AS cust_nation,
        EXTRACT(YEAR FROM ls.l_shipdate) AS l_year,
        ls.l_extendedprice * (1 - ls.l_discount) AS volume
    FROM
        {source1} ls,
        {source2} oc,
        nation n1,
        nation n2
    WHERE
        ls.l_orderkey = oc.o_orderkey
        AND ls.s_nationkey = n1.n_nationkey
        AND oc.c_nationkey = n2.n_nationkey
        AND (
            (n1.n_name = '{nation1}' AND n2.n_name = '{nation2}')
            OR
            (n1.n_name = '{nation2}' AND n2.n_name = '{nation1}')
        )
        AND ls.l_shipdate BETWEEN DATE '1995-01-01'
                             AND DATE '1996-12-31'
) AS shipping
GROUP BY
    shipping.supp_nation,
    shipping.cust_nation,
    shipping.l_year
ORDER BY
    shipping.supp_nation,
    shipping.cust_nation,
    shipping.l_year;
"""
