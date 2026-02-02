ATTACH 'ducklake:{datapath}/{datalake}.ducklake' as {datalake};
USE {datalake};

COMMENT ON TABLE {dataset}.{table} IS '{description}';

USE memory;
DETACH sprouts;