import numpy as np

import trimesh
from trimesh.creation import cylinder, box
from trimesh.transformations import translation_matrix
from trimesh.boolean import difference
from shapely.geometry import LineString, Polygon

from copy import deepcopy
from types import SimpleNamespace
import os

from util import *  # translate, rotate, center, add_texture, add_texture_simple

here = os.path.dirname(os.path.abspath(__file__))

components = {}

# ------------------------------
# Scene / Room setup
# ------------------------------
room = SimpleNamespace(x=8000, y=8000, z=4000)
wall_width = 1

metallic_appearance = trimesh.visual.material.PBRMaterial(
    name="metal",
    baseColorFactor=[0.4, 0.4, 0.45, 1.0],
    metallicFactor=0.6,
    roughnessFactor=0.2
)
metallic_texture = trimesh.visual.TextureVisuals(material=metallic_appearance)

glass_material = trimesh.visual.material.PBRMaterial(
    baseColorFactor=[0.8, 0.9, 1.0, 0.3],
    metallicFactor=0.2,
    roughnessFactor=0.1,
    alphaMode="BLEND",
)

# ---------------------------------
# Electric Bike Layout
# ---------------------------------
wheel_radius = 280
wheel_thickness = 160 
tire_overhang = 10
hub_radius = 60
hub_length = 80
frame_tube_r = 100
handlebar_w = 600
stem_len = 250
seat_tube_angle = np.deg2rad(73)
head_tube_angle = np.deg2rad(71)
chainstay_len = 440
wheelbase = 1080
bb_drop = 70
bb_height = wheel_radius - bb_drop

rear_axle = np.array([0.0, 0.0, 0.0])
front_axle = np.array([wheelbase, 0.0, 0.0])
bb_center = np.array([chainstay_len/2, 0.0, bb_height])

seatpost_len = 500
seat_top = bb_center + seatpost_len * np.array([
    np.cos(np.pi/2 - seat_tube_angle), 0.0, np.sin(np.pi/2 - seat_tube_angle)
])

head_tube_len = 160
ht_base = front_axle + np.array([-90.0, 0.0, wheel_radius - 100.0])
ht_dir = np.array([-np.cos(head_tube_angle), 0.0, np.sin(head_tube_angle)])
ht_top = ht_base + ht_dir * head_tube_len

def cylinder_between(p0, p1, radius, sections=240, material=None):
    """Create a cylinder between p0 and p1.
    Robust to trimesh.geometry.align_vectors returning 3x3 or 4x4.
    """
    p0 = np.asarray(p0, dtype=float)
    p1 = np.asarray(p1, dtype=float)
    vec = p1 - p0
    length = np.linalg.norm(vec)
    if length == 0:
        length = 1e-9

    cyl = trimesh.creation.cylinder(radius=radius, height=length, sections=sections)

    # cylinder is along +Z by default; align +Z to the segment direction
    z_axis = np.array([0.0, 0.0, 1.0])
    R = trimesh.geometry.align_vectors(z_axis, vec / length)

    # Build a 4x4 transform from R, regardless of shape
    if isinstance(R, np.ndarray) and R.shape == (4, 4):
        M = R.copy()
    else:
        M = np.eye(4)
        M[:3, :3] = R

    # place at the midpoint
    M[:3, 3] = (p0 + p1) / 2.0

    cyl.apply_transform(M)

    if material is not None:
        cyl.visual = material
    return cyl


import numpy as np
import trimesh

import numpy as np
import trimesh

