TEMPLATE_Q21 = """
SELECT
    sn.s_name,
    COUNT(*) AS numwait
FROM
    {source1} lo,
    {source2} sn
WHERE
    sn.s_suppkey = lo.l_suppkey
    AND lo.o_orderstatus = 'F'
    AND lo.l_receiptdate > lo.l_commitdate
    AND EXISTS (
        SELECT 1
        FROM {source1} lo2
        WHERE lo2.l_orderkey = lo.l_orderkey
          AND lo2.l_suppkey <> lo.l_suppkey
    )
    AND NOT EXISTS (
        SELECT 1
        FROM {source1} lo3
        WHERE lo3.l_orderkey = lo.l_orderkey
          AND lo3.l_suppkey <> lo.l_suppkey
          AND lo3.l_receiptdate > lo3.l_commitdate
    )
    AND sn.n_name = '{nation}'
GROUP BY
    sn.s_name
ORDER BY
    numwait DESC,
    sn.s_name;
"""
