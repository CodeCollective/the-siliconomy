import trimesh
import numpy as np
from pygltflib import GLTF2, Scene, Node, Mesh, Primitive, Buffer, BufferView, Accessor
from pygltflib.utils import ImageFormat, Image

def create_laser_cutter_model():
    """Create a 3D model of a standard laser cutter"""
    # Main dimensions (mm)
    machine_width = 600
    machine_depth = 300
    machine_height = 200
    material_thickness = 2  # Sheet metal thickness
    
    # Create main enclosure
    enclosure = trimesh.creation.box(
        extents=[machine_width, machine_depth, machine_height],
        transform=np.eye(4)
    )
    
    # Create interior cavity (subtracted from enclosure)
    cavity = trimesh.creation.box(
        extents=[machine_width - material_thickness*2, 
                 machine_depth - material_thickness*2, 
                 machine_height - material_thickness],
        transform=np.eye(4)
    )
    enclosure = enclosure.difference(cavity)
    
    # Create cutting bed
    bed = trimesh.creation.box(
        extents=[machine_width - 50, machine_depth - 50, 5],
        transform=trimesh.transformations.translation_matrix([0, 0, -machine_height/2 + 10])
    )
    
    # Create laser head assembly
    laser_head = trimesh.creation.cylinder(
        radius=15,
        height=40,
        transform=trimesh.transformations.translation_matrix([0, 0, machine_height/2 - 20])
    )
    
    # Create gantry system
    x_rail = trimesh.creation.box(
        extents=[machine_width, 20, 20],
        transform=trimesh.transformations.translation_matrix([0, machine_depth/2 - 30, machine_height/2 - 30])
    )
    
    y_rail = trimesh.creation.box(
        extents=[20, machine_depth, 20],
        transform=trimesh.transformations.translation_matrix([0, 0, machine_height/2 - 30])
    )
    
    # Create control panel
    control_panel = trimesh.creation.box(
        extents=[150, material_thickness, 80],
        transform=trimesh.transformations.translation_matrix([machine_width/2 - 80, machine_depth/2, machine_height/2 - 40])
    )
    
    # Combine all parts
    machine = trimesh.util.concatenate([
        enclosure,
        bed,
        laser_head,
        x_rail,
        y_rail,
        control_panel
    ])
    
    return machine

def export_gltf(mesh, filename):
    """Export a trimesh object to GLTF format"""
    # Create a GLTF2 object
    gltf = GLTF2()
    
    # Create a scene
    scene = Scene()
    gltf.scenes.append(scene)
    
    # Create a node
    node = Node()
    gltf.nodes.append(node)
    
    # Add the node to the scene
    scene.nodes.append(0)
    
    # Create a mesh
    gltf_mesh = Mesh()
    gltf.meshes.append(gltf_mesh)
    
    # Create a primitive
    primitive = Primitive()
    gltf_mesh.primitives.append(primitive)
    
    # Convert trimesh to GLTF format
    # Note: This is a simplified conversion - for production use consider using trimesh's built-in GLTF export
    vertices = mesh.vertices
    faces = mesh.faces
    
    # Create buffer with vertex data
    vertex_buffer = np.concatenate([
        vertices.astype(np.float32),
        mesh.visual.vertex_normals.astype(np.float32)
    ], axis=1).tobytes()
    
    face_buffer = faces.astype(np.uint32).tobytes()
    
    # Add buffers
    buffer = Buffer()
    gltf.buffers.append(buffer)
    
    # Add buffer views
    bufferView1 = BufferView()
    bufferView1.buffer = 0
    bufferView1.byteOffset = 0
    bufferView1.byteLength = len(vertex_buffer)
    bufferView1.target = 34962  # ARRAY_BUFFER
    gltf.bufferViews.append(bufferView1)
    
    bufferView2 = BufferView()
    bufferView2.buffer = 0
    bufferView2.byteOffset = len(vertex_buffer)
    bufferView2.byteLength = len(face_buffer)
    bufferView2.target = 34963  # ELEMENT_ARRAY_BUFFER
    gltf.bufferViews.append(bufferView2)
    
    # Add accessors
    accessor1 = Accessor()
    accessor1.bufferView = 0
    accessor1.byteOffset = 0
    accessor1.componentType = 5126  # FLOAT
    accessor1.count = len(vertices)
    accessor1.type = "VEC3"
    accessor1.min = vertices.min(axis=0).tolist()
    accessor1.max = vertices.max(axis=0).tolist()
    gltf.accessors.append(accessor1)
    
    accessor2 = Accessor()
    accessor2.bufferView = 0
    accessor2.byteOffset = 0
    accessor2.componentType = 5126  # FLOAT
    accessor2.count = len(vertices)
    accessor2.type = "VEC3"
    gltf.accessors.append(accessor2)
    
    accessor3 = Accessor()
    accessor3.bufferView = 1
    accessor3.byteOffset = 0
    accessor3.componentType = 5125  # UNSIGNED_INT
    accessor3.count = len(faces) * 3
    accessor3.type = "SCALAR"
    gltf.accessors.append(accessor3)
    
    # Set primitive attributes
    primitive.attributes.POSITION = 0
    primitive.attributes.NORMAL = 1
    primitive.indices = 2
    
    # Link mesh to node
    node.mesh = 0
    
    # Save the GLTF file
    gltf.save(filename)
    print(f"Exported laser cutter model to {filename}")

def main():
    # Create the laser cutter model
    print("Creating laser cutter 3D model...")
    laser_cutter = create_laser_cutter_model()
    
    # Export to GLTF
    print("Exporting to GLTF format...")
    export_gltf(laser_cutter, "laser_cutter.gltf")
    
    # Also export as GLB (binary version)
    laser_cutter.export("laser_cutter.glb", file_type='glb')
    print("Exported laser cutter model to laser_cutter.glb")
    
    print("Done!")

if __name__ == "__main__":
    main()