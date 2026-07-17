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
        EXTRACT(YEAR FROM los.l_shipdate) AS l_year,
        los.l_extendedprice * (1 - los.l_discount) AS volume
    FROM
        {source2} los,
        {source1} cn2,
        nation n1
    WHERE
        cn2.c_custkey = los.o_custkey
        AND los.s_nationkey = n1.n_nationkey
        AND (
            (n1.n_name = '{nation1}' AND cn2.n_name = '{nation2}')
            OR
            (n1.n_name = '{nation2}' AND cn2.n_name = '{nation1}')
        )
        AND los.l_shipdate BETWEEN DATE '1995-01-01'
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
