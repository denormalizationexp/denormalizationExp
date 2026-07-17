TEMPLATE_Q2 = """
SELECT
    sn.s_acctbal,
    sn.s_name,
    sn.n_name,
    pp.p_partkey,
    pp.p_mfgr,
    sn.s_address,
    sn.s_phone,
    sn.s_comment
FROM
    {source1} pp,
    {source2} sn,
    region r
WHERE
    pp.ps_suppkey = sn.s_suppkey
    AND pp.p_size = {p_size}
    AND pp.p_type LIKE '%{type_suffix}'
    AND sn.n_regionkey = r.r_regionkey
    AND r.r_name = '{region}'
    AND pp.ps_supplycost = (
        SELECT
            MIN(pp2.ps_supplycost)
        FROM
            {source1} pp2,
            {source2} sn2,
            region r2
        WHERE
            pp2.ps_partkey = pp.p_partkey
            AND pp2.ps_suppkey = sn2.s_suppkey
            AND sn2.n_regionkey = r2.r_regionkey
            AND r2.r_name = '{region}'
    )
ORDER BY
    sn.s_acctbal DESC,
    sn.n_name,
    sn.s_name,
    pp.p_partkey;
"""
