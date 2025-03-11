import numpy as np
import trimesh
import argparse
import os

def calculate_splits(model_size, max_size):
    """
    Calculate the number of splits required to fit the model within the maximum printer dimensions.

    Parameters:
        model_size (float): Size of the model along an axis.
        max_size (float): Maximum printable size along the same axis.

    Returns:
        int: Number of splits required.
    """
    if max_size is None or max_size <= 0:
        raise ValueError("Maximum size must be a positive number.")
    splits = np.ceil(model_size / max_size)
    return int(splits)

def create_dovetail(width, height, depth, angle):
    # Create a single dovetail shape
    points = [
        [0, 0, 0],
        [width, 0, 0],
        [width - np.tan(angle) * height, height, 0],
        [np.tan(angle) * height, height, 0]
    ]
    faces = [[0, 1, 2], [0, 2, 3]]
    dovetail = trimesh.Trimesh(vertices=points, faces=faces)
    dovetail = dovetail.extrude(depth)
    return dovetail

def add_dovetails(mesh, split_axis, num_splits, dovetail_params):
    bounds = mesh.bounds
    axis_length = bounds[1][split_axis] - bounds[0][split_axis]
    segment_length = axis_length / num_splits

    for i in range(1, num_splits):
        position = bounds[0][split_axis] + i * segment_length
        
        # Create male and female dovetails
        male_dovetail = create_dovetail(**dovetail_params)
        female_dovetail = male_dovetail.copy()
        female_dovetail.invert()

        # Position dovetails
        translation = [0, 0, 0]
        translation[split_axis] = position
        male_dovetail.apply_translation(translation)
        female_dovetail.apply_translation(translation)

        # Add dovetails to the mesh
        mesh = mesh.union(male_dovetail)
        mesh = mesh.difference(female_dovetail)

    return mesh



def split_stl_into_grid(input_stl, xsplit=None, ysplit=None, max_x=None, max_y=None, flip=False):
    """
    Splits an STL file into a grid of smaller STL files and prints their dimensions.

    Parameters:
        input_stl (str): Path to the input STL file.
        xsplit (int): Number of divisions along the X-axis.
        ysplit (int): Number of divisions along the Y-axis.
        max_x (float): Maximum printable dimension along the X-axis in mm.
        max_y (float): Maximum printable dimension along the Y-axis in mm.
        flip (bool): Whether to flip the STL model over the X-axis.
    """
    # Load the STL file
    mesh = trimesh.load(input_stl)
    if not isinstance(mesh, trimesh.Trimesh):
        raise ValueError("Failed to load STL as a valid 3D mesh")

    # Flip the mesh if specified
    if flip:
        # Apply a 180-degree rotation around the X-axis
        rotation_matrix = trimesh.transformations.rotation_matrix(np.pi, [1, 0, 0])
        mesh.apply_transform(rotation_matrix)

    # Get the bounding box dimensions
    bounds = mesh.bounds
    model_size_x = bounds[1][0] - bounds[0][0]
    model_size_y = bounds[1][1] - bounds[0][1]
    model_size_z = bounds[1][2] - bounds[0][2]

    # Print main part dimensions
    print(f"Main part dimensions (mm): X: {model_size_x:.2f}, Y: {model_size_y:.2f}, Z: {model_size_z:.2f}")
    
    # Determine the number of splits
    if xsplit is None:
        if max_x is not None:
            xsplit = calculate_splits(model_size_x, max_x)
        else:
            xsplit = 1  # Default to 1 if neither xsplit nor max_x is provided

    if ysplit is None:
        if max_y is not None:
            ysplit = calculate_splits(model_size_y, max_y)
        else:
            ysplit = 1  # Default to 1 if neither ysplit nor max_y is provided

    # Ensure at least one split
    xsplit = max(1, xsplit)
    ysplit = max(1, ysplit)

    # Calculate subdivision sizes
    segment_size_x = model_size_x / xsplit
    segment_size_y = model_size_y / ysplit

    # Print subdivision sizes
    print(f"Number of divisions: X: {xsplit}, Y: {ysplit}")
    print(f"Each segment size (mm): X: {segment_size_x:.2f}, Y: {segment_size_y:.2f}, Z: {model_size_z:.2f}")

    # Determine the output prefix
    output_prefix = os.path.splitext(input_stl)[0]  # Strip .stl extension

    # Calculate extents
    x_extent = np.linspace(bounds[0][0], bounds[1][0], xsplit + 1)
    y_extent = np.linspace(bounds[0][1], bounds[1][1], ysplit + 1)
    z_min, z_max = bounds[0][2], bounds[1][2]

    if dovetail:
        dovetail_params = {
        'width': 10,  # Adjust as needed
        'height': 5,  # Adjust as needed
        'depth': min(segment_size_x, segment_size_y) / 2,  # Half the smaller segment size
        'angle': np.radians(15)  # 15-degree angle
        }
        if xsplit > 1:
            mesh = add_dovetails(mesh, 0, xsplit, dovetail_params)
        if ysplit > 1:
            mesh = add_dovetails(mesh, 1, ysplit, dovetail_params)

    # Split the mesh into grid cells
    part_number = 1
    
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

            # Save the section to an STL file
            output_filename = f"{output_prefix}_splt-{part_number:02d}.stl"
            section.export(output_filename)
            print(f"Saved: {output_filename}")
            part_number += 1

if __name__ == "__main__":
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Split an STL file into a grid of smaller STL files.")
    parser.add_argument("input_stl", help="Path to the input STL file")
    parser.add_argument("--dovetail", action="store_true", help="Add symmetrical dovetail joints at each split")
    parser.add_argument("--xsplit", type=int, default=None, help="Number of divisions along the X-axis")
    parser.add_argument("--ysplit", type=int, default=None, help="Number of divisions along the Y-axis")
    parser.add_argument("--max-x", "-mx", type=float, default=None, help="Maximum printable dimension along the X-axis in mm")
    parser.add_argument("--max-y", "-my", type=float, default=None, help="Maximum printable dimension along the Y-axis in mm")
    parser.add_argument("--flip", action="store_true", help="Flip the STL model over the X-axis before splitting")

    args = parser.parse_args()

    # Run the splitting function
    split_stl_into_grid(
        input_stl=args.input_stl,
        xsplit=args.xsplit,
        ysplit=args.ysplit,
        max_x=args.max_x,
        max_y=args.max_y,
        flip=args.flip,
        dovetail=args.dovetail
    )
