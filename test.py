import ttkbootstrap as tk
from ttkbootstrap.dialogs import Messagebox
from enum import IntEnum
from project_functions import EcnFile, get_ecn, read_ecn_changes, EcnChange, get_drawings, get_dwg_number_rev
from StandardOSILib.osi_directory import OSIDIR
from project_data import PROJDIR, PROJDATA
from StandardOSILib.osi_functions import osi_file_load, osi_file_store, replace_file
from shutil import copy
from os import scandir, listdir, mkdir
import webbrowser
from pathlib import Path
from dataclasses import dataclass
from typing import NamedTuple

class OsiFolder():
    """ Data and Functions to navigate through OSI file directories """
    
    class FolderType(IntEnum):
        EMPTY = 0
        FOLDER = 1
        FILES = 2
        MIX = 3
        
    class FolderChild(NamedTuple):
        fpath: Path
        fname: str
        fsuffix: str
        ftype: int
        
    def _check_dir_empty(self) -> bool:
        """Error Checking Function: Verify that root folder is an empty folder

        Returns:
            bool: Returns True if folder contains is empty, Returns False if files or folders are present
        """
        if self.children.__len__() == 0:
            return True
        else:
            return False
    
    def _check_directory(self) -> bool:
        """Error Checking Function: Verify that root folder contains only folders

        Returns:
            bool: Returns True if folder contains only directories, Returns False if files are present
        """
        for child in self.children:
            if child.fpath.is_dir():
                continue
            else:
                return False
        return True
    
    def _check_no_children(self, selection):
        """Error Checking Function: Verify that selected folder is empty

        Returns:
            bool: Returns True if folder does not contain children, Returns False if children are present,
             or if there is error
        """
        folder_path = self.children[selection].fpath
        try:
            if len(listdir(folder_path)) == 0:
                return True
            else:
                return False
        except:
            return False
    
    def _scan_folder(self):
        """ Scans the root directory and find all documents contained """
        # Need to clear the data
        self.children.clear()
        
        # Get each entry in the root directory, path, name, and type
        with scandir(self.root) as dir:
            child_temp: dict[str, OsiFolder.FolderChild] = dict()
            for file in dir:
                file_path = Path(file.path)
                file_name = file_path.name
                file_suffix = file_path.suffix
                
                # Folders dont have a suffic
                if file_suffix == "":
                    file_suffix = "Folder"
                    file_type = self.FolderType.FOLDER
                else:
                    file_type = self.FolderType.FILES
                    
                child_temp[file_name] = self.FolderChild(file_path, file_name, file_suffix, file_type)
        
        # Sort the keys be alphabetic / numerical order and append to the children list
        sorted_keys = sorted(child_temp.keys())
        for key in sorted_keys:
            self.children.append(child_temp[key])
            
        # Determine if the folder is empty
        if self.children.__len__() == 0:
            self.type = self.FolderType.EMPTY
            return
        
        # Determine if the folder contains folder or file or both
        contains_dir = False
        contains_file = False
        
        for child in self.children:
            if child.fpath.is_dir():
                contains_dir = True
            else:
                contains_file = True
                
        if contains_dir and contains_file:
            self.type = self.FolderType.MIX
            return
        if contains_dir:
            self.type = self.FolderType.FOLDER
        if contains_file:
            self.type = self.FolderType.FOLDER
    
    def enter_folder(self, selection):
        child = self.children[selection]
        if child.ftype != self.FolderType.FOLDER:
            return
        self.root = child.fpath
        self._scan_folder()
    
    def _prev_folder(self):
        """Return to the parent folder of the current root directory, limits to the production drawings folder"""
        if self.root == self.start_path:    # don't let user out of the scope of the program
            return
        self.root = self.root.parent
        self._scan_folder()
    
    def _delete_selection(self, selection):
        file_path: Path = self.children[selection].fpath
        file_type: int = self.children[selection].ftype
        
        if file_type == self.FolderType.FOLDER:
            if not self._check_no_children(selection):
                print(f"attempted delete of {file_path} cannot delete folder with children")
                Messagebox.ok("cannot delete folder with children")
                return
            if Messagebox.yesno("are you sure, this will permenantly deletes the folder") == "No":
                print(f"user canceled delete of {file_path}")
                return
            file_path.rmdir()
            print(f"removed folder {file_path}")
        elif file_type == self.FolderType.FILES:
            if Messagebox.yesno("are you sure, this will permenantly deletes the file") == 'No':
                print(f"user canceled delete of {file_path}")
                return
            file_path.unlink()
            print(f"removed file {file_path}")
        else:
            return
        
        self._scan_folder()        
    
    def _insert_folder(self, folder_name):
        folder = self.root.joinpath(folder_name)
        mkdir(folder)
    
    def _insert_file(self, file_path):
        copy(src=file_path, dst=self.root)
    
    def __init__(self, start_path: Path = Path(r"X:")):
        self.start_path = start_path
        self.root = start_path
        self.children: list[OsiFolder.FolderChild] = list()    # String is the File Name in the FolderChild object
        self.type = None
        self._scan_folder()

def change_index(file_name: str, change: int):
    """Takes a file name with an index in the format "index-dwg_number-etc" and updates it by the change value.

        Args:
            file_name (str): The file name to change the index of. Index must be integers at the start of the file name.
            change (int): The integer to change the index by. Negative numbers decriment, Positive numbers incriment

        Returns:
            str: The file name with the updated index in the format it was given
    """
    # Get the ammount of numbers that make up the index, This assumes the index is a numberical number at the start
    for i in range(file_name.__len__()):
        try:
            int(file_name[i])
        except ValueError:
            break
    
    drawing = file_name[i:]
    index = str(int(file_name[:i]) + change)
    
    # Index must keep the same number of integers, 000 -> 001, 0002 -> 0001 etc
    for j in range(i - index.__len__()):
        index = str(0) + index
        
    return index + drawing

def serialize_files(directory: OsiFolder, selection: int, inc_selection: bool, change: int):
    for i in range(selection, directory.children.__len__()):
        if not inc_selection:       # Skip first iteration to avoid updating selected file
            inc_selection = True    # Stops this section from looping
            continue
        
        # Index the child by the change and create a new path for renaming the file
        child = directory.children[i]
        file_name = change_index(child.fname, change)
        file_path = child.fpath.parent.joinpath(file_name)
        
        # Update the child
        child.fpath.rename(file_path)
        directory.children[selection] = directory.FolderChild(file_path, file_name, child.fsuffix, child.ftype)
        
        
    # Do a refresh
    directory._scan_folder()