TEMPLATE_Q2 = """
SELECT
    s.s_acctbal,
    s.s_name,
    nr.n_name,
    pp.p_partkey,
    pp.p_mfgr,
    s.s_address,
    s.s_phone,
    s.s_comment
FROM
    {source2} pp,
    supplier s,
    {source1} nr
WHERE
    s.s_suppkey = pp.ps_suppkey
    AND pp.p_size = {p_size}
    AND pp.p_type LIKE '%{type_suffix}'
    AND s.s_nationkey = nr.n_nationkey
    AND nr.r_name = '{region}'
    AND pp.ps_supplycost = (
        SELECT
            MIN(pp2.ps_supplycost)
        FROM
            {source2} pp2,
            supplier s2,
            {source1} nr2
        WHERE
            pp2.ps_partkey = pp.p_partkey
            AND s2.s_suppkey = pp2.ps_suppkey
            AND s2.s_nationkey = nr2.n_nationkey
            AND nr2.r_name = '{region}'
    )
ORDER BY
    s.s_acctbal DESC,
    nr.n_name,
    s.s_name,
    pp.p_partkey;
"""
