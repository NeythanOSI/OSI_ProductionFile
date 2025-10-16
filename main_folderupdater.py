"""This script take the files in the updated drawings folder, and updates any drawings drawings in the
working folder to use those latest drawings."""

from pathlib import Path
from StandardOSILib.osi_functions import replace_file
from project_data import PROJDIR
from project_functions import get_drawings

src_drawings = get_drawings(PROJDIR.UPDATE_DRAWINGS)
for key in src_drawings.keys():
    if src_drawings[key].__len__() > 1:
        raise ValueError(f"Error: More than one drawing found for {key}, please remove duplicates")
dst_drawings = get_drawings(PROJDIR.CS_500)

for key in src_drawings.keys():
    
    if key in dst_drawings.keys():
        for value in dst_drawings[key]:
            print(f"Replacing {value} with {src_drawings[key]}")
            replace_file(src_drawings[key][0], value, PROJDIR.BACKUP)
    else:
        print(f"{key} not found in product folders, skipping...")




