TEMPLATE_Q7 = """
SELECT
    shipping.supp_nation,
    shipping.cust_nation,
    shipping.l_year,
    SUM(shipping.volume) AS revenue
FROM
(
    SELECT
        sn1.n_name AS supp_nation,
        n2.n_name AS cust_nation,
        EXTRACT(YEAR FROM lo.l_shipdate) AS l_year,
        lo.l_extendedprice * (1 - lo.l_discount) AS volume
    FROM
        {source1} lo,
        {source2} sn1,
        customer c,
        nation n2
    WHERE
        lo.l_suppkey = sn1.s_suppkey
        AND c.c_custkey = lo.o_custkey
        AND c.c_nationkey = n2.n_nationkey
        AND (
            (sn1.n_name = '{nation1}' AND n2.n_name = '{nation2}')
            OR
            (sn1.n_name = '{nation2}' AND n2.n_name = '{nation1}')
        )
        AND lo.l_shipdate BETWEEN DATE '1995-01-01'
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