def hollow_cylinder(outer_r, inner_r, height, sections=128, cap=True):
    """
    Build a hollow cylinder (ring) with correct, outward-facing normals.
    Axis: Z. Center at origin. Height spans [-h/2, +h/2].
    """
    assert outer_r > inner_r > 0, f"Bad radii: outer={outer_r}, inner={inner_r}"
    n = int(sections)
    h = float(height) * 0.5

    theta = np.linspace(0, 2*np.pi, n, endpoint=False)
    c, s = np.cos(theta), np.sin(theta)

    # Rings
    outer_top    = np.column_stack([outer_r*c, outer_r*s, np.full(n, +h)])
    outer_bottom = np.column_stack([outer_r*c, outer_r*s, np.full(n, -h)])
    inner_top    = np.column_stack([inner_r*c, inner_r*s, np.full(n, +h)])
    inner_bottom = np.column_stack([inner_r*c, inner_r*s, np.full(n, -h)])

    # Vertex layout
    # 0..n-1      outer_top
    # n..2n-1     outer_bottom
    # 2n..3n-1    inner_top
    # 3n..4n-1    inner_bottom
    V = np.vstack([outer_top, outer_bottom, inner_top, inner_bottom])

    def idx(i): return i % n

    F = []

    # ---- Outer wall
    # For each sector, create two triangles with CCW order as seen from *outside* the ring.
    # (ob0, ot0, ob1) and (ot0, ot1, ob1)
    for i in range(n):
        ot0 = i
        ob0 = n + i
        ot1 = idx(i+1)
        ob1 = n + idx(i+1)
        F += [
            [ob0, ot0, ob1],
            [ot0, ot1, ob1],
        ]

    # ---- Inner wall
    # For the inner cylinder, the outward normal points toward the hole center,
    # so we flip winding relative to outer wall.
    # Use (it0, ib1, ib0) and (it0, it1, ib1) (CCW when viewed from inside).
    for i in range(n):
        it0 = 2*n + i
        ib0 = 3*n + i
        it1 = 2*n + idx(i+1)
        ib1 = 3*n + idx(i+1)
        F += [
            [it0, ib1, ib0],
            [it0, it1, ib1],
        ]

    if cap:
        # ---- Top cap (viewed from +Z) -> CCW
        for i in range(n):
            ot0 = i
            it0 = 2*n + i
            ot1 = idx(i+1)
            it1 = 2*n + idx(i+1)
            F += [
                [ot0, it0, it1],
                [ot0, it1, ot1],
            ]
        # ---- Bottom cap (viewed from -Z) -> flip winding
        for i in range(n):
            ob0 = n + i
            ib0 = 3*n + i
            ob1 = n + idx(i+1)
            ib1 = 3*n + idx(i+1)
            F += [
                [ob0, ib1, ib0],
                [ob0, ob1, ib1],
            ]

    mesh = trimesh.Trimesh(vertices=V, faces=np.asarray(F, dtype=np.int64), process=False)

    # Repair without reprocessing topology
    trimesh.repair.fix_normals(mesh)                # ensure consistent normals

    # --- Auto-check: ensure sidewall normals are truly "outward"
    # Compare vertex normals on the outer_top ring with radial directions.
    vt_normals = mesh.vertex_normals[:n]       # normals at outer_top vertices
    radial = np.column_stack([c, s, np.zeros(n)])
    # If mean dot < 0, the whole mesh is inverted; flip once.
    if np.mean(np.einsum('ij,ij->i', vt_normals, radial)) < 0.0:
        mesh.invert()
        trimesh.repair.fix_normals(mesh)

    # ----- UVs (basic but stable): cylindrical mapping for walls, radial for caps
    uv = np.zeros((len(V), 2), dtype=np.float32)
    u = (theta / (2*np.pi)).astype(np.float32)
    uv[0:n, 0] = u;       uv[0:n, 1]   = 1.0   # outer_top
    uv[n:2*n, 0] = u;     uv[n:2*n, 1] = 0.0   # outer_bottom
    uv[2*n:3*n, 0] = u;   uv[2*n:3*n, 1] = 1.0 # inner_top
    uv[3*n:4*n, 0] = u;   uv[3*n:4*n, 1] = 0.0 # inner_bottom

    def radial_uv(xy):
        scale = 0.5 / (outer_r + 1e-6)
        return np.column_stack([0.5 + xy[:,0]*scale, 0.5 + xy[:,1]*scale]).astype(np.float32)

    if cap:
        top_xy = np.vstack([outer_top[:, :2], inner_top[:, :2]])
        bot_xy = np.vstack([outer_bottom[:, :2], inner_bottom[:, :2]])
        top_uv = radial_uv(top_xy)
        bot_uv = radial_uv(bot_xy)
        uv[0:n, :]       = top_uv[0:n, :]
        uv[2*n:3*n, :]   = top_uv[n:2*n, :]
        uv[n:2*n, :]     = bot_uv[0:n, :]
        uv[3*n:4*n, :]   = bot_uv[n:2*n, :]

    mesh.visual = trimesh.visual.texture.TextureVisuals(uv=uv)
    return mesh


