from string import Template
from roadtypes import LabelEnums, road_enum, tram_enum
import glob

entry_format = Template("[$x * 64, $y * 31, 64 ,31 ,-31, 0, \"$path\"]")
entry_empty = "[]"

def complete_entry(path):
    a = [
        entry_format.substitute(x=0, y=0, path=path),
        entry_format.substitute(x=1, y=0, path=path),
        entry_format.substitute(x=2, y=0, path=path),
        entry_format.substitute(x=3, y=0, path=path),
        entry_format.substitute(x=4, y=0, path=path),
        entry_format.substitute(x=5, y=0, path=path),
        entry_format.substitute(x=6, y=0, path=path),
        entry_format.substitute(x=7, y=0, path=path),
    ]
    return a

with open("src/spriteset.pynml", "r") as f:
    data = f.read()

template_data = Template(data)

# construct the entries
# if the file doesn't exist, skip it
files = glob.glob("gfx/*.png")
# get basename
files = [f.split("/")[-1].split(".")[0] for f in files]
print(files)

temp_enums = {}
for key, val in road_enum.enums.copy().items():
    if isinstance(key, (list, tuple, set, dict)):
        temp_enums[key[0]] = val
    else:
        temp_enums[key] = val

roads = sorted(temp_enums.keys(), key=lambda x: temp_enums[x])
# construct the entries
entries = []
entries_len = len(complete_entry(""))
for road in roads:
    if road not in files:
        for i in range(entries_len):
            entries.append(entry_empty)
        continue
    for i in range(entries_len):
        entries.append(complete_entry(f"gfx/{road}.png")[i])

with open("src/spriteset.pnml", "w+") as f:
    f.write(template_data.substitute(entries="\n".join(entries)))
