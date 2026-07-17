TEMPLATE_Q7 = """
SELECT
    shipping.supp_nation,
    shipping.cust_nation,
    shipping.l_year,
    SUM(shipping.volume) AS revenue
FROM
(
    SELECT
        lsn1.n_name AS supp_nation,
        n2.n_name AS cust_nation,
        EXTRACT(YEAR FROM lsn1.l_shipdate) AS l_year,
        lsn1.l_extendedprice * (1 - lsn1.l_discount) AS volume
    FROM
        {source1} lsn1,
        {source2} oc,
        nation n2
    WHERE
        lsn1.l_orderkey = oc.o_orderkey
        AND oc.c_nationkey = n2.n_nationkey
        AND (
            (lsn1.n_name = '{nation1}' AND n2.n_name = '{nation2}')
            OR
            (lsn1.n_name = '{nation2}' AND n2.n_name = '{nation1}')
        )
        AND lsn1.l_shipdate BETWEEN DATE '1995-01-01'
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
