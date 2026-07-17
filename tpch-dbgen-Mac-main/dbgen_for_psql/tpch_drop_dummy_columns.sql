-- =========================================================
-- Remove dummy columns used for TPC-H .tbl trailing delimiter
-- =========================================================

ALTER TABLE region   DROP COLUMN _dummy;
ALTER TABLE nation   DROP COLUMN _dummy;
ALTER TABLE part     DROP COLUMN _dummy;
ALTER TABLE supplier DROP COLUMN _dummy;
ALTER TABLE partsupp DROP COLUMN _dummy;
ALTER TABLE customer DROP COLUMN _dummy;
ALTER TABLE orders   DROP COLUMN _dummy;
ALTER TABLE lineitem DROP COLUMN _dummy;

