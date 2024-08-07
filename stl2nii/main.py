import vtk
import SimpleITK as sitk
from typing import List
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

def vtktonii(input_vtk:str, 
             ref: str, 
             output_folder: str,
             weird_behavior: bool = False) -> str:
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
    refnii = sitk.ReadImage(ref)
    refnii_ndarray = sitk.GetArrayFromImage(refnii)
    ref_dims = refnii_ndarray.shape[::-1] # flip to match image (maybe should be changed per use case?)
    ref_spacing = refnii.GetSpacing()
    ref_origin = (0, 0, 0) if weird_behavior else refnii.GetOrigin()
    ref_direction = refnii.GetDirection()
    
    image = vtk.vtkImageData()
    image.SetSpacing(ref_spacing)
    image.SetDimensions(ref_dims)
    image.SetOrigin(ref_origin)
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
    pol2stenc.SetOutputOrigin(ref_origin)
    pol2stenc.SetOutputSpacing(ref_spacing)
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

    if weird_behavior:
        label = sitk.ReadImage(outfilename)
        label_array = sitk.GetArrayFromImage(label)
        assert np.sum(label_array>0) != 0, "Empty mask. Please report this issue (in case it's not supposed to be empty) \
            at https://github.com/vcasellesb/stl2nii/issues"
    
        # this is hardcoded. I've found that it's necessary in the stl files I've encountered. Please consider if it works in your case
        label_array = rotate_stl(label_array)
        
        niipostproc = sitk.GetImageFromArray(label_array)
        niipostproc.SetDirection(ref_direction)
        niipostproc.SetOrigin(refnii.GetOrigin())
        niipostproc.SetSpacing(ref_spacing)
        sitk.WriteImage(niipostproc, outfilename)

    return outfilename

def stltonii(stl_files_list: List[str], 
             nii_ref: str,
             output_folder: str=None,
             weird_behavior: bool=False):
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
                                  weird_behavior=weird_behavior)
        
        os.remove(transformed_to_vtk)
    return nii_file_final

def rotate_stl(data_array: np.ndarray) -> np.ndarray:
    """
    Hardcoded. Requires trial and error.
    """
    label_array = np.flip(data_array, 1)
    return label_array
    
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
    parser.add_argument('--weird_behavior', required=False, action='store_true',
                        help='Set this if you want to activate the weird behavior that is discussed in issue #3 '
                        'This is just to match the "developer"\'s (vicentcaselles) use case')
    args = parser.parse_args()

    stltonii(stl_files_list=args.i, 
             nii_ref=args.ref, 
             output_folder=args.o,     
             weird_behavior=args.weird_behavior)

if __name__ == "__main__":   
    run_stl2nii_entrypoint()