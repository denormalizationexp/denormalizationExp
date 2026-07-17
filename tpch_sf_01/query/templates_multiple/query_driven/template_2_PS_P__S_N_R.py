TEMPLATE_Q2 = """
SELECT
    snr.s_acctbal,
    snr.s_name,
    snr.n_name,
    pp.p_partkey,
    pp.p_mfgr,
    snr.s_address,
    snr.s_phone,
    snr.s_comment
FROM
    {source1} pp,
    {source2} snr
WHERE
    pp.ps_suppkey = snr.s_suppkey
    AND pp.p_size = {p_size}
    AND pp.p_type LIKE '%{type_suffix}'
    AND snr.r_name = '{region}'
    AND pp.ps_supplycost = (
        SELECT
            MIN(pp2.ps_supplycost)
        FROM
            {source1} pp2,
            {source2} snr2
        WHERE
            pp2.ps_partkey = pp.p_partkey
            AND pp2.ps_suppkey = snr2.s_suppkey
            AND snr2.r_name = '{region}'
    )
ORDER BY
    snr.s_acctbal DESC,
    snr.n_name,
    snr.s_name,
    pp.p_partkey;
"""
