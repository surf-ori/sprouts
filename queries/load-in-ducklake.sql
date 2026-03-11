CREATE SCHEMA IF NOT EXISTS {dataset};

CREATE OR REPLACE TABLE {dataset}."{table}" ({tableschemasql});

CALL ducklake_add_data_files('{datalake}', '{table}', 
                '{datapath}/{dataset}/{table}/*.parquet', schema => '{dataset}');
