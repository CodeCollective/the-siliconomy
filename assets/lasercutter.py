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
machine = SimpleNamespace(x=2400, y=1400, z=1100)
room = SimpleNamespace(x=8000, y=8000, z=4000)
wall_width = 1

aluminum_thickness = 4
material_thickness = 2 

ccrotation = trimesh.transformations.rotation_matrix(np.pi / 2, [0, 1, 0])
ccrotation1 = trimesh.transformations.rotation_matrix(np.pi / 2, [1, 0, 0])
ccrotation2 = trimesh.transformations.rotation_matrix(np.pi / 2, [0, 0, 1])

# Add metallic material
metallic_appearance = trimesh.visual.material.PBRMaterial(
    name="metal",
    baseColorFactor=[0.8/2, 0.8/2, 0.85/2, 1.0],  # Slightly bluish silver
    metallicFactor=0.5,
    roughnessFactor=0.1
)
metallic_texture = trimesh.visual.TextureVisuals(material=metallic_appearance)
# Apply the color to all faces
glass_material = trimesh.visual.material.PBRMaterial(
    baseColorFactor=[0.8, 0.9, 1.0, 0.3],  # RGBA
    metallicFactor=0.2,
    roughnessFactor=0.1,
    alphaMode="BLEND",
)

wall = box([room.y, room.x, wall_width])
floor = translate(wall, [0,room.y/2-machine.y/2,0])
floor.visual.material = glass_material
rightwall = translate(rotate(box([room.z, room.y, wall_width]), [0,90,0]), [-room.x/2, room.y/2-machine.y/2, room.z/2])
leftwall = translate(rotate(box([room.z, room.y, wall_width]), [0,270,0]), [room.x/2, room.y/2-machine.y/2, room.z/2])
rearwall = translate(rotate(box([room.z, room.x, wall_width]), [0,270,90]), [0, -machine.y/2, room.z/2])

#rotate(wall, [0,90,0])
components["floor"] = floor
components["rightwall"] = rightwall
components["leftwall"] = leftwall
components["rearwall"] = rearwall


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

enclosure_left.visual = metallic_texture

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
enclosure_front.visual = metallic_texture
rotate(enclosure_front, [90, 0, 0])

enclosure_rear = deepcopy(enclosure_front)
# Apply translation
translate(enclosure_front, [0, machine.y / 2, machine.z / 2])
translate(enclosure_rear, [0, -machine.y / 2, machine.z / 2])

door_front_left = box([machine.x / 2 - 50, machine.z - 100, aluminum_thickness])
add_texture_simple(door_front_left, "red.jpg")
rotate(door_front_left, [90, 0, 0])
door_front_right = deepcopy(door_front_left)
door_rear_left = deepcopy(door_front_left)
door_rear_right = deepcopy(door_front_left)
translate(door_front_left, [(machine.x - 100 + 6) / 4, machine.y / 2, machine.z / 2])
components["door_front_left"] = door_front_left
translate(door_front_right, [-(machine.x - 100 + 6) / 4, machine.y / 2, machine.z / 2])
components["door_front_right"] = door_front_right
translate(door_rear_left, [(machine.x - 100 + 6) / 4, -machine.y / 2, machine.z / 2])
components["door_rear_left"] = door_rear_left
translate(door_rear_right, [-(machine.x - 100 + 6) / 4, -machine.y / 2, machine.z / 2])
components["door_rear_right"] = door_rear_right

door3 = box([machine.y - 100, machine.z - 100, aluminum_thickness])
add_texture_simple(door3, "red.jpg")
rotate(door3, [90, 0, 90])
door4 = deepcopy(door3)
translate(door3, [(machine.x) / 2, 0, machine.z / 2])
components["door3"] = door3
translate(door4, [-(machine.x) / 2, 0, machine.z / 2])
components["door4"] = door4

components["enclosure_left"] = enclosure_left
components["enclosure_right"] = enclosure_right
components["enclosure_front"] = enclosure_front
components["enclosure_rear"] = enclosure_rear


def create_pull_handle(
    length=120, width=20, thickness=10, grip_radius=7, mount_thickness=4
):
    # Define a tapered side cover profile
    line = LineString(
        [
            (0, 0),
            (length * 1 / 6, 0),
            (length * 2 / 6, thickness),
            (length * 4 / 6, thickness),
            (length * 5 / 6, 0),
            (length, 0),
        ]
    )

    # Buffer the line to give it thickness (10 units tall)
    profile = line.buffer(grip_radius, cap_style="round")

    # Extrude the 2D profile along Z
    handle = trimesh.creation.extrude_polygon(profile, height=width)
    center(handle)

    handle.visual = metallic_texture

    return handle


