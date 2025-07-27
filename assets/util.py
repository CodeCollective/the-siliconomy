import trimesh
import numpy as np
from shapely.geometry import Polygon, MultiPolygon
from PIL import ImageFont, Image, ImageDraw
from shapely.ops import unary_union
from trimesh.visual.texture import SimpleMaterial, TextureVisuals
import hashlib
import pickle
from trimesh.transformations import rotation_matrix, translation_matrix
import os
here = os.path.dirname(os.path.abspath(__file__))
hash_obj = hashlib.sha256()

cache_dir = os.path.join(here, "cache")

# Create cache directory if it doesn't exist
if not os.path.exists(cache_dir):
    os.makedirs(cache_dir)


def rotate(mesh, angle=[0, 0, 0]):
    """
    Rotate a trimesh object by specified angles (in degrees) about x, y, and z axes.

    Parameters:
    mesh (trimesh.Trimesh): The mesh to rotate.
    angle (list or tuple): Rotation angles in degrees for [x, y, z] axes.

    Returns:
    trimesh.Trimesh: The rotated mesh.
    """
    # Convert degrees to radians
    angle_rad = np.radians(angle)

    # Define the origin for rotation (can be the mesh centroid or origin)
    origin = [0,0,0]

    # Rotation about X axis
    rot_x = rotation_matrix(angle_rad[0], [1, 0, 0], point=origin)
    # Rotation about Y axis
    rot_y = rotation_matrix(angle_rad[1], [0, 1, 0], point=origin)
    # Rotation about Z axis
    rot_z = rotation_matrix(angle_rad[2], [0, 0, 1], point=origin)

    # Combine rotations (Z * Y * X order)
    transform = rot_z @ rot_y @ rot_x

    # Apply the transformation
    mesh.apply_transform(transform)

    return mesh
import numpy as np
from trimesh.transformations import translation_matrix
from trimesh.transformations import translation_matrix

def center(mesh):
    """
    Center a trimesh object with respect to its centroid.

    Parameters:
    mesh (trimesh.Trimesh): The mesh to center.

    Returns:
    trimesh.Trimesh: The centered mesh.
    """
    # Compute the centroid of the mesh
    centroid = mesh.centroid

    # Create a translation matrix to move the mesh to the origin
    tform = translation_matrix(-centroid)

    # Apply the transformation
    mesh.apply_transform(tform)

    return mesh

def translate(mesh, offset=[0, 0, 0]):
    """
    Translate a trimesh object by a given offset vector.

    Parameters:
    mesh (trimesh.Trimesh): The mesh to translate.
    offset (list or tuple): Translation vector [x, y, z].

    Returns:
    trimesh.Trimesh: The translated mesh.
    """
    # Create the translation matrix
    tform = translation_matrix(offset)

    # Apply the transformation
    mesh.apply_transform(tform)

    return mesh

def get_parameter_hash(text, font_path, font_size, depth):
    """Generate a reliable hash of all parameters that affect the output."""
    hash_obj.update(text.encode('utf-8'))
    hash_obj.update(font_path.encode('utf-8'))
    hash_obj.update(str(font_size).encode('utf-8'))
    hash_obj.update(str(depth).encode('utf-8'))
    return hash_obj.hexdigest()

def create_text_mesh_custom_font(text, font_path=os.path.join(here, "nofile"), font_size=100, depth=2):
    """
    Render text using a custom TTF font via Pillow, export to SVG,
    parse path with svgpathtools, then extrude to a 3D mesh.
    """
    
    # Generate hash for the current parameters
    param_hash = get_parameter_hash(text, font_path, font_size, depth)
    cache_file = os.path.join(cache_dir, f"{param_hash}.pkl")
    
    # Try to load from cache
    if os.path.exists(cache_file):
        try:
            with open(cache_file, 'rb') as f:
                return pickle.load(f)
        except (pickle.PickleError, EOFError):
            print("Warning: Cache file corrupted, regenerating mesh...")
    
    # Create image and draw text
    font = ImageFont.truetype(font_path, font_size)
    (width, height) = font.getsize(text)
    image = Image.new("L", (width + 10, height + 10), 0)
    draw = ImageDraw.Draw(image)
    draw.text((5, 5), text, fill=255, font=font)

    # Convert to SVG using svgwrite and the bitmap outline
    contours = []
    for y in range(image.height):
        for x in range(image.width):
            if image.getpixel((x, y)) > 0:
                contours.append((x, -y))  # Flip Y axis for geometric consistency

    if not contours:
        raise ValueError("Text image is empty — font may be missing.")

    # Turn pixel cloud into a Shapely polygon
    pixels = [Polygon([
        (x, y),
        (x + 1, y),
        (x + 1, y + 1),
        (x, y + 1)
    ]) for x, y in contours]

    unioned = unary_union(pixels)
    if isinstance(unioned, Polygon):
        polygons = [unioned]
    elif isinstance(unioned, MultiPolygon):
        polygons = list(unioned.geoms)
    else:
        raise ValueError("Failed to extract polygonal outlines from text.")

    # Extrude
    mesh = trimesh.util.concatenate([
        trimesh.creation.extrude_polygon(p, height=depth)
        for p in polygons if p.area > 1
    ])
    
    # Save to cache for future use
    try:
        with open(cache_file, 'wb') as f:
            pickle.dump(mesh, f)
    except (pickle.PickleError, IOError) as e:
        print(f"Warning: Failed to cache mesh ({str(e)})")

    return mesh


