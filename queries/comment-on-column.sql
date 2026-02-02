ATTACH 'ducklake:{datapath}/{datalake}.ducklake' as {datalake};
USE {datalake};

COMMENT ON COLUMN {dataset}.{table}."{column}" IS '{description}';

USE memory;
DETACH sprouts;