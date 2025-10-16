"""Main Script: Goes through every drawing in the Working Folder and find the available revisions for that drawing
in the engineering directory. It then finds the most recent revision and copies it to the working folder"""

from pathlib import Path, WindowsPath, PosixPath
from StandardOSILib.osi_functions import osi_file_load, osi_file_store, sort_revisions, replace_file
from project_functions import get_available_dwg_revisions
from project_data import PROJDATA, PROJDIR

"""Load the tables of drawing nummbers in the working folder with their locations"""
build_table: dict[str, list[Path]] = osi_file_load(PROJDATA.FILE_TABLE)

for key in build_table: # Updates every drawings in the build table
    
    # Get latest drawing revision
    available_revisions = get_available_dwg_revisions(key)
    avail_rev_list = available_revisions.keys()         # Need to place keys into a list to sort
    avail_rev_list = sort_revisions(avail_rev_list)
    try:
        recent_dwg_rev = available_revisions[avail_rev_list[-1]]
    except KeyError:    # If a revision letter was capitalized by sort_revisions, a key error will throw
        print(f"Drawing {key}, All revisions should use capital letters, cannot update to desired revision until revision is fixed on drawings pdf")
    
    # Update each location the drawing is stored
    for value in build_table[key]:
        print(f"File {value} is being replaced with {recent_dwg_rev}")
        new_file = replace_file(recent_dwg_rev, value, PROJDIR.BACKUP)
        build_table[key][build_table[key].index(value)] = new_file
        print(new_file)
        
# Update Build Table
osi_file_store(build_table, PROJDATA.FILE_TABLE)