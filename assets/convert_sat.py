# convert_sat.py

import Part
import sys

# Load the SAT file
input_file = "cnc.sat"
shape = Part.read(input_file)

# Export as STEP and STL
Part.export([shape], "cnc.step")
Part.export([shape], "cnc.stl")

print("Exported to cnc.step and cnc.stl")
