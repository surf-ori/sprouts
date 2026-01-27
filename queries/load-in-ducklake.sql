CREATE SCHEMA IF NOT EXISTS {dataset};

CREATE TABLE {dataset}.{table} AS
        FROM '{datapath}/{dataset}/{table}/*.parquet'
        WITH NO DATA;

CALL ducklake_add_data_files('{datalake}', '{table}', 
                '{datapath}/{dataset}/{table}/*.parquet', schema => '{dataset}');