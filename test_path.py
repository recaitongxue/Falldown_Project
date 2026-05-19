import os

# 测试不同路径格式
paths = [
    r'd:\falldown\back\uploads\跌倒视频5.mp4',
    'd:\\falldown\\back\\uploads\\跌倒视频5.mp4',
    'd:/falldown/back/uploads/跌倒视频5.mp4',
]

for path in paths:
    exists = os.path.exists(path)
    print(f"Path: {path}")
    print(f"  Exists: {exists}")
    if exists:
        print(f"  Size: {os.path.getsize(path)} bytes")
    print()