# ----------------
# Wheels
# ----------------
def make_solid_wheel(center, radius, thickness, tire_lip=30, add_motor=False, hub_clearance=0.75):
    """
    tire_lip: how much narrower the hub hole is than the tire outer radius.
    hub_clearance: small gap so the hub doesn't coincide with the tire's inner radius.
    """
    # dimensions
    inner_r = radius - tire_lip
    assert inner_r > 0, "Choose tire_lip < radius"

    # central disc (hub) slightly smaller than the tire's inner radius
    hub_r = max(inner_r - hub_clearance, 1e-3)

    disc = cylinder(radius=hub_r, height=thickness, sections=240)
    disc.visual = trimesh.visual.TextureVisuals(material=metallic_appearance)
    translate(disc, center)

    # tire as hollow cylinder (no boolean), small height margin to avoid z-fighting
    tire = hollow_cylinder(
        outer_r=radius,
        inner_r=inner_r,
        height=thickness * 1.05,
        sections=240,
        cap=True,
    )
    add_texture(tire, "aluminum.jpg")
    translate(tire, center)

    parts = {"disc": disc, "tire": tire}

    if add_motor:
        motor_body = cylinder(radius=hub_radius, height=hub_length)
        add_texture(motor_body, "red.jpg")
        translate(motor_body, center)
        parts["motor_body"] = motor_body

        cable = trimesh.creation.capsule(height=200, radius=8)
        add_texture(cable, "cable.jpg")
        translate(cable, center + np.array([hub_radius, 0, thickness/2]))
        rotate(cable, [0, 45, 0])
        parts["motor_cable"] = cable

    # rotate each part individually; don't concatenate
    for m in parts.values():
        rotate(m, [90, 0, 0])

    return parts


# Build wheels as multiple nodes so PBR survives export
rear_wheel_parts = make_solid_wheel(rear_axle, wheel_radius, wheel_thickness, tire_lip=tire_overhang, add_motor=True)
front_wheel_parts = make_solid_wheel(front_axle, wheel_radius, wheel_thickness, tire_lip=tire_overhang, add_motor=False)

for key, mesh in rear_wheel_parts.items():
    components[f"rear_wheel_{key}"] = mesh
for key, mesh in front_wheel_parts.items():
    components[f"front_wheel_{key}"] = mesh


# ----------------
# Frame Tubes
# ----------------
seat_cluster = seat_top

chainstay = cylinder_between(rear_axle + [0,0,wheel_thickness/2], bb_center, frame_tube_r, material=metallic_texture)
seatstay = cylinder_between(rear_axle + [0,0,wheel_thickness/2], seat_cluster, frame_tube_r*0.75, material=metallic_texture)
seattube = cylinder_between(bb_center, seat_cluster + [-60,0,-60], frame_tube_r, material=metallic_texture)
down_tube = cylinder_between(bb_center+[-50,0,0], ht_base+[50,0,0], frame_tube_r*1.1, material=metallic_texture, sections=8)
translate(down_tube, [0,0,-100])  # lower slightly 
# build a scaling transform
scale_matrix = np.eye(4)
scale_matrix[1, 1] = 1.5   # stretch in Y
scale_matrix[2, 2] = 2.0   # stretch in Z

# apply it
down_tube.apply_transform(scale_matrix)

top_tube = cylinder_between(seat_cluster, ht_top, frame_tube_r*0.9, material=metallic_texture, sections=6)

