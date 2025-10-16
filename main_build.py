"""Main Script: Walks through the directory and rebuilds a file table"""

from pathlib import Path, PosixPath, WindowsPath

from project_functions import get_drawings
from project_data import PROJDIR, PROJDATA
from StandardOSILib.osi_functions import osi_file_store, osi_file_load

if __name__ == '__main__':
    build_table: dict[str, list[Path|WindowsPath|PosixPath]] = get_drawings(PROJDIR.WORKING)
    osi_file_store(build_table, PROJDATA.FILE_TABLE)
    
    build_table = osi_file_load(PROJDATA.FILE_TABLE)
    for key in build_table.keys():
        print(f"{key} : {build_table[key]}")