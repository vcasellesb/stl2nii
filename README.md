# STL to NIFTI file converter

This Python file will convert your STL meshes into NIFTI files. The way the code is structured requires you to give as an input a NIFTI file the STL meshes map to.

## Usage

```bash
python3 /path/to/stl2nii -i [.stl files] -ref [.nii/.nii.gz file to map stl to its space (usually the image the stl comes from)] -o [/path/to/desired/out/folder]]
```