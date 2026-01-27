raw_data_path=$(jq -r '."raw-data-path"' <../config.json)/openaire/
log_file=$(jq -r '."log-path"' < ../config.json)/download-$(date -Iseconds -u).log

cd $raw_data_path

curl https://zenodo.org/api/deposit/depositions/17098012/files |
    jq -r '.[] | [.filename, .links.download] | join(" ")' |
    xargs -t -L1 2>> $log_file curl -o