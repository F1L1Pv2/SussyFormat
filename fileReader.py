import struct

def read_uint16(file):
    return struct.unpack('<H', file.read(2))[0]

def read_float32(file):
    return struct.unpack('<f', file.read(4))[0]

def read_binary_file(filename):
    with open(filename, 'rb') as file:
        # Read [uint16 pos+normal count]
        pos_normal_count = read_uint16(file)
        print(f'Position/Normal count: {pos_normal_count}')

        # Read [float32 * 3 (pos) + float32 * 3 (normal)]
        positions = []
        normals = []
        for _ in range(pos_normal_count):
            pos = [read_float32(file) for _ in range(3)]
            normal = [read_float32(file) for _ in range(3)]
            positions.append(pos)
            normals.append(normal)
        
        print('\nPositions and Normals:')
        for i, (pos, normal) in enumerate(zip(positions, normals)):
            pos_str = ' '.join(f'{v:.2f}' for v in pos)
            normal_str = ' '.join(f'{v:.2f}' for v in normal)
            print(f'{i:2d}: Position: {pos_str} | Normal: {normal_str}')

        # Read [uint16 uv count]
        uv_count = read_uint16(file)
        print(f'\nUV count: {uv_count}')

        # Read [float32 * 2 uv]
        uvs = []
        for _ in range(uv_count):
            uv = [read_float32(file) for _ in range(2)]
            uvs.append(uv)
        
        print('UVs:')
        for i, uv in enumerate(uvs):
            uv_str = ' '.join(f'{v:.2f}' for v in uv)
            print(f'{i:2d}: UV: {uv_str}')

        # Read [uint16 triangles count]
        triangles_count = read_uint16(file)
        print(f'\nTriangles count: {triangles_count}')

        # Read [(uint16 pos+normal ID + uint16 uv ID) * 3]
        triangles = []
        for _ in range(triangles_count):
            triangle = []
            for _ in range(3):
                pos_normal_id = read_uint16(file)
                uv_id = read_uint16(file)
                triangle.append((pos_normal_id, uv_id))
            triangles.append(triangle)
        
        print('Triangles:')
        for i, triangle in enumerate(triangles):
            triangle_str = ' '.join(f'({pos_normal_id:2d}, {uv_id:2d})' for pos_normal_id, uv_id in triangle)
            print(f'{i:2d}: {triangle_str}')

if __name__ == "__main__":
    filename = 'untitled.sussy'  # Replace with your binary file path
    read_binary_file(filename)