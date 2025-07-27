import numpy as np

import trimesh
from trimesh.creation import cylinder, box, icosphere
from trimesh.boolean import difference
from trimesh.transformations import translation_matrix
from shapely.geometry import LineString

from copy import deepcopy

# NOTE: Trimesh uses a right-handed coordinate system by default:
# X: right
# Y: forward (into the screen)
# Z: up

from types import SimpleNamespace

import os
from util import *
from PIL import Image

here = os.path.dirname(os.path.abspath(__file__))

components = {}
machine = SimpleNamespace(x=1000, y=600, z=500)
aluminum_thickness = 4
material_thickness = 2

ccrotation = trimesh.transformations.rotation_matrix(np.pi / 2, [0, 1, 0])
ccrotation1 = trimesh.transformations.rotation_matrix(np.pi / 2, [1, 0, 0])
ccrotation2 = trimesh.transformations.rotation_matrix(np.pi / 2, [0, 0, 1])

# enclosure = difference([main_box, cutout_box])
# Create the left enclosure
# Want a vertical rectangle on YZ plane, thickness in X
enclosure_left = create_rect_with_hole(
    width=machine.z,  # along Y
    height=machine.y,  # along Z
    top=50,
    bottom=50,
    left=50,
    right=50,
    extrusion_height=aluminum_thickness,  # thickness goes into X direction after rotation
)
rotate(enclosure_left, [0, 90, 0])
# Create the right enclosure
enclosure_right = deepcopy(enclosure_left)
# Apply translation
enclosure_left.apply_transform(
    translation_matrix([machine.x / 2 - aluminum_thickness / 2, 0, machine.z / 2])
)
# Apply translation
enclosure_right.apply_transform(
    translation_matrix([-machine.x / 2 + aluminum_thickness / 2, 0, machine.z / 2])
)

# Create the front enclosure
enclosure_front = create_rect_with_hole(
    machine.x, machine.z, 50, 50, 50, 50, plane="xz"
)
rotate(enclosure_front, [90, 0, 0])
enclosure_rear = deepcopy(enclosure_front)
# Apply translation
translate(enclosure_front, [0, machine.y / 2, machine.z / 2])
translate(enclosure_rear, [0, -machine.y / 2, machine.z / 2])

door1 = box([machine.x / 2 - 50, machine.z - 100, aluminum_thickness])
add_texture_simple(door1, "red.jpg")
rotate(door1, [90, 0, 0])
door2 = deepcopy(door1)
door5 = deepcopy(door1)
door6 = deepcopy(door1)
translate(door1, [(machine.x - 100 + 6) / 4, machine.y / 2, machine.z / 2])
components["door1"] = door1
translate(door2, [-(machine.x - 100 + 6) / 4, machine.y / 2, machine.z / 2])
components["door2"] = door2
translate(door5, [(machine.x - 100 + 6) / 4, -machine.y / 2, machine.z / 2])
components["door5"] = door5
translate(door6, [-(machine.x - 100 + 6) / 4, -machine.y / 2, machine.z / 2])
components["door6"] = door6

door3 = box([machine.y - 100, machine.z - 100, aluminum_thickness])
add_texture_simple(door3, "red.jpg")
rotate(door3, [90, 0, 90])
door4 = deepcopy(door3)
translate(door3, [(machine.x) / 2, 0, machine.z / 2])
components["door3"] = door3
translate(door4, [-(machine.x) / 2, 0, machine.z / 2])
components["door4"] = door4

add_texture_simple(enclosure_left, "aluminum.jpg")
add_texture_simple(enclosure_right, "aluminum.jpg")
add_texture_simple(enclosure_front, "aluminum.jpg")
add_texture_simple(enclosure_rear, "aluminum.jpg")
components["enclosure_left"] = enclosure_left
components["enclosure_right"] = enclosure_right
components["enclosure_front"] = enclosure_front
components["enclosure_rear"] = enclosure_rear

# Cutting components["bed"]
components["bed"] = box(
    extents=[machine.x, machine.y, 5],
    transform=trimesh.transformations.translation_matrix([0, 0, machine.z]),
)
add_texture(components["bed"], "aluminum.jpg")

# Laser components
components["laser_body"] = cylinder(
    radius=15,
    height=40,
    transform=trimesh.transformations.translation_matrix([0, 0, machine.z + 10]),
)
add_texture(components["laser_body"], "steel.jpg")

components["laser_lens"] = cylinder(
    radius=5,
    height=5,
    transform=trimesh.transformations.translation_matrix([0, 0, machine.z + 10]),
)
add_texture(components["laser_lens"], "red.jpg")

# Side piece
sp_total_height = 200
sp_bend_point = 100
sp_width = 60

# Define 2D profile as Shapely polygon
points = [
    [0, 0],
    [0, sp_total_height],
    [machine.y - sp_bend_point, sp_total_height],
    [machine.y, sp_bend_point],
    [machine.y, 0]
]
profile = Polygon(points)

# Extrude the 2D profile along the Z-axis
left_extension = trimesh.creation.extrude_polygon(profile, height=sp_width)
translate(left_extension, [-machine.y/2, -sp_total_height/2, -sp_width/2])
rotate(left_extension, [90,0,90])
add_texture(left_extension, "metal.jpg")
right_extension = deepcopy(left_extension)
translate(left_extension, [machine.x/2-sp_width/2,0,machine.z+sp_total_height/2])
components["left_extension"] = left_extension
translate(right_extension, [-machine.x/2+sp_width/2,0,machine.z+sp_total_height/2])
components["right_extension"] = right_extension

