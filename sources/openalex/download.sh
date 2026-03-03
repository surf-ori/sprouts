source ./setup.sh download openalex

&>> $logfile aws s3 cp s3://openalex/data . --recursive --no-sign-request --region us-east-1