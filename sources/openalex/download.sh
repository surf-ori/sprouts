source ./setup.sh download openalex

>>$log_file 2>>$log_file aws s3 cp s3://openalex/data . --recursive --no-sign-request --region us-east-1