source ./setup.sh download openaire-sample

for file in $(zenodo_filelist 14891799)
    do echo $file >> $log_file
    2>> $log_file curl $file | tar -xf -
done