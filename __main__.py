import vtk
from typing import List
import nibabel as nib
import numpy as np
import os
from batchgenerators.utilities.file_and_folder_operations import join

def stltovtk(input_stl: str, output_folder: str) -> str:
    """Python function that uses vtk to convert a stl file to a vtk file
    Returns: path to vtk file"""

    if not os.path.exists(output_folder):
        os.makedirs(output_folder, exist_ok=True)
    assert input_stl.endswith('.stl'), f'stl file is expected! Got {input_stl[:3]} instead.'

    reader = vtk.vtkSTLReader()
    reader.SetFileName(input_stl)
    reader.Update()
    stl = reader.GetOutput()

    writer = vtk.vtkPolyDataWriter()
    outfilename = join(output_folder, os.path.basename(input_stl.replace('.stl', '.vtk')))
    writer.SetFileName(outfilename)
    writer.SetInputData(stl)
    writer.Update()

    return outfilename

def vtktonii(input_vtk:str, ref:str, output_folder: str) -> str:

    # import vtk image
    reader = vtk.vtkPolyDataReader()
    reader.SetFileName(input_vtk)
    reader.ReadAllVectorsOn()
    reader.ReadAllScalarsOn()
    reader.Update()

    polydata = reader.GetOutput()

    # read reference volume nii file
    refnii = nib.load(ref)
    refnii_data, refnii_affine = refnii.get_fdata(), refnii.affine
    x_dim, y_dim, z_dim = refnii_data.shape
    sx, sy, sz = abs(refnii_affine[0,0]), abs(refnii_affine[1,1]), abs(refnii_affine[2,2])
    ox, oy, oz = (0, 0, 0)

    image = vtk.vtkImageData()
    image.SetSpacing(sx, sy, sz)
    image.SetDimensions(x_dim, y_dim, z_dim)
    image.SetOrigin(ox, oy, oz)
    image.AllocateScalars(vtk.VTK_UNSIGNED_CHAR, 1)

    inval = 1
    outval = 0
    for i in range(image.GetNumberOfPoints()):
        image.GetPointData().GetScalars().SetTuple1(i, inval)

    pol2stenc = vtk.vtkPolyDataToImageStencil()
    pol2stenc.SetInputData(polydata)
    pol2stenc.SetOutputOrigin((ox, oy, oz))
    pol2stenc.SetOutputSpacing((sx, sy, sz))
    pol2stenc.SetOutputWholeExtent(image.GetExtent())
    pol2stenc.Update()

    imgstenc = vtk.vtkImageStencil()
    imgstenc.SetInputData(image)
    imgstenc.SetStencilConnection(pol2stenc.GetOutputPort())
    imgstenc.ReverseStencilOff()
    imgstenc.SetBackgroundValue(outval)
    imgstenc.Update()

    writer = vtk.vtkNIFTIImageWriter()
    outfilename = join(output_folder, os.path.basename(input_vtk.replace('.vtk', '.nii.gz')))
    writer.SetFileName(outfilename)
    writer.SetInputConnection(imgstenc.GetOutputPort())
    writer.Write()

    assert (refnii is not None and ref.endswith((".nii.gz", ".nii"))), "Please provide valid reference nifti file"
    label = nib.load(outfilename)
    label_array = label.get_fdata()
    niipostproc = addrefheader(label_array, refnii_affine)
    nib.save(niipostproc, outfilename)

    return outfilename

def addrefheader(label_array: np.ndarray, refnii_affine: np.ndarray):
    label_array = rotstl(label_array)
    label_array = label_array.astype(np.uint8)
    niipostproc = nib.Nifti1Image(label_array, refnii_affine)
    return niipostproc


def stltonii(stl_files_list: List[str], nii_ref: str, output_folder: str):
    for stl_file in stl_files_list:
        transformed_to_vtk = stltovtk(stl_file, output_folder=output_folder)
        nii_file_final = vtktonii(transformed_to_vtk, ref = nii_ref, output_folder=output_folder)
        os.remove(transformed_to_vtk)
    return nii_file_final

def rotstl(data_array: np.ndarray) -> np.ndarray:
    label_array = np.flip(data_array, 1)
    return label_array

def run_stl2nii_entrypoint():

    import argparse
    parser = argparse.ArgumentParser(prog='stl2nii', 
                                     description="Stl to NIFTI (.nii.gz) file converter")
    parser.add_argument('-i', nargs='+', type=str, 
                        required=True, help='Input files. Can be one or more.')
    parser.add_argument('-ref', type=str, required=True, help='Reference NIFTI for computing image properties (i.e. spacing, ...)')
    parser.add_argument('-o', type=str, required=False, default='nii', 
                        help='Folder were output will be written (default: nii)')
    args = parser.parse_args()
    stltonii(args.i, args.ref, args.o)

if __name__ == "__main__":
    # import sys
    # i = sys.argv[1]
    # i = nib.load(i).affine
    # print(i)
    # exit(0)
    
    run_stl2nii_entrypoint()