components.update({
    "chainstay": chainstay,
    #"seatstay": seatstay,
    "seattube": seattube,
    "down_tube": down_tube,
#    "top_tube": top_tube,
})

head_tube = cylinder_between(ht_base, ht_top, frame_tube_r*1.2, material=metallic_texture)
#components["head_tube"] = head_tube

fork_left = cylinder_between(front_axle + [0,0,wheel_thickness/2], ht_base + [-15, 0, 0], frame_tube_r*0.7, material=metallic_texture)
fork_right = cylinder_between(front_axle + [0,0,wheel_thickness/2], ht_base + [ 15, 0, 0], frame_tube_r*0.7, material=metallic_texture)
#components.update({"fork_left": fork_left})
#components.update({"fork_right": fork_right})

# Stem + handlebar
stem_start = ht_top + [100,0,0]
stem_end = stem_start + ht_dir * stem_len
stem = cylinder_between(stem_start, stem_end, frame_tube_r*0.3, material=metallic_texture)
handlebar_left = cylinder_between(stem_end, stem_end + np.array([0.0, -handlebar_w/2, 0.0]), frame_tube_r*0.2, material=metallic_texture)
handlebar_right = cylinder_between(stem_end, stem_end + np.array([0.0,  handlebar_w/2, 0.0]), frame_tube_r*0.2, material=metallic_texture)
add_texture(handlebar_left, "aluminum.jpg")
add_texture(handlebar_right, "aluminum.jpg")
components.update({"stem": stem, "handlebar_left": handlebar_left, "handlebar_right": handlebar_right})

# Seatpost + saddle
seatpost = cylinder_between(seat_cluster - [0,0,120], seat_cluster, frame_tube_r*0.6, material=metallic_texture)
saddle = box([260, 140, 40])
add_texture_simple(saddle, "red.jpg")
translate(saddle, seat_cluster + np.array([60, 0, 10]))
rotate(saddle, [0, 0, 10])
#components.update({"seatpost": seatpost, "saddle": saddle})

# ------------------------------
# Battery pack and controller box
# ------------------------------
pack = box([360, 120, 90])
add_texture_simple(pack, "aluminum.jpg")
pack_anchor = (bb_center + ht_base) / 2 + np.array([20.0, 0.0, -40.0])
translate(pack, pack_anchor)
vec_dt = ht_base - bb_center
yaw = np.degrees(np.arctan2(vec_dt[1], vec_dt[0]))
pitch = np.degrees(np.arctan2(vec_dt[2], np.linalg.norm(vec_dt[:2])))
rotate(pack, [pitch, 0, 0])
components["battery_pack"] = pack

ctl = box([160, 80, 60])
add_texture_simple(ctl, "steel.jpg")
translate(ctl, bb_center + np.array([60, 0, 40]))
components["controller_box"] = ctl

ctl_cable = trimesh.creation.capsule(height=600, radius=6)
add_texture(ctl_cable, "cable.jpg")
translate(ctl_cable, bb_center + np.array([80, 0, 40]))
rotate(ctl_cable, [0, 30, 0])
components["controller_cable"] = ctl_cable

# ------------------------------
# Stand
# ------------------------------
stand_x = 4000
stand_y = 2000
stand_z = 40
stand = box([stand_x, stand_y, stand_z])
add_texture_simple(stand, "aluminum.jpg")
translate(stand, [0, 0, -300])
components["stand"] = stand

# ---------------------------------
# Final scene assembly
# ---------------------------------
scene = trimesh.Scene(components.values())
scene.bg_color = [0.9, 0.9, 0.9, 1.0]

export_path = os.path.join(here, "e_bike.glb")
new_scene = trimesh.Scene()

for name, mesh in components.items():
    print(f"Processing {name}")
    rotate(mesh, [-90, 0, 0])  # rotate to match control.html
    new_scene.add_geometry(mesh, node_name=name, geom_name=name)
    if hasattr(mesh, 'metadata') and isinstance(mesh.metadata, dict):
        mesh.metadata["name"] = name

new_scene.bg_color = scene.bg_color
new_scene.export(export_path)

print("Exported:", export_path)
