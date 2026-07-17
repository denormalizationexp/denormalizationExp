TEMPLATE_Q2 = """
SELECT
    psp.s_acctbal,
    psp.s_name,
    nr.n_name,
    psp.p_partkey,
    psp.p_mfgr,
    psp.s_address,
    psp.s_phone,
    psp.s_comment
FROM
    {source2} psp,
    {source1} nr
WHERE
    psp.p_size = {p_size}
    AND psp.p_type LIKE '%{type_suffix}'
    AND psp.s_nationkey = nr.n_nationkey
    AND nr.r_name = '{region}'
    AND psp.ps_supplycost = (
        SELECT
            MIN(psp2.ps_supplycost)
        FROM
            {source2} psp2,
            {source1} nr2
        WHERE
            psp2.ps_partkey = psp.p_partkey
            AND psp2.s_nationkey = nr2.n_nationkey
            AND nr2.r_name = '{region}'
    )
ORDER BY
    psp.s_acctbal DESC,
    nr.n_name,
    psp.s_name,
    psp.p_partkey;
"""