# Create and position the handle on door_front_left
door_handle_left = create_pull_handle(length = machine.z / 6, width = machine.z/30, thickness=machine.z/50)
door_handle_cover = deepcopy(door_handle_left)
rotate(door_handle_left, [0, 90, 0])  # Orient horizontally
door_handle_right = deepcopy(door_handle_left) 
translate(
    door_handle_left,
    [
        90,
        machine.y / 2 + aluminum_thickness / 2 + 10,
        machine.z - 180,
    ],
) 
translate(
    door_handle_right,
    [
        -90,
        machine.y / 2 + aluminum_thickness / 2 + 10,
        machine.z - 180,
    ],
)

translate(
    door_handle_cover,
    [
        0,
        machine.y / 2 * 1.05 + aluminum_thickness / 2 ,
        machine.z * 1.12,
    ],
)

# Add to components
components["door_handle_left"] = door_handle_left
components["door_handle_right"] = door_handle_right
components["door_handle_cover"] = door_handle_cover

# Cutting components["bed"]
components["bed"] = box(
    extents=[machine.x, machine.y, 5],
    transform=trimesh.transformations.translation_matrix([0, 0, machine.z]),
)
add_texture(components["bed"], "aluminum.jpg")

components["laser_lens"] = cylinder(
    radius=5,
    height=5,
    transform=trimesh.transformations.translation_matrix([0, 0, machine.z + 10]),
)
add_texture(components["laser_lens"], "red.jpg")

# Side piece
sp_total_height = machine.z / 4
sp_bend_point = machine.z / 6
sp_width = machine.x / 10

# Define 2D profile as Shapely polygon
points = [
    [0, 0],
    [0, sp_total_height],
    [machine.y - sp_bend_point, sp_total_height],
    [machine.y, sp_bend_point],
    [machine.y, 0],
]
profile = Polygon(points)

# Extrude the 2D profile along the Z-axis
left_extension = trimesh.creation.extrude_polygon(profile, height=sp_width)
translate(left_extension, [-machine.y / 2, -sp_total_height / 2, -sp_width / 2])
rotate(left_extension, [90, 0, 90])

left_extension.visual = metallic_texture

right_extension = deepcopy(left_extension)
translate(
    left_extension, [machine.x / 2 - sp_width / 2, 0, machine.z + sp_total_height / 2]
)
components["left_extension"] = left_extension
translate(
    right_extension, [-machine.x / 2 + sp_width / 2, 0, machine.z + sp_total_height / 2]
)
components["right_extension"] = right_extension

rear_extension = box([machine.x, 20, sp_total_height])
rear_extension.visual = metallic_texture
translate(rear_extension, [0, -machine.y / 2 + 20 / 2, machine.z + sp_total_height / 2])
components["rear_extension"] = rear_extension

front_extension = box([machine.x - sp_width * 2, 20, sp_bend_point / 2])
front_extension.visual = metallic_texture
translate(front_extension, [0, machine.y / 2 - 20 / 2, machine.z + sp_bend_point / 4])
components["front_extension"] = front_extension


# Emergency Stop
emergency_stop = cylinder(
    radius=machine.x/70,
    height=40,
)
add_texture(emergency_stop, "red.jpg")
rotate(emergency_stop, [-45,0,0])
translate(emergency_stop, [-machine.x/2 + sp_width/2, machine.y/2-50, machine.z+sp_bend_point+45])
components["emergency_stop"] = emergency_stop

# Laser components
components["laser_body"] = cylinder(
    radius=15,
    height=40,
    transform=trimesh.transformations.translation_matrix([0, 0, machine.z + 10]),
)
add_texture(components["laser_body"], "steel.jpg")


# Define a tapered side cover profile
line = LineString(
    [
        (machine.y / 2 - sp_bend_point, sp_total_height),
        (machine.y / 2, sp_bend_point),
        (machine.y / 2, sp_bend_point / 2),
    ]
)

# Buffer the line to give it thickness (10 units tall)
profile = line.buffer(5, cap_style=2)

# Extrude the 2D profile along Z
cover_length = machine.x - sp_width * 2
cover_overhang_part = trimesh.creation.extrude_polygon(profile, height=cover_length)

# Apply transformations: center, orient, and position
cover_overhang_part.apply_translation([0, 0, -(cover_length) / 2])
rotate(cover_overhang_part, [90, 0, 90])
cover_overhang_part.apply_translation([0, 0, machine.z])

