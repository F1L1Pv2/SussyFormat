# SussyFormat
 simple 3d model format made with disk space in mind + blender plugin


### Format
```
[uint16 pos+normal count] [float32 * 3 (pos) + float32 * 3 (normal) ]
[uint16 uv count] [float32 * 2 uv] 
[uint16 triangles count] [(uint16 pos+normal ID + uint16 uv ID) * 3 (triangles have three points thats why x3)]
```

if you need more than 65535 vertices no problem just increase from uint16 to uint32 my project doesnt need much so thats what i did