#!/bin/bash

# $1 should contain the "bigger" object you want to add $2 to.
# that is, $2 will be preserved while $1's part that intersects 
# with $2 will be removed from $1 ($2 has priority).

set -o nounset

while getopts :rd: opt; do   
    case $opt in 
        r) reverse=true ;;
        d) working_dir=${OPTARG} ;;
        :) echo "Missing argument for option -$OPTARG"; exit 1;;
       \?) echo "Unknown option -$OPTARG"; exit 1;;
    esac
done
shift $(( OPTIND - 1 ))

# positional arguments
total_accumulated=$1
new_object=$2
out=${3:-"$total_accumulated"}

# flag args
reverse=${reverse:-"false"}
default_wd=$(dirname $out)
working_dir=${working_dir:-$default_wd}

mkdir "$working_dir"/.tmp_sum/

if $reverse; then
    echo $total_accumulated has priority over $new_object
else
    echo $new_object has priority over $total_accumulated
fi

# binaritzem la mascara amb tot el que portem sumat
seg_maths ${total_accumulated} -bin "$working_dir"/.tmp_sum/TA-bin.nii.gz
# binaritzem la nova dent o objecte a afegir
seg_maths ${new_object} -bin "$working_dir"/.tmp_sum/NO-bin.nii.gz

# Compute intersection
seg_maths "$working_dir"/.tmp_sum/TA-bin.nii.gz -mul "$working_dir"/.tmp_sum/NO-bin.nii.gz "$working_dir"/.tmp_sum/intersection.nii.gz

# Flip intersection (everywhere where there is no intersection will be 1, where there is intersection will be 0)
seg_maths "$working_dir"/.tmp_sum/intersection.nii.gz -sub 1 -abs "$working_dir"/.tmp_sum/intersection-inv.nii.gz

# Jo prefereixo l’opció girada després hi ha l’opció girada on és més important el que ja hi ha i esborrem els voxels conflictius de l’objecte
if $reverse; then
    seg_maths ${new_object} -mul "$working_dir"/.tmp_sum/intersection-inv.nii.gz -add ${total_accumulated} ${out}
else
    seg_maths ${total_accumulated} -mul "$working_dir"/.tmp_sum/intersection-inv.nii.gz -add ${new_object} ${out}
fi

rm -r "$working_dir"/.tmp_sum/