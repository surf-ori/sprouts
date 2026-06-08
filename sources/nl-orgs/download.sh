source ./setup.sh download "nl-orgs"

for file in $(zenodo_filelist 18957154)
    do echo $file >> $log_file
    2>> $log_file curl $file | tar -xf -
done
