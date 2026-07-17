TEMPLATE_Q20 = """
SELECT DISTINCT
    sn.s_name,
    sn.s_address
FROM
    {source1} lpsp,
    {source2} sn
WHERE
    sn.s_suppkey = lpsp.ps_suppkey
    AND sn.n_name = '{nation}'
    AND lpsp.p_name LIKE '{p_name}'
    AND EXISTS (
        SELECT 1
        FROM {source1} lpsp1
        WHERE
            lpsp1.ps_suppkey = lpsp.ps_suppkey
            AND lpsp1.ps_partkey = lpsp.ps_partkey
        GROUP BY
            lpsp1.ps_suppkey,
            lpsp1.ps_partkey
        HAVING
            COUNT(*) FILTER (
                WHERE lpsp1.l_shipdate >= DATE '{date}'
                  AND lpsp1.l_shipdate < DATE '{date}' + INTERVAL '1 year'
            ) > 0
            AND MAX(lpsp1.ps_availqty) >
                0.5 * SUM(lpsp1.l_quantity) FILTER (
                    WHERE lpsp1.l_shipdate >= DATE '{date}'
                      AND lpsp1.l_shipdate < DATE '{date}' + INTERVAL '1 year'
                )
    )
ORDER BY
    sn.s_name;
"""
