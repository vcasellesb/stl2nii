#!/bin/bash

mkdir "$3"tmp_sum/

# binaritzem la mascara amb tot el que portem sumat
seg_maths ${1} -bin "$3"tmp_sum/TA-bin.nii.gz
# binaritzem la nova dent o objecte a afegir
seg_maths ${2} -bin "$3"tmp_sum/NO-bin.nii.gz

# Calculem la intersecció
seg_maths "$3"tmp_sum/TA-bin.nii.gz -mul "$3"tmp_sum/NO-bin.nii.gz "$3"tmp_sum/intersection.nii.gz

# Fem el flip de la interseccio per poder esborrar els voxels conflictius
seg_maths "$3"tmp_sum/intersection.nii.gz -sub 1 -abs "$3"tmp_sum/intersection-inv.nii.gz

# Jo prefereixo l’opció girada després hi ha l’opció girada on és més important el que ja hi ha i esborrem els voxels conflictius de l’objecte
seg_maths ${1} -mul "$3"tmp_sum/intersection-inv.nii.gz -add ${2} ${1}

rm -r "$3"tmp_sum/