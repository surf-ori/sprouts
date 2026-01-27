raw_data_path=$(jq -r '."raw-data-path"' < ../config.json)/openalex/
log_file=$(jq -r '."log-path"' < ../config.json)/openalex/download/$(date -Iseconds -u).txt

aws s3 cp s3://openalex/data $raw_data_path --recursive --no-sign-request --region us-east-1 --no-progress >> $log_file