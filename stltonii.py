import vtk
import sys
import nibabel as nib
import numpy as np
import os

def stltovtk(input_stl: str) -> str:
    """Python function that uses vtk to convert a stl file to a vtk file
    Returns: path to vtk file"""
    assert input_stl.endswith('.stl'), 'stl file is expected!'

    reader = vtk.vtkSTLReader()
    reader.SetFileName(input_stl)
    reader.Update()
    stl = reader.GetOutput()

    writer = vtk.vtkPolyDataWriter()
    outfilename = input_stl.replace('.stl', '.vtk')
    writer.SetFileName(outfilename)
    writer.SetInputData(stl)
    writer.Update()

    return outfilename

def vtktonii(input_vtk:str, ref:str, addheader: bool = True) -> str:

    # import vtk image
    reader = vtk.vtkPolyDataReader()
    reader.SetFileName(input_vtk)
    reader.ReadAllVectorsOn()
    reader.ReadAllScalarsOn()
    reader.Update()

    polydata = reader.GetOutput()

    # read reference volume nii file
    refnii = nib.load(ref)
    refnii_data = refnii.get_fdata()
    refnii_afine = refnii.affine
    x_dim, y_dim, z_dim = refnii_data.shape
    sx, sy, sz = abs(refnii_afine[0,0]), abs(refnii_afine[1,1]), abs(refnii_afine[2,2])
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
    outfilename = input_vtk.replace('.vtk', '.nii.gz')
    writer.SetFileName(outfilename)
    writer.SetInputConnection(imgstenc.GetOutputPort())
    writer.Write()

    if addheader:
        assert (refnii is not None and ref.endswith(".nii.gz")), "Please provide valid reference nifti file"
        label = nib.load(outfilename)
        label_array = label.get_fdata()
        niipostproc = addrefheader(label_array, refnii_afine)
        nib.save(niipostproc, outfilename)

    return outfilename

def addrefheader(label_array: np.ndarray, refnii_affine: np.ndarray):
    label_array = rotstl(label_array)
    label_array = label_array.astype(np.uint8)
    niipostproc = nib.Nifti1Image(label_array, refnii_affine)
    return niipostproc


def stltonii(stl, nii_ref):
    transformed_to_vtk = stltovtk(stl)
    if nii_ref is not None:
        refheader = True
    else:
        refheader = False
    nii_file_final = vtktonii(transformed_to_vtk, ref = nii_ref, addheader=refheader)
    os.remove(transformed_to_vtk)
    return nii_file_final

def rotstl(data_array: np.ndarray) -> np.ndarray:
    label_array = np.flip(data_array, 1)
    return label_array
    

if __name__ == "__main__":
    stltonii(sys.argv[1], sys.argv[2])