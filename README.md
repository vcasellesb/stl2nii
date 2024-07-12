# STL to NIFTI file converter

This Python file will convert your STL meshes into NIFTI files. This "tool" is intended for researchers working on biomedical imaging, so the code is structured in a way that requires you to provide an input image to map the "labels" to. Please, if you've found this code useful don't forget to give it a star!

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

A few things in the code were hardcoded, and now have been hidden away with a flag. You can still activate them with the ```--weird_behavior``` flag. Namely, these were:
- Rotating the converted `stl` array (see lines 100 and 133-138).
- At the start of the `.vtk` -> `.nii` conversion, I used to set the origin of the output `sitk.Image` to `(0, 0, 0)`. I've been told that this is not optimal, since obviously you wanna set the so that it matches the reference, so now the default behavior is using the reference origin. However, in my use case, the only way to successfully convert the `stl` meshes is to set it to `(0, 0, 0)`. Please consider this point if the code doesn't work in your case.

If the default, not-doing-these-things behavior does not work, consider activating the aforementioned hardcoded parameters with said flag. They work for my `.stl` files (which I'm starting to think suck), so it might work in your case too.