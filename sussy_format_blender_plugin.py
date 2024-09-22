bl_info = {
    "name": "Sussy Format",
    "blender": (3, 0, 0),
    "category": "Import-Export",
}

import bpy
import struct
from bpy_extras.io_utils import ExportHelper, ImportHelper

def write_sussy(filepath, mesh):
    pos_normal_map = {}
    uv_map = {}
    
    pos_normal_list = []
    uv_list = []
    triangles = []

    # Ensure the mesh is in object mode
    bpy.ops.object.mode_set(mode='OBJECT')
    
    # Calculate split normals and triangulation in memory
    mesh.calc_normals_split()
    mesh.calc_loop_triangles()

    uv_layer = mesh.uv_layers.active.data if mesh.uv_layers.active else None

    for tri in mesh.loop_triangles:
        tri_indices = []
        
        for loop_index in tri.loops:
            vert = mesh.vertices[mesh.loops[loop_index].vertex_index]
            pos = tuple(vert.co)
            normal = tuple(mesh.loops[loop_index].normal)
            
            pos_normal_key = (pos, normal)
            
            if pos_normal_key not in pos_normal_map:
                pos_normal_map[pos_normal_key] = len(pos_normal_list)
                pos_normal_list.append((pos, normal))
            
            pos_normal_id = pos_normal_map[pos_normal_key]

            uv_id = 0
            if uv_layer:
                uv = tuple(uv_layer[loop_index].uv)
                if uv not in uv_map:
                    uv_map[uv] = len(uv_list)
                    uv_list.append(uv)
                uv_id = uv_map[uv]

            tri_indices.append((pos_normal_id, uv_id))
        
        triangles.extend(tri_indices)

    try:
        with open(filepath, 'wb') as file:
            file.write(struct.pack('H', len(pos_normal_list)))
            
            for pos, normal in pos_normal_list:
                file.write(struct.pack('3f', *pos))
                file.write(struct.pack('3f', *normal))
            
            file.write(struct.pack('H', len(uv_list)))
            
            for uv in uv_list:
                file.write(struct.pack('2f', *uv))
            
            file.write(struct.pack('H', len(triangles) // 3))
            
            for i in range(0, len(triangles), 3):
                for j in range(3):
                    file.write(struct.pack('H', triangles[i + j][0]))
                    file.write(struct.pack('H', triangles[i + j][1]))
    except IOError as e:
        print(f"Error writing file: {e}")

def read_sussy(filepath):
    try:
        with open(filepath, 'rb') as file:
            pos_normal_count = struct.unpack('H', file.read(2))[0]
            
            pos_normal_list = []
            pos_normal_map = {}
            for _ in range(pos_normal_count):
                pos = struct.unpack('3f', file.read(12))
                normal = struct.unpack('3f', file.read(12))
                pos_normal_key = (pos, normal)
                
                if pos_normal_key not in pos_normal_map:
                    pos_normal_map[pos_normal_key] = len(pos_normal_list)
                    pos_normal_list.append(pos_normal_key)
                else:
                    pos_normal_id = pos_normal_map[pos_normal_key]
                    pos_normal_list.append(pos_normal_list[pos_normal_id])
            
            uv_count = struct.unpack('H', file.read(2))[0]
            
            uv_list = []
            uv_map = {}
            for _ in range(uv_count):
                uv = struct.unpack('2f', file.read(8))
                if uv not in uv_map:
                    uv_map[uv] = len(uv_list)
                    uv_list.append(uv)
                else:
                    uv_id = uv_map[uv]
                    uv_list.append(uv_list[uv_id])
            
            triangle_count = struct.unpack('H', file.read(2))[0]
            
            triangles = []
            for _ in range(triangle_count):
                tri = []
                for _ in range(3):
                    pos_normal_id = struct.unpack('H', file.read(2))[0]
                    uv_id = struct.unpack('H', file.read(2))[0]
                    
                    # Update pos_normal_id and uv_id to point to the correct index
                    pos_normal_id = pos_normal_map.get(pos_normal_list[pos_normal_id], pos_normal_id)
                    uv_id = uv_map.get(uv_list[uv_id], uv_id)
                    
                    tri.append((pos_normal_id, uv_id))
                triangles.append(tri)
                
    except IOError as e:
        print(f"Error reading file: {e}")
        return [], [], []
    except struct.error as e:
        print(f"Error unpacking data: {e}")
        return [], [], []
    
    return pos_normal_list, uv_list, triangles

def create_mesh_from_data(pos_normal_list, uv_list, triangles):
    # Create a new mesh and object
    mesh = bpy.data.meshes.new("ImportedMesh")
    obj = bpy.data.objects.new("ImportedObject", mesh)
    
    # Link the object to the scene
    bpy.context.collection.objects.link(obj)
    
    # Prepare the mesh data
    vertices = []
    vertex_map = {}
    
    # Collect unique vertices
    for pos, normal in pos_normal_list:
        if pos not in vertex_map:
            vertex_map[pos] = len(vertices)
            vertices.append(pos)
    
    # Create faces based on the triangles
    faces = []
    for tri in triangles:
        face = [vertex_map[pos_normal_list[tri[i][0]][0]] for i in range(3)]
        faces.append(face)

    # Create the mesh from the vertex and face data
    mesh.from_pydata(vertices, [], faces)
    mesh.update()

    # Add UV mapping if available
    if uv_list:
        if not mesh.uv_layers:
            mesh.uv_layers.new()
        uv_layer = mesh.uv_layers.active.data
        
        # Ensure correct number of UV coordinates
        if len(uv_layer) >= len(vertices):
            for poly in mesh.polygons:
                for loop_idx in poly.loop_indices:
                    face_idx = poly.index
                    uv_id = triangles[face_idx][loop_idx % 3][1]
                    if uv_id < len(uv_list):
                        uv_layer[loop_idx].uv = uv_list[uv_id]
        else:
            print("Warning: UV map size does not match the number of loops.")

    # Set custom normals if available
    if pos_normal_list:
        mesh.use_auto_smooth = True
        custom_normals = [normal for _, normal in pos_normal_list]
        
        if len(custom_normals) == len(mesh.loops):
            mesh.normals_split_custom_set(custom_normals)
        else:
            print(f"Warning: Number of custom normals ({len(custom_normals)}) does not match number of loops ({len(mesh.loops)})")

    return obj

class ExportSussyFormat(bpy.types.Operator, ExportHelper):
    """Export to Sussy Format"""
    bl_idname = "export_scene.sussy"
    bl_label = "Export Sussy"
    
    filename_ext = ".sussy"
    
    def execute(self, context):
        obj = context.object
        if obj.type != 'MESH':
            self.report({'ERROR'}, "Selected object is not a mesh")
            return {'CANCELLED'}
        
        mesh = obj.data
        write_sussy(self.filepath, mesh)
        
        return {'FINISHED'}

class ImportSussyFormat(bpy.types.Operator, ImportHelper):
    """Import from Sussy Format"""
    bl_idname = "import_scene.sussy"
    bl_label = "Import Sussy"
    
    filename_ext = ".sussy"
    
    def execute(self, context):
        pos_normal_list, uv_list, triangles = read_sussy(self.filepath)
        create_mesh_from_data(pos_normal_list, uv_list, triangles)
        
        return {'FINISHED'}

def menu_func_export(self, context):
    self.layout.operator(ExportSussyFormat.bl_idname, text="Sussy Format (.sussy)")

def menu_func_import(self, context):
    self.layout.operator(ImportSussyFormat.bl_idname, text="Sussy Format (.sussy)")

def register():
    bpy.utils.register_class(ExportSussyFormat)
    bpy.utils.register_class(ImportSussyFormat)
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)

def unregister():
    bpy.utils.unregister_class(ExportSussyFormat)
    bpy.utils.unregister_class(ImportSussyFormat)
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)

if __name__ == "__main__":
    register()
