""" Splits a STL file into equal sized pieces along X,Y axis 
 and saves those pieces as individual segments for printing.
 I needed this  because both orca and cura failed to slice 
 my large model for 3d printing.  Generates files using 
 same file name as input with + "_splt-" + segmentNum

 Prereq:
  Linux:
    pip3 install trimesh numpy
    pip3 install manifold3d

  To Run: 
    Linux:
      python split-file.py inputFileName.stl
      python split-file.py --xsplit 4 --ysplit 6 testfile.stl

      depending on how you have python installed you may need
      to run using python3 instead of python.
      
 """
import numpy as np
import trimesh
import argparse
import os

def split_stl_into_grid(input_stl, xsplit=3, ysplit=3):
    """
    Splits an STL file into a grid of smaller STL files.

    Parameters:
        input_stl (str): Path to the input STL file.
        xsplit (int): Number of divisions along the X-axis.
        ysplit (int): Number of divisions along the Y-axis.
    """
    # Load the STL file
    mesh = trimesh.load(input_stl)
    if not isinstance(mesh, trimesh.Trimesh):
        raise ValueError("Failed to load STL as a valid 3D mesh")

    # Determine the output prefix
    output_prefix = os.path.splitext(input_stl)[0]  # Strip .stl extension

    # Get the bounding box
    bounds = mesh.bounds
    min_bound = bounds[0]
    max_bound = bounds[1]

    # Calculate extents
    x_extent = np.linspace(min_bound[0], max_bound[0], xsplit + 1)
    y_extent = np.linspace(min_bound[1], max_bound[1], ysplit + 1)
    z_min, z_max = min_bound[2], max_bound[2]

    # Split the mesh into grid cells
    part_number = 1
    for i in range(xsplit):
        for j in range(ysplit):
            # Define the bounding box for the current grid cell
            x_min, x_max = x_extent[i], x_extent[i + 1]
            y_min, y_max = y_extent[j], y_extent[j + 1]
            bounds_box = trimesh.creation.box(
                extents=(x_max - x_min, y_max - y_min, z_max - z_min),
                transform=trimesh.transformations.translation_matrix(
                    [(x_max + x_min) / 2, (y_max + y_min) / 2, (z_max + z_min) / 2]
                )
            )

            # Intersect the mesh with the bounding box
            section = mesh.intersection(bounds_box)

            # Save the section if it contains geometry
            if section.is_empty:
                continue
            output_filename = f"{output_prefix}_splt-{part_number:02d}.stl"
            section.export(output_filename)
            print(f"Saved: {output_filename}")
            part_number += 1


if __name__ == "__main__":
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Split an STL file into a grid of smaller STL files.")
    parser.add_argument("input_stl", help="Path to the input STL file")
    parser.add_argument("--xsplit", type=int, default=3, help="Number of divisions along the X-axis (default: 3)")
    parser.add_argument("--ysplit", type=int, default=3, help="Number of divisions along the Y-axis (default: 3)")

    args = parser.parse_args()

    # Run the splitting function
    split_stl_into_grid(args.input_stl, args.xsplit, args.ysplit)
