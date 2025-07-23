import os
import sys


def check_thumb(file):
    exists = os.path.isfile(sys.argv[1])
    if exists:
        exit(0)
    else:
        exit(1)


if len(sys.argv) != 3 and len(sys.argv) != 2:
    print("TOO MANY/FEW ARGUMENTS")
    exit(1)

if len(sys.argv) == 2:
    check_thumb(sys.argv[1])

else:
    path = str(sys.argv[1])
    cache_path = str(sys.argv[2])

    filepaths = []
    current_dir = os.getcwd()

    wallpaper_files_path = os.path.join(current_dir, "wallpapers.txt")
    cache_files_path = os.path.join(current_dir, "cachefiles.txt")

    for root, dirs, files in os.walk(path):
        for name in files:
            filepaths.append(os.path.join(root, name))

    wallpaper_file = open(wallpaper_files_path, "w")
    for file in filepaths:
        wallpaper_file.write(file + "\n")

    wallpaper_file.close()

    cache_file = open(cache_files_path, "w")
    for file in filepaths:
        base = os.path.basename(file)
        noext = base.rsplit('.', 1)
        filename = noext[0] + ".png"
        full = os.path.join(cache_path, filename)
        cache_file.write(full + "\n")

    cache_file.close()
