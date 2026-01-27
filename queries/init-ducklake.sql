.shell mkdir -p {datapath}

ATTACH 'ducklake:{datapath}/{datalake}.ducklake' as {datalake} (DATA_PATH {datapath});
USE {datalake};