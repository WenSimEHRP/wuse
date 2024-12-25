# im too lazy to duplicate the sprites, so I wrote this
from roadtypes import road_enum, tram_enum
from PIL import Image
import glob
import os
png_files = []

keys = set(road_enum.enums.keys())
for key in keys.copy():
    if isinstance(key, (list, tuple, set, dict)):
        keys |= set(key)

for file in glob.glob("gfx/*.png"):
    name = file.split("/")[-1].split(".")[0]
    if name not in keys:
        continue
    print(name)
    png_files.append(file)

# ensure the folder exists
if not os.path.exists("gfx/p"):
    os.makedirs("gfx/p")

for file in png_files:
    with Image.open(file) as img:
        # split the sprites into chunks of 64, h
        # mirror the chunks and paste them on the bottom of the original image
        # save the image
        w, h = img.size
        new_img = Image.new('P', (w, h * 2))
        new_img.putpalette(img.getpalette())
        new_img.paste(img, (0, 0))

        for i in range(0, w, 64):
            chunk = img.crop((i, 0, i + 64, h))
            chunk = chunk.transpose(Image.FLIP_LEFT_RIGHT)
            new_img.paste(chunk, (i, h))

        # save in a new folder "p"
        new_img.save(f"gfx/p/{file.split('/')[-1]}")
