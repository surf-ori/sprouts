source ./setup.sh openaire

function zenodo_filelist {
    curl https://zenodo.org/api/deposit/depositions/${1}/files | jq -r '.[].links.download'
}

for file in $(zenodo_filelist 14891799)
    do echo $file >> $log_file
    2>> $log_file curl $file | tar -xf -
done