# Add texture and assign to components
add_texture(cover_overhang_part, "red.jpg")

cover_overhang = machine.y - sp_bend_point
cover_top = create_rect_with_hole(
    width=cover_length, height=cover_overhang, top=50, bottom=50, left=50, right=50
)
add_texture(cover_top, "red.jpg")
translate(cover_top, [0, -(machine.y - cover_overhang) / 2, machine.z + sp_total_height])

cover_glass = center(box([cover_length - 100, cover_overhang - 100, 10]))
translate(cover_glass, [0, -50, machine.z + sp_total_height])
# Define the glass material
# Set a translucent light blue RGBA color (R, G, B, A)
rgba = [200, 220, 255, 10]  # A = 30/255 ≈ ~12% opacity (mostly transparent)

cover_glass.visual.material = glass_material

# Create a group scene for cover and glass
cover_group = trimesh.Scene()
cover_group.add_geometry(cover_overhang_part, node_name="cover_overhang_part")
cover_group.add_geometry(cover_top, node_name="cover_top")
cover_group.add_geometry(cover_glass, node_name="cover_glass")
cover_group.metadata = {
    "pivot_point": [0, -machine.y/2 + 20/2, machine.z + sp_total_height],  # Your hinge location
    "rotation_axis": "x"  # Or "y"/"z" depending on hinge orientation
}
# Add to components
components["cover_group"] = cover_group


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
exhaust_radius = machine.y / 15
exhaust = trimesh.creation.capsule(height=machine.z*0.9, radius=exhaust_radius)
add_texture(exhaust, "cable.jpg")
translate(exhaust, [machine.x / 2 + 10, 0, machine.y / 2])
cables.append(exhaust)

# Logo
#logo_mesh = create_text_mesh_custom_font("Code Collective", font_size=50)
#logo_mesh.apply_transform(ccrotation)
#logo_mesh.apply_transform(ccrotation1)
#logo_mesh.apply_transform(ccrotation2)
#logo_mesh.apply_translation([-50, machine.z / 2 + 1, machine.y / 2 - 30])
#add_texture(logo_mesh, "logo.png")

# Load and position crate model
crate = rotate(center(trimesh.load(os.path.join(here, "Crate.glb"))), [90,0,180])
# Scale to 1000 units tall (Z axis)
box_height = 1200
current_height = crate.bounds[1][2] - crate.bounds[0][2]
scale_factor = box_height / current_height
crate.apply_scale([scale_factor*2, scale_factor*2, scale_factor])
# Position to left of laser cutter
translate(crate, [room.x/2 + crate.bounds[0][1], room.y/2, box_height/2])
components["crate"] = crate


# Create a silicon wafer-style disk with a flat edge
wafer_radius = 250  # 500 mm diameter
wafer_thickness = 0.775  # Typical silicon wafer thickness in mm
flat_width = 30  # Width of the flat cut, adjust as needed
# Create full round wafer
wafer_disk = cylinder(radius=wafer_radius, height=wafer_thickness, sections=128)
# Create box to subtract for the flat
flat_box = box([flat_width, wafer_radius * 2 + 10, wafer_thickness + 1])
flat_box.apply_translation([wafer_radius - flat_width / 2, 0, 0])  # Position box on one edge
# Subtract the flat
wafer_with_flat = difference([wafer_disk, flat_box])
# Set metallic/silicon-like material (dark gray, slightly shiny)
silicon_material = trimesh.visual.material.PBRMaterial(
    baseColorFactor=[0.2, 0.2, 0.2, 1.0],
    metallicFactor=0.1,
    roughnessFactor=0.2,
)
wafer_with_flat.visual.material = silicon_material
# Position the wafer somewhere visible in the scene
translate(wafer_with_flat, [room.x/2-box_height/2, room.y/2, box_height])
# Add to components
components["wafer"] = wafer_with_flat


# Combine honeycomb_list, buttons, vents, and cables
#components["honeycomb_mesh"] = generateHoneycomb(machine)
#translate(components["honeycomb_mesh"], [0, 0, machine.z + aluminum_thickness])
#add_texture(components["honeycomb_mesh"], "aluminum.jpg")

components["vents_mesh"] = trimesh.util.concatenate(vents)
components["cables_mesh"] = trimesh.util.concatenate(cables)

# Apply rotation to orient the machine
rotation = trimesh.transformations.rotation_matrix(-np.pi / 2, [1, 0, 0])

# Apply transformations to all components
for name, component in components.items():
    if component is not None:
        translate(component, [0,machine.y/2,0])
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
