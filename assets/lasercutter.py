import numpy as np
import trimesh
from trimesh.creation import cylinder, box, icosphere
from trimesh.boolean import difference
from trimesh.transformations import translation_matrix

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
    center_planes="xy",
    plane="yz",  # this means we rotate the XY polygon to YZ
    extrusion_height=aluminum_thickness,  # thickness goes into X direction after rotation
)
# Create the right enclosure
enclosure_right = enclosure_left.copy()
# Apply translation
enclosure_left.apply_transform(
    translation_matrix([machine.x / 2 - aluminum_thickness / 2, 0, 0])
)
# Apply translation
enclosure_right.apply_transform(
    translation_matrix([-machine.x / 2 + aluminum_thickness / 2, 0, 0])
)

# Create the front enclosure
enclosure_front = create_rect_with_hole(
    machine.x, machine.z, 50, 50, 50, 50, plane="xz"
)
# Apply translation
enclosure_front.apply_transform(translation_matrix([0, machine.y / 2, 0]))

add_texture_simple(enclosure_left, "aluminum.jpg")
add_texture_simple(enclosure_right, "aluminum.jpg")
add_texture_simple(enclosure_front, "aluminum.jpg")
components["enclosure_left"] = enclosure_left
components["enclosure_right"] = enclosure_right
components["enclosure_front"] = enclosure_front

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
    transform=trimesh.transformations.translation_matrix([0, 0, machine.z]),
)
add_texture(components["laser_body"], "steel.jpg")

components["laser_lens"] = cylinder(
    radius=8,
    height=5,
    transform=trimesh.transformations.translation_matrix([0, 0, machine.z + 10]),
)
add_texture(components["laser_lens"], "lens.png")

# Rails
components["x_rail"] = box(
    extents=[machine.x, 20, 20],
    transform=trimesh.transformations.translation_matrix([0, 0, machine.y / 2 + 60]),
)
add_texture(components["x_rail"], "rail.jpg")

components["y_rail"] = box(
    extents=[20, machine.z, 20],
    transform=trimesh.transformations.translation_matrix([0, 0, machine.y / 2 + 60]),
)
add_texture(components["y_rail"], "rail.jpg")

# Belt pulley
components["belt_pulley"] = cylinder(
    radius=5,
    height=15,
    transform=trimesh.transformations.translation_matrix(
        [machine.x / 2 - 40, machine.z / 2 - 40, machine.y / 2 + 60]
    ),
)

# Control components["control_panel"]
cp_center = [-machine.x / 2, machine.y / 2, machine.z / 2 - 100]
components["control_panel"] = box(extents=[150, material_thickness, 80])
components["control_panel"].apply_translation(cp_center)
add_texture(components["control_panel"], "panel.jpg")

# Control buttons
buttons = []
button_count = 5
for i in range(button_count):
    button = cylinder(
        radius=5,
        height=30,
    )
    button.apply_transform(ccrotation1)
    button.apply_translation(cp_center)
    button.apply_translation([i * 15 - 15 * (button_count / 2.0), 0, 0])
    add_texture(button, "red.jpg")
    buttons.append(button)

# Display
components["display"] = box(
    extents=[60, 2, 30],
)
components["display"].apply_translation(cp_center)
components["display"].apply_translation([0, 0, -1])
add_texture(components["display"], "lcd.png")

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
for i in range(3):
    cable = trimesh.creation.capsule(
        height=machine.y,
        radius=8,
        transform=trimesh.transformations.translation_matrix(
            [machine.x / 2 + 10, machine.z / 2 - 80 - i * 20, 0]
        ),
    )
    add_texture(cable, "cable.jpg")
    cables.append(cable)

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
components["buttons_mesh"] = trimesh.util.concatenate(buttons)
components["vents_mesh"] = trimesh.util.concatenate(vents)
components["cables_mesh"] = trimesh.util.concatenate(cables)

# Apply transformations to all components
for name, component in components.items():
    if component is not None:
        component.apply_transform(rotation)
        component.apply_translation([0, machine.y / 2, 0])

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
