TEMPLATE_Q20 = """
SELECT DISTINCT
    sn.s_name,
    sn.s_address
FROM
    {source1} psp,
    {source2} sn
WHERE
    sn.s_suppkey = psp.ps_suppkey
    AND sn.n_name = '{nation}'
    AND psp.p_name LIKE '{p_name}'
    AND EXISTS (
        SELECT 1
        FROM
            {source1} psp1,
            lineitem l
        WHERE
            l.l_partkey = psp1.ps_partkey
            AND l.l_suppkey = psp1.ps_suppkey
            AND psp1.ps_suppkey = psp.ps_suppkey
            AND psp1.ps_partkey = psp.ps_partkey
        GROUP BY
            psp1.ps_suppkey,
            psp1.ps_partkey
        HAVING
            COUNT(*) FILTER (
                WHERE l.l_shipdate >= DATE '{date}'
                  AND l.l_shipdate < DATE '{date}' + INTERVAL '1 year'
            ) > 0
            AND MAX(psp1.ps_availqty) >
                0.5 * SUM(l.l_quantity) FILTER (
                    WHERE l.l_shipdate >= DATE '{date}'
                      AND l.l_shipdate < DATE '{date}' + INTERVAL '1 year'
                )
    )
ORDER BY
    sn.s_name;
"""
