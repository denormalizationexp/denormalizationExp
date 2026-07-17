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
        EXTRACT(YEAR FROM loc.l_shipdate) AS l_year,
        loc.l_extendedprice * (1 - loc.l_discount) AS volume
    FROM
        {source1} loc,
        {source2} sn1,
        nation n2
    WHERE
        loc.l_suppkey = sn1.s_suppkey
        AND loc.c_nationkey = n2.n_nationkey
        AND (
            (sn1.n_name = '{nation1}' AND n2.n_name = '{nation2}')
            OR
            (sn1.n_name = '{nation2}' AND n2.n_name = '{nation1}')
        )
        AND loc.l_shipdate BETWEEN DATE '1995-01-01'
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
