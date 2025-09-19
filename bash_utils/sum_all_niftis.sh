#!/bin/bash

set -e

## Script to add all parts
if [[ $# -eq 0 ]]; then
	echo "No directory specified, using current directory"
	target_dir="."
else
	target_dir="$1"
fi

nifti_in_target_files=$(ls "${target_dir}"/*.nii.gz | wc -l)

if [[ $nifti_in_target_files -lt 1 ]]; then
	echo "No nifti files found in "$target_dir" directory, exitting. Please provide a valid dir"
	exit 1
fi

# This part removes the nasty disgusting spaces
## TODO: do the same but for the dirs (I'm tired of doing this manually)
if [[ $(ls "$target_dir"/*\ * 2>/dev/null | wc -l) -gt 0 ]]; then
	for file in "${target_dir}"/*' '*; do
		mv "$file" $(echo "$file" | tr ' ' '_')
	done
fi

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)

if [[ $(ls "$target_dir"/*[0-9][0-9]*.nii.gz 2>/dev/null | wc -l) -gt 0 ]]; then
	patternLR="$target_dir/.*4[1-9].*\.nii.gz$"
	patternLL="$target_dir/.*3[1-9].*\.nii.gz$"
	patternUR="$target_dir/.*1[1-9].*\.nii.gz$"
	patternUL="$target_dir/.*2[1-9].*\.nii.gz$"
	mandible=$(find "$target_dir" -maxdepth 1 -iregex "$target_dir/mand[ií]u\{0,1\}bl[ea].*\.nii.gz" 2>/dev/null)
	nerves=$(find "$target_dir" -maxdepth 1 -iregex "$target_dir/nervi\{0,1\}[oe]s.*\.nii.gz" 2>/dev/null)
	# -E so that we get modern regex. This allows us not to escape {...} and |
	maxillary=$(find -E "$target_dir" -maxdepth 1 -iregex "$target_dir/.*(maxill{0,1}ary{0,1}|skull).*\.nii.gz" 2>/dev/null)
else
	patternLR=".*LR.*$"
	patternLL=".*LL.*$"
	patternUR=".*UR.*$"
	patternUL=".*UL.*$"
	mandible=$(ls "$target_dir"/*[Mm]and[ií]bula*.nii.gz)
	nerves=$(ls "$target_dir"/Nerve*)
	maxillary=$(ls "$target_dir/"*maxilar.nii.gz)
fi

# handle case where l/r nerves are in different files
seg_maths $mandible -mul 0 "$target_dir"/nerves_tmp.nii.gz
for n in $nerves; do
	seg_maths "$target_dir"/nerves_tmp.nii.gz -add $n "$target_dir"/nerves_tmp.nii.gz
done
nerves="$target_dir/nerves_tmp.nii.gz"

#### THIS IS FOR THE LOWER PART OF THE MOUTH
# now we search the lower area teeth
lw_teeth_right=$(find "$target_dir" -maxdepth 1 -regex $patternLR | xargs -n1 | sort -r | xargs)
lw_teeth_left=$(find "$target_dir" -maxdepth 1 -regex $patternLL | sort)
lw_teeth=$(echo "$lw_teeth_left" "$lw_teeth_right")

# If we don't find mandible, STOP
if [ -z "$mandible" ] && [ -z "$lw_teeth" ]; then
	echo "Neither Mandible nor lower teeth found."
else
	# we initialize where we are gonna leave everything
	seg_maths "$mandible" -mul 1 "$target_dir"/inf.nii.gz
	fac=2
	for teeth in $lw_teeth; do
		seg_maths "$teeth" -mul $fac "$teeth"
		$SCRIPT_DIR/intersection.sh -d "${target_dir}" "$target_dir/inf.nii.gz" "$teeth"
		fac=$((fac + 1))
	done
	seg_maths "$nerves" -mul $fac "$nerves"
	$SCRIPT_DIR/intersection.sh -d "${target_dir}" "$target_dir/inf.nii.gz" "$nerves"
fi

#### NOW COMES THE UPPER MOUTH
up_teeth_right=$(find "$target_dir" -maxdepth 1 -regex "$patternUR" | xargs -n1 | sort -r | xargs)
up_teeth_left=$(find "$target_dir" -maxdepth 1 -regex "$patternUL" | sort)
up_teeth=$(echo "$up_teeth_right" $up_teeth_left)

if [ -z "$maxillary" ] && [ -z "$up_teeth" ]; then
	echo "Neither maxillary nor upper teeth found"
else
	seg_maths $maxillary -mul 1 "$target_dir"/sup.nii.gz

	# now we iterate through all upper teeth
	fac=2
	for teeth in $up_teeth; do
		seg_maths "$teeth" -mul $fac "$teeth"
		$SCRIPT_DIR/intersection.sh -d "${target_dir}" "${target_dir}/sup.nii.gz" "$teeth"
		fac=$((fac + 1))
	done
fi

echo "Done"