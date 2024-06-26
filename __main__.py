import vtk
from typing import List
import nibabel as nib
import numpy as np
import os
from vtkmodules.util.numpy_support import vtk_to_numpy

def stltovtk(input_stl: str, output_folder: str) -> str:
    """
    Stl to vtk conversion.
    Returns: path to vtk file
    """
    assert input_stl.endswith('.stl'), f'stl file is expected! Got {input_stl[-3:]} instead.'

    if not os.path.exists(output_folder):
        os.makedirs(output_folder, exist_ok=True)

    reader = vtk.vtkSTLReader()
    reader.SetFileName(input_stl)
    reader.Update()
    stl = reader.GetOutput()

    writer = vtk.vtkPolyDataWriter()
    outfilename = os.path.join(output_folder, os.path.basename(input_stl.replace('.stl', '.vtk')))
    writer.SetFileName(outfilename)
    writer.SetInputData(stl)
    writer.Update()

    return outfilename

def vtktonii(input_vtk:str, ref:str, output_folder: str, dtype) -> str:
    """
    Vtk to nii conversion
    """

    # import vtk image
    reader = vtk.vtkPolyDataReader()
    reader.SetFileName(input_vtk)
    reader.ReadAllVectorsOn()
    reader.ReadAllScalarsOn()
    reader.Update()

    polydata = reader.GetOutput()

    # read reference volume nii file
    refnii: nib.Nifti1Image = nib.load(ref)
    refnii_ndarray, refnii_affine = refnii.get_fdata(), refnii.affine
    x_dim, y_dim, z_dim = refnii_ndarray.shape
    sx, sy, sz = abs(refnii_affine[0,0]), abs(refnii_affine[1,1]), abs(refnii_affine[2,2])
    ox, oy, oz = (0, 0, 0)

    image = vtk.vtkImageData()
    image.SetSpacing(sx, sy, sz)
    image.SetDimensions(x_dim, y_dim, z_dim)
    image.SetOrigin(ox, oy, oz)
    image.AllocateScalars(vtk.VTK_UNSIGNED_CHAR, 1)

    inval = 1
    outval = 0
    
    # https://github.com/vcasellesb/stl2nii/issues/2
    scalars = image.GetPointData().GetScalars()
    scalar_array = vtk_to_numpy(scalars)
    scalar_array[:] = inval

    scalars.Modified()

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
    outfilename = os.path.join(output_folder, os.path.basename(input_vtk.replace('.vtk', '.nii.gz')))
    writer.SetFileName(outfilename)
    writer.SetInputConnection(imgstenc.GetOutputPort())
    writer.Write()

    assert (refnii is not None and ref.endswith((".nii.gz", ".nii"))), "Please provide valid reference nifti file"
    label: nib.Nifti1Image = nib.load(outfilename)
    label_array = label.get_fdata().astype(dtype)
   
   # this is hardcoded. I've found that it's necessary in the stl files I've encountered. Please consider if it works in your case
    label_array = rotatestl(label_array)
    
    niipostproc = nib.Nifti1Image(label_array, refnii_affine)
    nib.save(niipostproc, outfilename)

    return outfilename

def stltonii(stl_files_list: List[str], 
             nii_ref: str, 
             dtype,
             output_folder: str = None):
    """
    Main function. Basically iterates through input and performs confersion in two steps:
        stl -> vtk -> nii
    """
    for stl_file in stl_files_list:
        
        if output_folder is None:
            output_folder = os.path.join(os.path.dirname(stl_file), 'nii') 
        transformed_to_vtk = stltovtk(stl_file, output_folder=output_folder)
        
        nii_file_final = vtktonii(transformed_to_vtk, ref = nii_ref, 
                                  output_folder=output_folder, 
                                  dtype=dtype)
        
        os.remove(transformed_to_vtk)
    return nii_file_final

def rotatestl(data_array: np.ndarray) -> np.ndarray:
    """
    Hardcoded. Requires trial and error.
    """
    label_array = np.flip(data_array, 1)
    return label_array

def parsedtype(dtype):
    """
    Dumb albeit self-explanatory
    """
    if dtype == 'UINT16':
        return np.uint16
    elif dtype == 'UINT32':
        return np.uint32
    elif dtype == 'UINT64':
        return np.uint64
    
def run_stl2nii_entrypoint():
    import argparse

    parser = argparse.ArgumentParser(prog='stl2nii', 
                                     description="stl to NIFTI (.nii.gz) file converter")
    parser.add_argument('-i', nargs='+', type=str, required=True, 
                        help='Input files. Can be one or more.')
    parser.add_argument('-ref', type=str, required=True, 
                        help='Reference NIFTI for computing image properties (i.e. spacing, ...)')
    parser.add_argument('-o', type=str, required=False, default=None, 
                        help='Folder were output will be written (default: input_dir/nii)')
    parser.add_argument('-dtype', required=False, default=np.uint8,
                        choices=['UINT8', 'UINT16', 'UINT32', 'UINT64'],
                        help = 'Data type for the resulting NIFTI label (voxel values).')
    args = parser.parse_args()

    if isinstance(args.dtype, str):
        args.dtype = parsedtype(args.dtype)

    stltonii(args.i, args.ref, output_folder=args.o, dtype=args.dtype)

if __name__ == "__main__":   
    run_stl2nii_entrypoint()