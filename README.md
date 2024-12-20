# STL Splitter: Divide STL Files into Equal Segments for Printing

This tool splits an STL file into equal-sized pieces along the X and Y axes, saving those pieces as individual segments for easier 3D printing. It’s designed to be faster and simpler than splitting models in slicers.
```
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
```
