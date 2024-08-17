import os
from typing import List
import itk

def mesh_to_nii(mesh_path: str, 
                output_folder: str,
                reference_image_path: str,
                DIM: int=3) -> str:
    # sources:
    # https://discourse.itk.org/t/trianglemeshtobinaryimagefilter-in-python/1604
    # https://examples.itk.org/src/core/mesh/converttrianglemeshtobinaryimage/documentation

    assert mesh_path.endswith('.stl'), f"Only stl files permitted as input! Got '{mesh_path}'"

    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
        
    output_nii_path = os.path.join(output_folder, os.path.basename(mesh_path).replace('.stl', '.nii.gz'))

    MeshType = itk.Mesh[itk.UC, DIM]
    reader = itk.MeshFileReader[MeshType].New()

    meshIO = itk.STLMeshIO.New()
    reader.SetMeshIO(meshIO)
    reader.SetFileName(mesh_path)
    reader.Update()
    mesh = reader.GetOutput()

    UCType = itk.Image[itk.UC, DIM]
    ConverterType = itk.TriangleMeshToBinaryImageFilter[MeshType, UCType]
    filter = ConverterType.New()
    filter.SetInput(mesh)  # mesh is read from file
    
    # referenceImage is read from file or constructed by setting size, origin, and spacing
    referenceImage = itk.imread(reference_image_path)
    referenceImage = referenceImage.astype(itk.UC)
    filter.SetInfoImage(referenceImage)
    filter.Update()
    itk.imwrite(filter.GetOutput(), output_nii_path)

    return output_nii_path

def stltonii(stl_files_list: List[str], 
             nii_ref: str,
             output_folder: str=None) -> None:
    """
    Uses itk::TriangleMeshToBinaryImageFilter to convert the stls/meshes
    """
    
    default_output_folder = output_folder is None

    for stl_file in stl_files_list:
        
        if default_output_folder:
            output_folder = os.path.join(os.path.dirname(stl_file), 'nii')
        
        try:
            mesh_to_nii(
                mesh_path=stl_file,
                output_folder=output_folder,
                reference_image_path=nii_ref
            )
        except AssertionError as e:
            print(f'{e}. Skipping \'{stl_file}\'.')
    
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
    args = parser.parse_args()

    stltonii(stl_files_list=args.i, 
             nii_ref=args.ref, 
             output_folder=args.o)

if __name__ == "__main__":   
    run_stl2nii_entrypoint()