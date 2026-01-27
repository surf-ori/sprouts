.shell mkdir -p {datapath}/{dataset}/{table}

COPY (
     FROM read_json('{rawdatapath}/{dataset}/{tablepath}', columns = {tableschema})
)
TO '{datapath}/{dataset}/{table}' (FORMAT parquet, FILE_SIZE_BYTES '2gb');