-- .shell rm -rf {catalogpath}
-- .shell mkdir -p {catalogpath}

ATTACH 'ducklake:{catalogpath}/{datalake}.ducklake' as {datalake} (DATA_PATH "{datapath}");
USE {datalake};