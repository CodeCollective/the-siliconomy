import trimesh
import numpy as np
from shapely.geometry import Polygon, MultiPolygon
from PIL import ImageFont, Image, ImageDraw
from shapely.ops import unary_union
import hashlib
import pickle
import os
here = os.path.dirname(os.path.abspath(__file__))

def get_parameter_hash(text, font_path, font_size, depth):
    """Generate a reliable hash of all parameters that affect the output."""
    hash_obj = hashlib.sha256()
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
    # Create cache directory if it doesn't exist
    cache_dir = "./cache"
    if not os.path.exists(cache_dir):
        os.makedirs(cache_dir)
    
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