.shell mkdir -p {datapath}/{dataset}/{table}

COPY (
     FROM read_xlsx('{rawdatapath}/{dataset}/{tablepath}')
)
TO '{datapath}/{dataset}/{table}' (FORMAT parquet, FILE_SIZE_BYTES '2gb');