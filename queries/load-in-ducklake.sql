ATTACH 'ducklake:{datapath}/{datalake}.ducklake' as {datalake};
USE {datalake};

CREATE SCHEMA IF NOT EXISTS {dataset};

CREATE OR REPLACE TABLE {dataset}.{table} AS
        FROM '{datapath}/{dataset}/{table}/*.parquet'
        WITH NO DATA;

CALL ducklake_add_data_files('{datalake}', '{table}', 
                '{datapath}/{dataset}/{table}/*.parquet', schema => '{dataset}');

USE memory;
DETACH sprouts;