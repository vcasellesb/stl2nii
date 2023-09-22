# STL to NIFTI file converter

This Python file will convert your STL meshes into NIFTI files. The way the code is structured requires you to give as an input a NIFTI file the STL meshes map to.

## Usage

`python3 [PATH_TO_WHERE_THE stl2nii.py_FILE_IS_LOCATED] -i [INPUT_STL.stl (can be more than 1)] -ref [REF_NIFTI.nii(.gz) -o [OUTPUT_FOLDER_WHERE_FILES_WILL_BE_WRITTEN_TO]]`


This function is VERY slow, aprox 4 min per stl mesh on my computer. Mainly, this is because of the usage of vtk to read/write files. I will be studying how to improve this.