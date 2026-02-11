-- .shell mkdir -p {datapath}/{dataset}/{table}

COPY (
     FROM read_csv('{rawdatapath}/{dataset}/{tablepath}', header=true, columns = {tableschema})
)
TO '{datapath}/{dataset}/{table}' (FORMAT parquet, FILE_SIZE_BYTES '2gb');