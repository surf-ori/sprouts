.shell mkdir -p {datapath}/{dataset}/{table}

ATTACH 'ducklake:{datapath}/{datalake}.ducklake' as {datalake};
USE {datalake};

COPY (
     FROM read_csv('{rawdatapath}/{dataset}/{tablepath}', header=true, columns = {tableschema})
)
TO '{datapath}/{dataset}/{table}' (FORMAT parquet, FILE_SIZE_BYTES '2gb');

USE memory;
DETACH sprouts;