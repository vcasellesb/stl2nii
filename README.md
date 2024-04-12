# STL to NIFTI file converter

This Python file will convert your STL meshes into NIFTI files. This "tool" is intended for researchers working on biomedical imaging, so the code is structured in a way that requires you to provide an input image to map the "labels" to.

**WARNING**: Default setting casts the output NIFTI numpy array to UINT8. To change this behavior, use the `-dtype` flag.

## Usage

```bash
python3 /path/to/stl2nii -i [.stl file(s)] -ref [.nii/.nii.gz file to map stl to its space (usually the image the stl comes from)] -o [/path/to/desired/output/folder]]
```

### Example Usage:

Let's say I want to convert a bunch of STL meshes I've obtained by segmenting the image corresponding to patient 225 using my favourite automatic segmentation tool. These are in my Downloads folder, and I want to generate NIFTI files mapped to the original image. I'd do it like this:

```bash
python3 ~/work/research/stl2nii -i ~/Downloads/P225/*.stl -ref data/P225/image/data_P225.nii.gz -o data/P225/labels/nii
```