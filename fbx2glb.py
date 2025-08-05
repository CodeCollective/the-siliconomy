import bpy
import os

# === CONFIG ===
fbx_path = "/home/julian/Downloads/CrateFBX/FBX/Create.FBX"
texture_dir = "/home/julian/Downloads/CrateFBX/Textures/1024"
output_path = "/home/julian/Downloads/CrateFBX/Create.glb"

# === CLEAN START ===
bpy.ops.wm.read_factory_settings(use_empty=True)

# === IMPORT FBX ===
bpy.ops.import_scene.fbx(filepath=fbx_path)

# === TEXTURE ASSIGNMENT ===
# Simple filename-to-channel mapping
texture_map = {
    "diffuse": "Base Color",
    "normal": "Normal",
    "spec": "Specular",
}

# Find texture files
for mat in bpy.data.materials:
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if not bsdf:
        continue

    for tex_type, input_name in texture_map.items():
        for file in os.listdir(texture_dir):
            if tex_type.lower() in file.lower():
                img_path = os.path.join(texture_dir, file)
                image = bpy.data.images.load(img_path)
                tex_node = mat.node_tree.nodes.new("ShaderNodeTexImage")
                tex_node.image = image
                mat.node_tree.links.new(bsdf.inputs[input_name], tex_node.outputs["Color"])

                # Normal map handling
                if tex_type == "normal":
                    norm_node = mat.node_tree.nodes.new("ShaderNodeNormalMap")
                    mat.node_tree.links.new(norm_node.inputs["Color"], tex_node.outputs["Color"])
                    mat.node_tree.links.new(bsdf.inputs["Normal"], norm_node.outputs["Normal"])

# === EXPORT GLB ===
bpy.ops.export_scene.gltf(filepath=output_path, export_format='GLB')
    