source ./setup.sh openapc

files="\
https://github.com/OpenAPC/openapc-de/raw/refs/tags/v4.167.1-0-1/data/apc_de.csv \
https://github.com/OpenAPC/openapc-de/raw/refs/tags/v4.167.1-0-1/data/apc_de_additional_costs.csv \
https://github.com/OpenAPC/openapc-de/raw/refs/tags/v4.167.1-0-1/data/bpc.csv \
https://github.com/OpenAPC/openapc-de/raw/refs/tags/v4.167.1-0-1/data/transformative_agreements/transformative_agreements.csv\
"

for file in $(echo $files)
    do echo $file >> $log_file
    2>> $log_file curl $file -L -O
done
