# STL to NIFTI file converter

This Python file will convert your STL meshes into NIFTI files. This "tool" is intended for researchers working on biomedical imaging, so the code is structured in a way that requires you to provide an input image to map the "labels" to. Please, if you've found this code useful don't forget to give it a star!

## 16/08/24 UPDATE

Now this software uses `itk`, instead of `vtk` and `SimpleITK`, to actually perform the conversion. I think it's much more simple and reliable. The usage has remained the same.

## Installation

To install `stl2nii`, first clone this repository, and then `cd` to it, i.e.:

```bash
git clone https://github.com/vcasellesb/stl2nii
cd stl2nii
```

Then, run the following command:

```bash
pip install -e .
```
This will install a _binary_ file in your environment (I recommend using `conda`), whereby you'll be able it to call it as `stl2nii` (see next section).

## Usage

```bash
stl2nii -i [.stl file(s)] \
        -ref [.nii/.nii.gz file to map stl to its space (usually the image the stl comes from)] \
        -o [/path/to/desired/output/folder]
```

### Example Usage:

Let's say I want to convert a bunch of STL meshes I've obtained by segmenting the image corresponding to patient 225 using my favourite automatic segmentation tool. These are in my Downloads folder, and I want to generate NIFTI files mapped to the original image. I'd do it like this:

```bash
stl2nii -i ~/Downloads/P225/*.stl \
        -ref data/P225/image/data_P225.nii.gz \
        -o data/P225/labels/nii
```

If you don't specify the output argument (`-o`), they will be saved inside the folder where the `stl` files are located.

## Docker support
I've added an option to run this software in a Docker container, just to avoid having to install anything on your local machine. To run it using Docker, first pull the `vcasellesb/stl2nii:v1` docker image (`docker image pull vcasellesb/stl2nii:v1`), and then run it like this:

```bash
docker container run --rm -v /path/to/reference.nii.gz:/ref/miau.nii.gz -v /path/to/stls/:/stl vcasellesb/stl2nii:v1
```

It is very important that you mount the reference file inside the docker container in a folder named '`/ref`', and the `.stl` files in a folder named '`/stl`', otherwise the code will fail. How you name the reference file inside the docker container is irrelevant (I've named it `miau.nii.gz`). The output `nifti` files will be available in the host at `/path/to/stls/nii/`.