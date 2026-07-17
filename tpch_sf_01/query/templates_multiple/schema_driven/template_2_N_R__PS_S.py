TEMPLATE_Q2 = """
SELECT
    pss.s_acctbal,
    pss.s_name,
    nr.n_name,
    p.p_partkey,
    p.p_mfgr,
    pss.s_address,
    pss.s_phone,
    pss.s_comment
FROM
    part p,
    {source2} pss,
    {source1} nr
WHERE
    p.p_partkey = pss.ps_partkey
    AND p.p_size = {p_size}
    AND p.p_type LIKE '%{type_suffix}'
    AND pss.s_nationkey = nr.n_nationkey
    AND nr.r_name = '{region}'
    AND pss.ps_supplycost = (
        SELECT
            MIN(pss2.ps_supplycost)
        FROM
            {source2} pss2,
            {source1} nr2
        WHERE
            pss2.ps_partkey = p.p_partkey
            AND pss2.s_nationkey = nr2.n_nationkey
            AND nr2.r_name = '{region}'
    )
ORDER BY
    pss.s_acctbal DESC,
    nr.n_name,
    pss.s_name,
    p.p_partkey;
"""
