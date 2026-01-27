raw_data_path=$(jq -r '."raw-data-path"' <../config.json)/orcid/
log_file=$(jq -r '."log-path"' < ../config.json)/openalex/download/$(date -Iseconds -u).txt

cd $raw_data_path

curl https://api.figshare.com/v2/articles/30375589/files |
    jq -r '.[] | [.name, .download_url] | join(" ")' |
    xargs -t -L1 2>> $log_file curl -L -o