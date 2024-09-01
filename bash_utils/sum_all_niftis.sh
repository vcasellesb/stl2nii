#!/bin/bash

## Script to add all parts
if [[ $# -eq 0 ]]; then
	echo "No directory specified, using current directory"
	target_dir="./"
else
	target_dir="$1/"
fi

nifti_in_target_files=$(ls "${target_dir}"*.nii.gz | wc -l)

if [[ $nifti_in_target_files -lt 1 ]]; then
	echo "No nifti files found in $target_dir directory, exitting. Please provide a valid dir"
	exit 1
fi

# This part removes the nasty disgusting spaces
## TODO: do the same but for the dirs (I'm tired of doing this manually)
if [[ $(ls "$target_dir"*\ * 2>/dev/null | wc -l) -gt 0 ]]; then
	for file in "${target_dir}"*' '*; do mv "$file" $(echo $file | tr ' ' '_'); done
fi

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)

if [[ $(ls "$target_dir"[0-9][0-9].nii.gz 2>/dev/null | wc -l) -gt 0 ]]; then
	patternLR=(-regex ".*/([4][0-9]|6[0-7])\.nii.gz$")
	patternLL=(-regex ".*/([3][0-9]|6[0-7])\.nii.gz$")
	patternUR=(-regex ".*/([1][0-9]|6[0-7])\.nii.gz$")
	patternUL=(-regex ".*/([2][0-9]|6[0-7])\.nii.gz$")
	mandible=$(ls "$target_dir"[Mm]and[ií]bula.nii.gz)
	nerves=$(ls "$target_dir"[Nn]ervios.nii.gz)	
	maxillary=$(ls "$target_dir"[Mm]axilar.nii.gz)
else
	patternLR=(-name "*LR*")
	patternLL=(-name "*LL*")
	patternUR=(-name "*UR*")
	patternUL=(-name "*UL*")
	mandible=$(ls "$target_dir"*[Mm]and[ií]bula*.nii.gz)
	nerve1=$(ls "${target_dir}"Nerve* | head -n1)
	nerve2=$(ls "${target_dir}"Nerve* | head -n2 | tail -1)
	seg_maths $nerve1 -add $nerve2 "${target_dir}"nerves.nii.gz
	nerves=$(ls ${target_dir}nerves.nii.gz)
	maxillary=$(ls "$target_dir"*maxilar.nii.gz)
fi

#### THIS IS FOR THE LOWER PART OF THE MOUTH
# now we search the lower area teeth
lw_teeth_right=$(find -E $target_dir -type f "${patternLR[@]}" | xargs -n1 | sort -r | xargs)
lw_teeth_left=$(find -E $target_dir -type f "${patternLL[@]}" | sort)
lw_teeth="$lw_teeth_right $lw_teeth_left"

# If we don't find mandible, STOP
if [ -z "$mandible" ] && [ -z "$maxillary" ]; then
	echo "Mandible nor maxillary not found. Exiting"
	exit
fi

# we initialize where we are gonna leave everything
seg_maths $mandible -mul 0 "${target_dir}"inf.nii.gz
fac=1
$SCRIPT_DIR/intersection.sh "${target_dir}"inf.nii.gz $mandible "$target_dir"

for tooth in $lw_teeth; do
	fac=$((fac + 1))
	seg_maths $tooth -mul $fac $tooth
	$SCRIPT_DIR/intersection.sh "${target_dir}"inf.nii.gz $tooth $target_dir
done

# now we add the nerves
if [ -f $nerves ]; then
	factor_to_multiply_nerves=$((fac + 1))
	seg_maths $nerves -mul $factor_to_multiply_nerves $nerves
	$SCRIPT_DIR/intersection.sh "${target_dir}"inf.nii.gz $nerves "$target_dir"
fi

#### NOW COMES THE UPPER MOUTH
up_teeth_right=$(find -E $target_dir -type f "${patternUR[@]}" | xargs -n1 | sort -r | xargs)
up_teeth_left=$(find -E $target_dir -type f "${patternUL[@]}" | sort)
up_teeth="$up_teeth_right $up_teeth_left"

seg_maths $maxillary -mul 0 "${target_dir}"sup.nii.gz

# now we iterate through all upper teeth
fac=1
$SCRIPT_DIR/intersection.sh "${target_dir}"sup.nii.gz $maxillary "$target_dir"
for tooth in $up_teeth; do
	fac=$((fac + 1))
	seg_maths $tooth -mul $fac $tooth
	$SCRIPT_DIR/intersection.sh "${target_dir}"sup.nii.gz ${tooth} $target_dir
done