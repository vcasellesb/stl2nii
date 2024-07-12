# STL to NIFTI file converter

This Python file will convert your STL meshes into NIFTI files. This "tool" is intended for researchers working on biomedical imaging, so the code is structured in a way that requires you to provide an input image to map the "labels" to. Please, if you've found this code useful don't forget to give it a star!

**WARNING**: Default setting casts the output NIFTI numpy array to ```uint8```. To change this behavior, use the `-dtype` flag.

## Usage

```bash
python3 /path/to/stl2nii \
    -i [.stl file(s)] \
    -ref [.nii/.nii.gz file to map stl to its space (usually the image the stl comes from)] \
    -o [/path/to/desired/output/folder]
```

### Example Usage:

Let's say I want to convert a bunch of STL meshes I've obtained by segmenting the image corresponding to patient 225 using my favourite automatic segmentation tool. These are in my Downloads folder, and I want to generate NIFTI files mapped to the original image. I'd do it like this:

```bash
python3 ~/work/research/stl2nii \
    -i ~/Downloads/P225/*.stl \
    -ref data/P225/image/data_P225.nii.gz \
    -o data/P225/labels/nii
```

### Disclosures

A few things in the code are hardcoded, so please feel free to experiment whether they work in your case. Namely, these are:
- Rotating the converted stl array (see lines 95 and 126-131).
- At the start of the `.vtk` -> `.nii` conversion, I set the origin of the output to `(0, 0, 0)`. I've been told that this is not optimal, since obviously you wanna set the so that it matches the reference. However, I do this at the end, when loading back the nii file to rotate it (see previous point). Please consider if this behavior is what you wanna. Maybe in the future I'll implement a flag that deactivates this. This behavior is because of how my `.stl` files are, but it might mess up yours.