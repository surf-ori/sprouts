raw_data_path=$(jq -r '."raw-data-path"' <config.json)/${1}/
log_path=$(pwd)/$(jq -r '."log-path"' <config.json)/${1}/
log_file=${log_path}download-$(date -Iseconds -u).txt

mkdir -p $log_path
touch $log_file

mkdir -p $raw_data_path
cd $raw_data_path