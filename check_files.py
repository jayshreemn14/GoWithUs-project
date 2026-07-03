# check_files.py
import os

base = os.path.dirname(os.path.abspath(__file__))
static_images = os.path.join(base, "static", "images")

print("Project folder:", base)
print("Looking for:", static_images)
if os.path.isdir(static_images):
    files = os.listdir(static_images)
    print("static/images contains:", len(files), "files")
    for f in files:
        print(" -", f)
else:
    print("No static/images folder found.")