rear_extension = box([machine.x, 20, sp_total_height])
add_texture(rear_extension, "metal.jpg")
translate(rear_extension, [0, -machine.y/2+20/2, machine.z+sp_total_height/2])
components["rear_extension"] = rear_extension

front_extension = box([machine.x-sp_width*2, 20, sp_bend_point/2])
add_texture(front_extension, "metal.jpg")
translate(front_extension, [0, machine.y/2-20/2, machine.z+sp_bend_point/4])
components["front_extension"] = front_extension


# Define a tapered side cover profile
line = LineString([
    (machine.y / 2 - sp_bend_point, sp_total_height),
    (machine.y / 2, sp_bend_point),
    (machine.y / 2, sp_bend_point/2)
])

# Buffer the line to give it thickness (10 units tall)
profile = line.buffer(5, cap_style=2)

# Extrude the 2D profile along Z
cover_length = machine.x - sp_width * 2
cover = trimesh.creation.extrude_polygon(profile, height=cover_length)

# Apply transformations: center, orient, and position
cover.apply_translation([0, 0, -(cover_length) / 2])
rotate(cover,[90,0,90])
cover.apply_translation([0, 0, machine.z])

# Add texture and assign to components
add_texture(cover, "red.jpg")

cover2_y = machine.y-sp_bend_point
cover2 = create_rect_with_hole(width = cover_length, 
                               height = cover2_y,
                               top=50,
                               bottom=50,
                               left=50,
                               right=50
                               )
add_texture(cover2, "red.jpg")
translate(cover2, [0,-(machine.y-cover2_y)/2,machine.z + sp_total_height])
components["cover"] = trimesh.util.concatenate([cover, cover2])

glass_top = center(box([cover_length - 100, cover2_y - 100, 10]))
translate(glass_top, [0,-50,machine.z + sp_total_height])
# Define the glass material
# Set a translucent light blue RGBA color (R, G, B, A)
rgba = [200, 220, 255, 10]  # A = 30/255 ≈ ~12% opacity (mostly transparent)
# Apply the color to all faces
glass_material = trimesh.visual.material.PBRMaterial(
    baseColorFactor=[0.8, 0.9, 1.0, 0.3],  # RGBA
    metallicFactor=0.2,
    roughnessFactor=0.1,
    alphaMode="BLEND"
)
glass_top.visual.material = glass_material
components["glass_top"] = glass_top

# Make it "10 tall" — buffer gives width to the line (extends perpendicular)
# buffer(5) makes total height 10 units (5 above and below)
profile = line.buffer(5, cap_style=2)  # cap_style=2 for flat ends


rail_lift = 40
# Rails
# Create a cylindrical rail
radius = 10  # half of the box width for a similar size
cover_length = machine.x  # length of the rail

components["x_rail"] = trimesh.creation.cylinder(
    radius=radius,
    height=cover_length,
    sections=64,  # increase for smoother appearance
)

rotate(components["x_rail"], [0, 90, 0])
# Apply transform to lift and center it along the X-axis
translate(components["x_rail"], [0, 0, machine.z + rail_lift])

# Ventilation
vents = []
for i in range(8):
    vent = box(
        extents=[80, material_thickness, 5],
        transform=trimesh.transformations.translation_matrix(
            [-machine.x / 2 + 50 + i * 10, -machine.z / 2, machine.y / 2 - 50]
        ),
    )
    vents.append(vent)

# Cables
cables = []
exhaust_radius = 40
exhaust = trimesh.creation.capsule(height=machine.y, radius=exhaust_radius)
add_texture(exhaust, "cable.jpg")
translate(exhaust, [machine.x / 2 + 10, 0, machine.y / 2])
cables.append(exhaust)

# Logo
logo_mesh = create_text_mesh_custom_font("Code Collective", font_size=50)
logo_mesh.apply_transform(ccrotation)
logo_mesh.apply_transform(ccrotation1)
logo_mesh.apply_transform(ccrotation2)
logo_mesh.apply_translation([-50, machine.z / 2 + 1, machine.y / 2 - 30])
add_texture(logo_mesh, "logo.png")

# Apply rotation to orient the machine
rotation = trimesh.transformations.rotation_matrix(-np.pi / 2, [1, 0, 0])

# Combine honeycomb_list, buttons, vents, and cables
components["honeycomb_mesh"] = generateHoneycomb(machine)
translate(components["honeycomb_mesh"], [0, 0, machine.z + aluminum_thickness])
add_texture(components["honeycomb_mesh"], "aluminum.jpg")

components["vents_mesh"] = trimesh.util.concatenate(vents)
components["cables_mesh"] = trimesh.util.concatenate(cables)

# Apply transformations to all components
for name, component in components.items():
    if component is not None:
        component.apply_transform(rotation)

# Create scene
scene = trimesh.Scene(components.values())
scene.bg_color = [0.9, 0.9, 0.9, 1.0]

"""Export the model to GLB format"""
export_path = os.path.join(here, "laser_cutter.glb")
new_scene = trimesh.Scene()

for name, mesh in components.items():
    print(f"Processing {name}")
    new_scene.add_geometry(mesh, node_name=name, geom_name=name)
    mesh.metadata["name"] = name

new_scene.bg_color = scene.bg_color

new_scene.export(export_path)