def generate_uv_coordinates(mesh):
    """Generate simple UV coordinates using bounding box projection"""
    vertices = mesh.vertices
    bounds = mesh.bounds
    
    # Get the size of the bounding box
    size = bounds[1] - bounds[0]
    
    # Project to UV coordinates (0-1 range)
    u = (vertices[:, 0] - bounds[0, 0]) / max(size[0], 1e-8)
    v = (vertices[:, 1] - bounds[0, 1]) / max(size[1], 1e-8)
    
    # Stack to create UV array
    uv = np.column_stack([u, v])
    
    # Clamp to [0, 1] range
    uv = np.clip(uv, 0, 1)
    
    return uv


def add_texture(mesh, texture_filename):
    """Add texture to a mesh with automatically generated UV coordinates"""
    image_path = os.path.join(here, 'textures', texture_filename)
    im = Image.open(image_path)
    
    # Generate UV coordinates
    uv = generate_uv_coordinates(mesh)
    
    mesh.visual = TextureVisuals(
        uv=uv,
        material=SimpleMaterial(image=im)
    )
    return mesh

def add_texture_simple(mesh, texture_filename):
    """Apply the center pixel of the texture to the entire mesh."""
    image_path = os.path.join(here, 'textures', texture_filename)
    im = Image.open(image_path)

    # Get number of vertices
    num_vertices = len(mesh.vertices)

    # Assign UV coordinates at the center of the texture to all vertices
    uv = np.tile([0.5, 0.5], (num_vertices, 1))

    mesh.visual = TextureVisuals(
        uv=uv,
        material=SimpleMaterial(image=im)
    )
    return mesh

def create_rect_with_hole(width, height, top, bottom, left, right, 
                         plane="xy", center_planes="xyz", extrusion_height=4):
    """
    Create a 3D extruded rectangular polygon with a rectangular hole.
    
    Parameters:
        width (float): Width of the outer rectangle.
        height (float): Height of the outer rectangle.
        top (float): Top margin between outer and inner rectangle.
        bottom (float): Bottom margin.
        left (float): Left margin.
        right (float): Right margin.
        plane (str): Plane to create the 2D profile in ('xy', 'xz', 'yz').
        center_planes (str/list): Which planes to center the object in, as:
                                 - String: any combination of 'x','y','z' (e.g. "xy", "yzx")
                                 - List: [x,y,z] where 1=center, 0=don't center (e.g. [1,0,1])
        extrusion_height (float): Height of extrusion in 3D.
    
    Returns:
        trimesh.Trimesh: A 3D mesh of the extruded rectangle with hole.
    """
    # Create outer rectangle coordinates (counter-clockwise)
    outer_2d = np.array([
        [-width / 2, -height / 2],
        [ width / 2, -height / 2],
        [ width / 2,  height / 2],
        [-width / 2,  height / 2]
    ])

    # Create inner rectangle (hole, clockwise winding)
    inner_2d = np.array([
        [-width / 2 + left,  height / 2 - top],
        [ width / 2 - right,  height / 2 - top],
        [ width / 2 - right, -height / 2 + bottom],
        [-width / 2 + left, -height / 2 + bottom]
    ])

    # Always create polygon in XY plane first, then transform
    polygon_with_hole = Polygon(outer_2d, [inner_2d])
    mesh = trimesh.creation.extrude_polygon(polygon_with_hole, height=extrusion_height)
    
    return mesh

def generateHoneycomb(machine):
    hash_object = hashlib.sha256(str(machine).encode())  # Convert string to bytes
    hex_dig = hash_object.hexdigest()            # Get hexadecimal digest
    filename = os.path.join(cache_dir, "honeycomb" + hex_dig + ".pkl")
    if os.path.exists(filename):
        with open(filename, 'rb') as f:
            return pickle.load(f)
        
    # Honeycomb pattern
    honeycomb_list = []
    hex_radius = 5
    for x in np.arange(-machine.x / 2 + 60, machine.x / 2 - 60, hex_radius * 1.5):
        for y in np.arange(-machine.z / 2 + 60, machine.z / 2 - 60, hex_radius * np.sqrt(3)):
            hexagon = trimesh.creation.cylinder(
                radius=hex_radius*0.6,
                height=3,
                sections=6,
                transform=trimesh.transformations.translation_matrix([
                    x + (hex_radius * 0.75 if (y / hex_radius) % 2 else 0),
                    y,
                    0
                ])
            )
            honeycomb_list.append(hexagon)
    retval = trimesh.util.concatenate(honeycomb_list)
    with open(filename, 'wb') as f:
        pickle.dump(retval, f)
    return retval
