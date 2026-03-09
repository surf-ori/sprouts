raw_data_path=$(jq -r '."raw-data-path"' <config_current.json)/${2}/
log_path=$(pwd)/$(jq -r '."log-path"' <config_current.json)/${2}/
log_file=${log_path}${1}-$(date -Iseconds -u).txt

mkdir -p $log_path
touch $log_file

mkdir -p $raw_data_path
cd $raw_data_path

function zenodo_filelist {
    curl https://zenodo.org/api/deposit/depositions/${1}/files | jq -r '.[].links.download'
}

