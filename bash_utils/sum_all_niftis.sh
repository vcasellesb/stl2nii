#!/bin/bash

set -e

## Script to add all parts
if [[ $# -eq 0 ]]; then
    echo "No directory specified, using current directory"
    target_dir="."
else
    target_dir="$1"
fi


nifti_count=$(find "$target_dir" -type f -name "*.nii.gz" | wc -l)
if [[ $nifti_count -lt 1 ]]; then
    echo "No nifti files found in $target_dir directory, exiting. Please provide a valid dir"
    exit 1
fi

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)


# if files are numbered, we are dealing with NEMOTEC; otherwise with Bluesky
numbered_files=$(find "$target_dir" -maxdepth 1 -name "*[0-9][0-9]*.nii.gz" -print -quit)

if [[ -n "$numbered_files" ]]; then
    # We store the search arguments in arrays to pass them cleanly to `find` later
    find_args_mandible=("-iregex" ".*/mand[ií]u?bl[ea].*\.nii.gz")
    find_args_nerves=("-iregex" ".*/nervi?[oe]s.*\.nii.gz")
    find_args_maxillary=("-iregex" ".*/(maxill?ary?|skull).*\.nii.gz")
    
    patternLR=".*/.*4[1-9].*\.nii.gz$"
    patternLL=".*/.*3[1-9].*\.nii.gz$"
    patternUR=".*/.*1[1-9].*\.nii.gz$"
    patternUL=".*/.*2[1-9].*\.nii.gz$"
else
    find_args_mandible=("-iregex" ".*/[Mm]and[ií]bula.*\.nii.gz")
    find_args_nerves=("-name" "Nerve*")
    find_args_maxillary=("-name" "*maxilar.nii.gz")

    patternLR=".*/.*LR.*\.nii.gz$"
    patternLL=".*/.*LL.*\.nii.gz$"
    patternUR=".*/.*UR.*\.nii.gz$"
    patternUL=".*/.*UL.*\.nii.gz$"
fi

# 'IFS= ' sets the Internal Field Separator to the null character, so that whitespaces are not trimmed
# during variable assignment (by default, IFS is white space, tab and newline). 
# "read d ''" makes the command not split strings by white space (default), but rather by what find
# sends it with '-print0', which is the null character.
IFS= read -r -d '' mandible < <(find -E "$target_dir" -maxdepth 1 "${find_args_mandible[@]}" -print0)
IFS= read -r -d '' maxillary < <(find -E "$target_dir" -maxdepth 1 "${find_args_maxillary[@]}" -print0)

# Safely extract multiple files into arrays using null-separators (-d '') and zero-byte sorting (-z)
nerves_array=()
while IFS= read -r -d "" nerve; do
	nerves_array+=("$nerve")
done < <(find "$target_dir" -maxdepth 1 "${find_args_nerves[@]}" -print0 | sort -z)

# Helper function to find and sort teeth, outputting a null-terminated stream
find_teeth() {
    local pattern="$1"
    local sort_flag="$2"
    if [[ "$sort_flag" == "rev" ]]; then
        find -E "$target_dir" -maxdepth 1 -regex "$pattern" -print0 | sort -z
    else
        find -E "$target_dir" -maxdepth 1 -regex "$pattern" -print0 | sort -z -r
    fi
}

# Populate teeth arrays
lw_teeth_right=()
while IFS= read -r -d "" teeth; do
	lw_teeth_right+=("$teeth")
done < <(find_teeth "$patternLR" "rev")

lw_teeth_left=()
while IFS= read -r -d "" teeth; do
	lw_teeth_left+=("$teeth")
done < <(find_teeth "$patternLL" "")

lw_teeth=("${lw_teeth_left[@]}" "${lw_teeth_right[@]}")

up_teeth_right=()
while IFS= read -r -d "" teeth; do
	up_teeth_right+=("$teeth")
done < <(find_teeth "$patternUR" "rev")

up_teeth_left=()
while IFS= read -r -d "" teeth; do
	up_teeth_left+=("$teeth")
done < <(find_teeth "$patternUL" "")

up_teeth=("${up_teeth_right[@]}" "${up_teeth_left[@]}")

# Handle case where l/r nerves are in different files
nerves_combined="$target_dir/nerves_tmp.nii.gz"
if [[ ${#nerves_array[@]} -gt 0 ]]; then
    seg_maths "$mandible" -mul 0 "$nerves_combined"
    for nerve in "${nerves_array[@]}"; do
        seg_maths "$nerves_combined" -add "$nerve" "$nerves_combined"
    done
else
    nerves_combined=""
fi

#### THIS IS FOR THE LOWER PART OF THE MOUTH
if [[ -z "$mandible" ]] && [[ ${#lw_teeth[@]} -eq 0 ]]; then
    echo "Neither Mandible nor lower teeth found."
else
    # we initialize where we are gonna leave everything
    seg_maths "$mandible" -mul 1 "$target_dir/inf.nii.gz"
    fac=2
    for teeth in "${lw_teeth[@]}"; do
        seg_maths "$teeth" -mul $fac "$teeth"
        "$SCRIPT_DIR/intersection.sh" -d "${target_dir}" "$target_dir/inf.nii.gz" "$teeth"
        fac=$((fac + 1))
    done

    # Process combined nerves if they exist
    if [[ -n "$nerves_combined" && -f "$nerves_combined" ]]; then
        seg_maths "$nerves_combined" -mul $fac "$nerves_combined"
        "$SCRIPT_DIR/intersection.sh" -d "${target_dir}" "$target_dir/inf.nii.gz" "$nerves_combined"
    fi
fi

#### NOW COMES THE UPPER MOUTH
if [[ -z "$maxillary" ]] && [[ ${#up_teeth[@]} -eq 0 ]]; then
    echo "Neither maxillary nor upper teeth found"
else
    seg_maths "$maxillary" -mul 1 "$target_dir/sup.nii.gz"

    # now we iterate through all upper teeth
    fac=2
    for teeth in "${up_teeth[@]}"; do
        seg_maths "$teeth" -mul $fac "$teeth"
        "$SCRIPT_DIR/intersection.sh" -d "${target_dir}" "${target_dir}/sup.nii.gz" "$teeth"
        fac=$((fac + 1))
    done
fi

echo "Done"