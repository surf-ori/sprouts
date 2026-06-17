source ./setup.sh download openaire

for file in $(zenodo_filelist 20428976)
    do echo $file >> $log_file
    2>> $log_file curl $file | tar -xf -
done
