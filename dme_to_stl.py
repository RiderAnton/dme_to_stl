import struct
import sys
import numpy
from stl import mesh

def main():
    if len(sys.argv) < 3:
        print("Usage: dme_to_stl.py <input> <output>", file=sys.stderr)
        return
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    f_in = open(input_file, "rb")
    #DMOD block
    magic = f_in.read(4)
    assert magic.decode("utf-8") == "DMOD", "Not a DME file"
    print(magic.decode("utf-8"))
    version = struct.unpack("<I", f_in.read(4))[0]
    assert 3 <= version <= 4, "Unsupported DME version"
    print("Version: {}".format(version))
    dmat_length = struct.unpack("<I", f_in.read(4))[0]
    print("DMAT length: {}".format(dmat_length))

    #DMAT block
    print("Seeking from {} ".format(f_in.tell()), end="")
    f_in.seek(f_in.tell() + dmat_length + 28)
    print("to {}".format(f_in.tell()))

    #MESH block
    if version == 3:
        unknown = f_in.read(16)
        bytes_per_vertex, vertex_count, index_size, index_count = struct.unpack("<IIII", f_in.read(16))
        vert_stream_count = 1
        draw_offset = None
        draw_count = None
        bone_count = None
    else:
        bytes_per_vertex = "Not read yet"
        draw_offset, draw_count, bone_count, unknown = struct.unpack("<IIII", f_in.read(16))
        vert_stream_count, index_size, index_count, vertex_count = struct.unpack("<IIII", f_in.read(16))
    print("Draw offset: {}\nDraw count: {}\nBone count: {}\nUnknown: 0x{:x}\nVertex Stream Count: {}\nIndex size: {}\nIndex count: {}\nVertex count: {}"
            .format(draw_offset, draw_count, bone_count, unknown, 
                vert_stream_count, index_size, index_count, vertex_count))
    
    vertices = [None] * vert_stream_count
    for i in range(vert_stream_count):
        print("Reading {} vertices...".format(vertex_count))
        vertices[i] = []
        if version == 4:
            bytes_per_vertex = struct.unpack("<I", f_in.read(4))[0]
        vertex_data = f_in.read(bytes_per_vertex * vertex_count)
        struct_format = "<" + "f" * int(bytes_per_vertex / 4)
        for vertex in struct.iter_unpack(struct_format, vertex_data):
            vertices[i].append(vertex)
        del vertex_data
    
    indices = []
    print("Reading {} indices...".format(index_count))
    index_data = f_in.read(index_size * index_count)

    for index_tuple in struct.iter_unpack("<H", index_data):
        indices.append(index_tuple[0])
    del index_data

    faces = []
    for i in range(0, len(indices), 3):
        faces.append((indices[i], indices[i+1], indices[i+2]))
    faces = numpy.array(faces)
    print("Created faces")
    vertex_array = numpy.array(vertices[0])
    stl_mesh = mesh.Mesh(numpy.zeros(faces.shape[0], dtype=mesh.Mesh.dtype))
    for i, f in enumerate(faces):
        for j in range(3):
            stl_mesh.vectors[i][j] = vertex_array[f[j], :]

    stl_mesh.save(output_file)
    f_in.close()
    print("Saved to {}".format(output_file))

main()
