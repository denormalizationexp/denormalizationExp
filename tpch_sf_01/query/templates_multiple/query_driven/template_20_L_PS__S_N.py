TEMPLATE_Q20 = """
SELECT DISTINCT
    sn.s_name,
    sn.s_address
FROM
    {source1} lps,
    {source2} sn,
    part p
WHERE
    sn.s_suppkey = lps.ps_suppkey
    AND sn.n_name = '{nation}'
    AND p.p_partkey = lps.ps_partkey
    AND p.p_name LIKE '{p_name}'
    AND EXISTS (
        SELECT 1
        FROM {source1} lps1
        WHERE
            lps1.ps_suppkey = lps.ps_suppkey
            AND lps1.ps_partkey = lps.ps_partkey
        GROUP BY
            lps1.ps_suppkey,
            lps1.ps_partkey
        HAVING
            COUNT(*) FILTER (
                WHERE lps1.l_shipdate >= DATE '{date}'
                  AND lps1.l_shipdate < DATE '{date}' + INTERVAL '1 year'
            ) > 0
            AND MAX(lps1.ps_availqty) >
                0.5 * SUM(lps1.l_quantity) FILTER (
                    WHERE lps1.l_shipdate >= DATE '{date}'
                      AND lps1.l_shipdate < DATE '{date}' + INTERVAL '1 year'
                )
    )
ORDER BY
    sn.s_name;
"""



