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
        cn2.n_name AS cust_nation,
        EXTRACT(YEAR FROM lo.l_shipdate) AS l_year,
        lo.l_extendedprice * (1 - lo.l_discount) AS volume
    FROM
        supplier s,
        {source2} lo,
        {source1} cn2,
        nation n1
    WHERE
        s.s_suppkey = lo.l_suppkey
        AND cn2.c_custkey = lo.o_custkey
        AND s.s_nationkey = n1.n_nationkey
        AND (
            (n1.n_name = '{nation1}' AND cn2.n_name = '{nation2}')
            OR
            (n1.n_name = '{nation2}' AND cn2.n_name = '{nation1}')
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
