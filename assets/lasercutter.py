import trimesh
import numpy as np
from trimesh.visual import TextureVisuals, material
from trimesh.creation import cylinder, box, icosphere
import os
import meshlib.mrmeshpy as mrmeshpy
import pyvista as pv
import vtk
import freetype
import cairocffi as cairo
import svgpathtools
import numpy as np
from shapely.geometry import Polygon
import trimesh
import tempfile
import os

from PIL import ImageFont, Image, ImageDraw
import svgwrite
import numpy as np
from shapely.geometry import Polygon, MultiPolygon
from shapely.ops import unary_union
import shapely
import trimesh
import tempfile
import os
from svgpathtools import svg2paths


def create_text_mesh_custom_font(text, font_path="nofile", font_size=100, depth=2):
    """
    Render text using a custom TTF font via Pillow, export to SVG,
    parse path with svgpathtools, then extrude to a 3D mesh.
    """
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

    return mesh



def create_laser_cutter_model():
    """Create a detailed 3D model of a laser cutter with all components"""
    # Main dimensions (mm)
    machine_width = 600
    machine_depth = 300
    machine_height = 200
    material_thickness = 2  # Sheet metal thickness
    
    # Create main enclosure with texture
    enclosure = box(
        extents=[machine_width, machine_depth, machine_height]
    )
    
    # Create interior cavity (subtracted from enclosure)
    cavity = box(
        extents=[machine_width - material_thickness*2, 
                 machine_depth - material_thickness*2, 
                 machine_height - material_thickness]
    )
    enclosure = enclosure.difference(cavity)
    
    # Apply metallic material to enclosure
    enclosure.visual = TextureVisuals(
        material=material.PBRMaterial(
            metallicFactor=0.7,
            roughnessFactor=0.3,
            baseColorFactor=[0.8, 0.8, 0.8, 1.0]
        )
    )
    
    # Create aluminum cutting bed with honeycomb pattern
    bed = box(
        extents=[machine_width - 50, machine_depth - 50, 5],
        transform=trimesh.transformations.translation_matrix([0, 0, -machine_height/2 + 10])
    )
    
    # Add honeycomb pattern to bed
    honeycomb = []
    hex_radius = 10
    for x in np.arange(-machine_width/2 + 60, machine_width/2 - 60, hex_radius * 1.5):
        for y in np.arange(-machine_depth/2 + 60, machine_depth/2 - 60, hex_radius * np.sqrt(3)):
            hexagon = trimesh.creation.cylinder(
                radius=hex_radius,
                height=3,
                sections=6,
                transform=trimesh.transformations.translation_matrix([
                    x + (hex_radius * 0.75 if (y/hex_radius) % 2 else 0),
                    y,
                    -machine_height/2 + 12.5
                ])
            )
            honeycomb.append(hexagon)
    bed.visual = TextureVisuals(material=material.PBRMaterial(
        metallicFactor=0.5,
        roughnessFactor=0.4,
        baseColorFactor=[0.9, 0.9, 0.9, 1.0]
    ))
    
    # Create laser head assembly with lens
    laser_body = cylinder(
        radius=15,
        height=40,
        transform=trimesh.transformations.translation_matrix([0, 0, machine_height/2 - 20])
    )
    laser_body.visual = TextureVisuals(material=material.PBRMaterial(
        metallicFactor=0.8,
        roughnessFactor=0.2,
        baseColorFactor=[0.2, 0.2, 0.2, 1.0]
    ))
    
    laser_lens = cylinder(
        radius=8,
        height=5,
        transform=trimesh.transformations.translation_matrix([0, 0, machine_height/2 + 10])
    )
    laser_lens.visual = TextureVisuals(material=material.PBRMaterial(
        metallicFactor=0.1,
        roughnessFactor=0.05,
        baseColorFactor=[0.1, 0.3, 0.8, 0.7],
        emissiveFactor=[0.1, 0.1, 0.5]
    ))
    
    # Create gantry system with linear rails
    x_rail = box(
        extents=[machine_width, 20, 20],
        transform=trimesh.transformations.translation_matrix([0, machine_depth/2 - 30, machine_height/2 - 30])
    )
    x_rail.visual = TextureVisuals(material=material.PBRMaterial(
        metallicFactor=0.6,
        roughnessFactor=0.4,
        baseColorFactor=[0.3, 0.3, 0.3, 1.0]
    ))
    
    y_rail = box(
        extents=[20, machine_depth, 20],
        transform=trimesh.transformations.translation_matrix([0, 0, machine_height/2 - 30])
    )
    
    # Create belt drive system
    belt_pulley = cylinder(
        radius=5,
        height=15,
        transform=trimesh.transformations.translation_matrix([machine_width/2 - 40, machine_depth/2 - 40, machine_height/2 - 25])
    )
    
    # Create control panel with buttons and display
    panel = box(
        extents=[150, material_thickness, 80],
        transform=trimesh.transformations.translation_matrix([machine_width/2 - 80, machine_depth/2, machine_height/2 - 40])
    )
    panel.visual = TextureVisuals(material=material.PBRMaterial(
        metallicFactor=0.2,
        roughnessFactor=0.6,
        baseColorFactor=[0.1, 0.1, 0.1, 1.0]
    ))
    
    # Add buttons
    buttons = []
    for i in range(5):
        button = cylinder(
            radius=5,
            height=2,
            transform=trimesh.transformations.translation_matrix([
                machine_width/2 - 100 + i*15,
                machine_depth/2 + 1,
                machine_height/2 - 20
            ])
        )
        button.visual = TextureVisuals(material=material.PBRMaterial(
            metallicFactor=0.1,
            roughnessFactor=0.7,
            baseColorFactor=[0.8, 0.1, 0.1, 1.0]
        ))
        buttons.append(button)
    
    # Add LCD display
    display = box(
        extents=[60, 2, 30],
        transform=trimesh.transformations.translation_matrix([
            machine_width/2 - 60,
            machine_depth/2 + 1,
            machine_height/2 - 10
        ])
    )
    display.visual = TextureVisuals(material=material.PBRMaterial(
        emissiveFactor=[0.2, 0.6, 0.2],
        baseColorFactor=[0.1, 0.3, 0.1, 1.0]
    ))
    
    # Create ventilation system
    vents = []
    for i in range(8):
        vent = box(
            extents=[80, material_thickness, 5],
            transform=trimesh.transformations.translation_matrix([
                -machine_width/2 + 50 + i*10,
                -machine_depth/2,
                machine_height/2 - 50
            ])
        )
        vents.append(vent)
    
    # Create cable management
    cables = []
    for i in range(3):
        cable = trimesh.creation.capsule(
            height=100,
            radius=3,
            transform=trimesh.transformations.translation_matrix([
                machine_width/2 - 30,
                machine_depth/2 - 50 - i*10,
                machine_height/2 - 60
            ])
        )
        cable.visual = TextureVisuals(material=material.PBRMaterial(
            metallicFactor=0.1,
            roughnessFactor=0.8,
            baseColorFactor=[0.3, 0.3, 0.3, 1.0]
        ))
        cables.append(cable)
    
    # Add branding/logo
    # Generate text mesh using meshlib
    logo_mesh = create_text_mesh_custom_font("Code Collective")
    
    logo_mesh.apply_translation([-machine_width/2 + 30, machine_depth/2 + 1, machine_height/2 - 30])
    logo_mesh.visual = TextureVisuals(material=material.PBRMaterial(
        metallicFactor=0.9,
        roughnessFactor=0.2,
        baseColorFactor=[0.8, 0.1, 0.1, 1.0]
    ))
    
    # Combine all parts
    components = [
        enclosure,
        bed,
        *honeycomb,
        laser_body,
        laser_lens,
        x_rail,
        y_rail,
        belt_pulley,
        panel,
        *buttons,
        display,
        *vents,
        *cables,
        logo_mesh
    ]
    
    # Set a nice background color for the scene
    scene = trimesh.Scene(components)
    scene.bg_color = [0.9, 0.9, 0.9, 1.0]
    
    return scene

def export_model(scene):
    """Export the model to GLB format"""
    # Create output directory if it doesn't exist
    os.makedirs("output", exist_ok=True)
    
    # Export as GLB (binary GLTF)
    export_path = os.path.join("output", "laser_cutter.glb")
    scene.export(export_path)
    print(f"Exported laser cutter model to {export_path}")
    

def main():
    print("Creating detailed laser cutter model...")
    laser_cutter = create_laser_cutter_model()
    
    print("Exporting model...")
    export_model(laser_cutter)
    
    print("Done! Model exported to /output directory")

if __name__ == "__main__":
    main()