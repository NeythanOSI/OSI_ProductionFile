"""Script for testing feasibility of adding automated drawing revision control to production folders
    Author: NNP"""
    
# Imports
from os import walk, scandir
from pathlib import Path, WindowsPath, PosixPath
import re
from dataclasses import dataclass

from StandardOSILib.osi_functions import osi_get_prefix
from StandardOSILib.osi_directory import PART_NUM_REGEX, OSIDIR
from StandardOSILib.osi_directory_append import PREFIX_LOOKUP_TABLE
from project_data import PROJDATA, PROJDIR

import openpyxl

def get_dwg_number_rev(file: Path|WindowsPath|PosixPath) -> tuple[str|None]:
    """Take a Pathlib Path to a drawing PDF and returns the drawing number and revision.

    Args:
        file (Path | WindowsPath | PosixPath): Pathlib Path to the drawing PDF

    Returns:
        tuple[str|None]: Returns a tuple with two strings, the first one is the drawing number, the second is the revision.
        If the drawing number is not recognised, returns None
    """
    name = file.stem
    try:
        dwg = re.search(PART_NUM_REGEX, name).group(0)
    except AttributeError:
        return None
    rev_unparsed = re.sub(PART_NUM_REGEX, "", name)
    rev_start = rev_unparsed.rfind("-")
    rev = rev_unparsed[rev_start+1:]
    return dwg, rev

def get_drawings(Folder: Path|WindowsPath|PosixPath) -> dict[str, list[str]]:
    """Walks through the directory and all subfolders of that directory and returns a dictionary containing
    all Pathlib Paths where the drawings are found using the drawing number as a key.

    Args:
        Folder (Path | WindowsPath | PosixPath): Directory that is walked

    Returns:
        dict[str, list[str]]: Dictionary, Key is a string that is the drawing number. Value is a list of
        Pathlib Paths where each copy of the drawing is found.
    """
    build_table: dict[str, list[Path|WindowsPath|PosixPath]] = dict()
    for (root, dirs, files) in walk(Folder, True):
        for file in files:
            if file == "":                            # Check for directory with no files
                continue
            dwg_number_rev = get_dwg_number_rev(Path(file))
            if dwg_number_rev is None:                       # Check for valid drawing number
                continue
            dwg_number = dwg_number_rev[0]
            
            if dwg_number not in build_table:
                build_table[dwg_number] = [Path(root).joinpath(file)]
            else:
                build_table[dwg_number].append(Path(root).joinpath(file))
    return build_table
          
def get_available_dwg_revisions(dwg: str) -> dict[str, Path|WindowsPath|PosixPath]:
    
    # Set up variables
    available_revision: dict[str, Path] = dict()
    # Find the appropraite directory
    directory = PREFIX_LOOKUP_TABLE[osi_get_prefix(dwg)]
    
    # Find all matching files
    with scandir(directory) as dir:
        for i, file in enumerate(dir):
            if not re.search(dwg, file.name):                   # Check for no returns
                continue
            if not file.name[file.name.__len__()-4:] == ".pdf": # Check for pdfs
                continue
            rev = get_dwg_number_rev(Path(file.path))[1]  # Find Revision
            if rev == "":                       # Remove Blank Revisions
                continue
            available_revision[rev] = Path(file.path)
    return available_revision

@dataclass
class EcnFile():
    ecn_name: str
    ecn_folder: Path
    ecn_drawings: Path
    ecn_file: Path

def get_ecn(ecn_number: str) -> EcnFile:
    ecn_name = "ECN-" + ecn_number
    ecn_folder = None
    
    with scandir(OSIDIR.ECN_FOLDER) as dir:
        for file in dir:
            if file.name == ecn_name:
                ecn_folder = Path(file.path)
                break
            
    if ecn_folder == None:
        raise FileNotFoundError(f"ECN: {ecn_name} does not have a folder in the location {OSIDIR.ECN_FOLDER}")
    ecn_drawings = ecn_folder.joinpath("Updated Drawings")
    
    if not ecn_drawings.exists():
        raise FileNotFoundError(f"Location: {ecn_folder} does not contain the following folder: Updated Drawings")
    ecn_file = ecn_folder.joinpath(ecn_name + ".xlsx")
    if not ecn_file.exists():
        raise FileNotFoundError(f"Location: {ecn_folder} does not contain an excel ecn file")
    
    return (EcnFile(ecn_name, ecn_folder, ecn_drawings, ecn_file))

@dataclass
class EcnChange():
    level: int
    dwg_number: str
    new_revision: str
    disposition: str

@dataclass
class FM00037():
    SHEET: str              = "Bill of Materials"
    DWGS_FIRST_COL: int     = 0  # Column A = 0
    DWGS_LAST_COL: int      = 7  # Reference Column A = 0
    DWGS_FIRST_ROW: int     = 4  # First row with the parent drawings in an ecn
    REV_COL: int            = 11 # Column Containing Revision
    DISPOSITION_COL: int    = 12 # Column Containing Disposition

def read_ecn_changes(ecn: Path) -> list[EcnChange]:
    wb = openpyxl.load_workbook(ecn, data_only=True)
    ws = wb[FM00037.SHEET]
    ecn_changes: list[EcnChange] = list()
    
    for row in ws.iter_rows(min_row=FM00037.DWGS_FIRST_ROW, values_only=True):

        empty_row = True
        for i, value in enumerate(row[FM00037.DWGS_FIRST_COL:FM00037.DWGS_LAST_COL+1]):
            if value == None or value == "":
                continue
            else:
                empty_row = False
                break
            
        if empty_row == True:
            continue
        if row[FM00037.DISPOSITION_COL] == "Old Product":
            continue
        
        try:    # Try except for integer revisions
            new_revision = row[FM00037.REV_COL].lstrip("-")
        except AttributeError:
            new_revision = row[FM00037.REV_COL]
        
        ecn_changes.append(EcnChange(i, value, new_revision, row[FM00037.DISPOSITION_COL]))

    return ecn_changes
    
    
