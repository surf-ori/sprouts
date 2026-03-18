source ./setup.sh download openalex

d="works/updated_date=2026-02-01"

>>$log_file 2>>$log_file aws s3 cp s3://openalex/data/$d $d --recursive --no-sign-request --region us-east-1