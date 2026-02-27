source ./setup.sh download openalex

>> $log_file aws s3 cp s3://openalex/data /Users/bey00001/dev/sprouts/build/raw-data/openalex --recursive --no-sign-request --region us-east-1