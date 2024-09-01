#!/bin/bash

# what should this do??
# in short: take a bunch of directories where there are DICOM files, generate NIFTI file
# actually... 
#   * check if there are any nifti files already in the directory
#   * if True, then skip that iteration

filestodcm="${@:1}"
for file in $filestodcm
do
    
    already=$(ls "$file"/*.nii* 2> /dev/null | wc -l)
    if [ $already -gt 0 ]
    then
        echo "$file already has nii file, skipping it"
        continue
    else
        dcm2niix $file
        gzip $file/*.nii
    fi
done
exit