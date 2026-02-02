source ./setup.sh openapc

files="https://github.com/OpenAPC/openapc-de/raw/refs/heads/master/data/apc_de.csv https://github.com/OpenAPC/openapc-de/raw/refs/heads/master/data/apc_de_additional_costs.csv https://github.com/OpenAPC/openapc-de/raw/refs/heads/master/data/bpc.csv https://github.com/OpenAPC/openapc-de/raw/refs/heads/master/data/transformative_agreements/transformative_agreements.csv"

for file in $(echo $files)
    do echo $file >> $log_file
    2>> $log_file curl $file -L -O
done
