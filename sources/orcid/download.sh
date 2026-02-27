source ./setup.sh download orcid

curl https://api.figshare.com/v2/articles/30375589/files |
    jq -r '.[] | [.name, .download_url] | join(" ")' |
    xargs -t -L1 2>> $log_file curl -L -o

# function figshare_filelist {
#     curl https://api.figshare.com/v2/articles/${1}/files | jq -r '.[] | [.name, .download_url] | join(" ")'
# }

# for file in $(figshare_filelist 30375589)
#     do echo $file >> $log_file
#     2>> $log_file curl $file | tar -xf -
# done