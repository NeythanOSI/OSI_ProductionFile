"""Contains functions that will be useful across multiple OSI programs"""

from pathlib import Path, WindowsPath, PosixPath
from pickle import load, dump
from typing import Any
from shutil import copy, copy2
from os import rename
import re

from .osi_directory import PART_NUM_REGEX

def sort_revisions(revisions: list[str]) -> list[str]:
    """Take a list of OSI revisions in the form of strings, makes all alphabetical letters uppercase. Then sort
    to the following order 1. Revision with no letters come first, 2. Sorts alphabetically A-Z,
    3. Sorts alphabetical numerical revisions, in order of the letters A-Z, then numbers, 1 - etc. E.G. A, B1, B2, C, C1

    Args:
        revisions (list[str]): List that contains revision numbers in the form of python strings, Revision numbers
        should follow Oil Skimmers Inc standards.

    Returns:
        list[str]: Returns a sorted version of the input list. Note all lowercase alphabeticla letters are
        made uppercase in the returned list.
    """
    return sorted([rev.upper() for rev in revisions])

def osi_file_store(data: Any, file_path: Path|WindowsPath|PosixPath):
    """Store python data to a pickle file"""
    with open(file_path, "wb") as db:
        dump(data, db)

def osi_file_load(file_path: Path|WindowsPath|PosixPath):
    """Loads python data from a pickle file"""
    with open(file_path, "rb") as db:
        return load(db)
    
def replace_file(src: Path, dst: Path, backup: Path = None) -> Path:
    """Function replaces the file in the destination path with a copy from the source path
    that has the source files data, filename, and file metadata.

    Args:
        src (Path): Source file to copy to destination. Must be a file not a directory
        dst (Path): File that is replaced with the source file. WARNING!!! this file
        will be deleted permanently from the directory
        backup (Path): Directory that stores replaced files as a backup to retrieve

    Returns:
        Path: The new Path of the replaced file
    """
    # Verify Inputs
    if src.is_dir() or dst.is_dir():
        raise ValueError("Argument must be a file")
    if backup:  # Run if backup directory is supplied
        if not backup.is_dir():
            raise ValueError("Argument must be a directory")
    
    # Backup file before it is removed
    if backup:  # Run if backup directory is supplied
        copy(dst, backup)
    
    # Get new file name for os rename function
    src_file_name = src.name
    dst_file_path = dst.parent
    dst_rename = dst_file_path.joinpath(src_file_name)

    # Copy and Rename
    copy2(src, dst)     # Keeps metadata
    rename(dst, dst_rename)
    
    return dst_rename   # Returns new file path if needed

def osi_get_prefix(drawing: str) -> str:
    """Takes a pdf of a engineering drawings in the form of a string and returns the prefix of the drawing number

    Args:
        drawing (str): drawing number

    Returns:
        str: Returns the prefix, if the drawing number is not in the OSI Part Number Regex, then the
        function will return None for error handling
    """
    try:
        drawing_number = re.search(PART_NUM_REGEX, drawing).group(0)
        return drawing_number[:drawing_number.find("-")]
    except AttributeError:
        return None