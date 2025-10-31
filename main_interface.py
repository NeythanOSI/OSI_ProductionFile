import ttkbootstrap as tk
from ttkbootstrap.dialogs import Messagebox, Querybox
from tkinter.filedialog import askopenfilename
import openpyxl

from enum import IntEnum
from dataclasses import dataclass
from typing import NamedTuple
from pathlib import Path
from shutil import copy
from os import scandir, listdir, mkdir, walk
import webbrowser

from project_functions import read_ecn_changes, get_dwg_number_rev
from StandardOSILib.osi_directory import OSIDIR
from project_data import PROJDIR, PROJDATA
from StandardOSILib.osi_functions import osi_file_load, osi_file_store, replace_file

""" Notes about the code base
    Author:
        Neythan P, 216-904-2378
    Data Published:
        Development
    Purpose: 
        Production drive has drawings indexed to make build instructions,
        See every location of a specific drawing
        Update drawings to new revisions at the click of a button
        Add new drawings and remove drawings from the production drive
        Add new folders and delete folders to organise work instructions
    Notes on the Code Base:
        1.  Data with methods specific to only that data are stored in classes at the top of the file
                E.G. ECN Data, methods to read ecn files, and its state is the data found in that file
                E.G. OsiFolder, methods for reading and creating folders, and its state is the data of the active folder
        2.  Each graphical ui element frame and treeview is its own object
                E.G. _DrawingViewTree, All lines of code to make the ui are contained in the class
        3.  Functions that are not specific to one set of data are in the global scope
                E.G. insert file alters the file table and the osi directory
        4.  If a function has paremeters, and is called by a button press, the function is reimplimented
                inside the object that uses it, becuase tkinter buttons cannot supply parameters
                E.G. _insert_file is implimented in the _FilePanel, The _FilePanel object supplies the parameters
                        and puts it in a method for the button to be able to call it"""
    

def open_pdf(self, file: Path):
    """Opens a pdf of the selected file"""
    if file.suffix == ".pdf" or file.suffix == ".PDF" or file.suffix == ".Pdf":
        webbrowser.open_new(file)

@dataclass
class OsiFile():
    file_path: Path
    file_name: str
    file_type: str

class OsiFolder():
    """ Collection of data and functions to handle folders and their files in the OSI directory """
    
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
    
    def enter_folder(self):
        child = self.children[self.selection]
        if child.ftype != self.FolderType.FOLDER:
            return
        self.root = child.fpath
        self._scan_folder()
    
    def prev_folder(self):
        """Return to the parent folder of the current root directory, limits to the production drawings folder"""
        if self.root == self.start_path:    # don't let user out of the scope of the program
            return
        self.root = self.root.parent
        self._scan_folder()
    
    def _insert_folder(self):
        folder_name = Querybox.get_string("Type Folder Name")
        if type(folder_name) == None:
            return
        folder = self.root.joinpath(folder_name)
        try:
            mkdir(folder)
        except FileExistsError:
            Messagebox.ok("file already exists")
            return
        except FileNotFoundError:
            Messagebox.ok("an error occured")
            return
        self._scan_folder()
    
    def __init__(self, start_path: Path = Path(r"X:")):
        self.start_path = start_path
        self.root = start_path
        self.children: list[OsiFolder.FolderChild] = list()    # String is the File Name in the FolderChild object
        self.selection = None
        self.type = None
        self._scan_folder()

class FileTable():
    """ Collection of data and functions to handle where production drawings are stored """
    
    def _get_drawings(self, Folder: Path) -> dict[str, list[Path]]:
        """Walks through the directory and all subfolders of that directory and returns a dictionary containing
        all Pathlib Paths where the drawings are found using the drawing number as a key.

        Args:
            Folder (Path | WindowsPath | PosixPath): Directory that is walked

        Returns:
            dict[str, list[str]]: Dictionary, Key is a string that is the drawing number. Value is a list of
            Pathlib Paths where each copy of the drawing is found.
        """
        build_table: dict[str, list[Path]] = dict()
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
        
    def update_file_table(self, key: str, old_path: Path, new_path: Path = None):
        """Updates the file table

        Args:
            file_table (dict[str, list[Path]]): A dictionary using drawing names as keys, for a list of Paths
            key (str): The drawing name
            old_path (Path): The path to change or remove
            new_path (Path, optional): Replaces the old path with the new one if supplied. Defaults to None.
        """
        index = self.file_table[key].index(old_path)
        self.file_table[key].pop(index)
        if new_path != None:
            self.file_table[key].append(new_path)
            
    def add_file_table_entry(self, key: str, new_path: Path = None):
        if key in self.file_table.keys():
            self.file_table[key].append(new_path)
        else:
            self.file_table[key] = [new_path]

    def get_file_paths(self, drawing: str) -> list[str, Path]:
        entries = list()
        for entry in self.file_table[drawing]:
            entries.append((None, entry))
        return entries

    def __init__(self, drive_root: Path):
        self.file_table: dict[str, list[Path]] = self._get_drawings(drive_root)

def get_index_length(file_name: str):
    # Get the ammount of numbers that make up the index, This assumes the index is a numberical number at the start
    for i in range(file_name.__len__()):
        try:
            int(file_name[i])
        except ValueError:
            break
    return i

def change_index(file_name: str, change: int):
    """Takes a file name with an index in the format "index-dwg_number-etc" and updates it by the change value.

        Args:
            file_name (str): The file name to change the index of. Index must be integers at the start of the file name.
            change (int): The integer to change the index by. Negative numbers decriment, Positive numbers incriment

        Returns:
            str: The file name with the updated index in the format it was given
    """
    # Get the ammount of numbers that make up the index, This assumes the index is a numberical number at the start
    i = get_index_length(file_name)
    
    drawing = file_name[i:]
    index = str(int(file_name[:i]) + change)
    
    # Index must keep the same number of integers, 000 -> 001, 0002 -> 0001 etc
    for j in range(i - index.__len__()):
        index = str(0) + index
        
    return index + drawing

def serialize_files(directory: OsiFolder, file_table: FileTable, inc_selection: bool, change: int):
    old_children = list()
    new_children = list()
    for i in range(directory.selection, directory.children.__len__()):
        if not inc_selection:       # Skip first iteration to avoid updating selected file
            inc_selection = True    # Stops this section from looping
            continue
        
        # Index the child by the change and create a new path for renaming the file
        child = directory.children[i]
        old_children.append((get_dwg_number_rev(child.fpath)[0], child.fpath))  # Save data for updating the file_table
        file_name = change_index(child.fname, change)
        file_path = child.fpath.parent.joinpath(file_name)
        new_children.append(file_path)  # Keep track for updating file_table
        
        # Update the child
        child.fpath.rename(file_path)
        directory.children[directory.selection] = directory.FolderChild(file_path, file_name, child.fsuffix, child.ftype)
        
    # Update the build table
    for i, child in enumerate(old_children):
        file_table.update_file_table(child[0], child[1], new_children[i])
        
    # Do a refresh
    directory._scan_folder()

def _insert_file(directory: OsiFolder, file_table: FileTable, above: bool = True):
    
    file_path = Path(askopenfilename(initialdir="X:"))
    if file_path.name == "":
        return
    
    if above:
        # Get the selected files index
        selection_name = directory.children[directory.selection].fname
        i = get_index_length(selection_name)+1
        index = selection_name[:i]
        
        # Serialize up selected file and its below files
        serialize_files(directory, file_table, True, 1)
    else:
        # Get the selected files index and incriment
        selection_name = directory.children[directory.selection].fname
        i = get_index_length(selection_name)+1
        index = selection_name[:i]
        index = change_index(index, 1)
        
        # Serialize up below files
        serialize_files(directory, file_table, False, 1)
        
    # Filling below, means stealing the below selected, and indexing below selected
    file_path = Path(copy(src=file_path, dst=directory.root))
    file_path_new = file_path.parent.joinpath(index + file_path.name)
    file_path = file_path.rename(file_path_new)
    
    # Add to File Table
    file_table.add_file_table_entry(get_dwg_number_rev(file_path)[0], file_path)
        
    # Updates
    directory._scan_folder()

def _delete_selection(directory: OsiFolder, file_table: FileTable):
    
    def _check_dir_empty() -> bool:
        """Returns: Returns True if folder contains is empty, Returns False if files or folders are present"""
        if directory.children.__len__() == 0:
            return True
        else:
            return False
    def _check_directory() -> bool:
        """Returns: Returns True if folder contains only directories, Returns False if files are present"""
        for child in directory.children:
            if child.fpath.is_dir():
                continue
            else:
                return False
        return True
    def _check_no_children(selection) -> bool:
        """Returns: Returns True if folder does not contain children, Returns False if children are present,
            or if there is error"""
        folder_path = directory.children[selection].fpath
        try:
            if len(listdir(folder_path)) == 0:
                return True
            else:
                return False
        except:
            return False
        
    file_path: Path = directory.children[directory.selection].fpath
    file_type: int = directory.children[directory.selection].ftype
    
    if file_type == OsiFolder.FolderType.FOLDER:
        # Code to run for deleting folders
        if not _check_no_children(directory.selection):
            print(f"attempted delete of {file_path} cannot delete folder with children")
            Messagebox.ok("cannot delete folder with children")
            return
        if Messagebox.yesno("are you sure, this will permenantly deletes the folder") != "Yes":
            print(f"user canceled delete of {file_path}")
            return
        file_path.rmdir()            
        print(f"removed folder {file_path}")
    elif file_type == OsiFolder.FolderType.FILES:
        # Code to run for deleting files
        if Messagebox.yesno("are you sure, this will permenantly deletes the file") != 'Yes':
            print(f"user canceled delete of {file_path}")
            return

        serialize_files(directory, file_table, False, -1)
        file_table.update_file_table(get_dwg_number_rev(file_path)[0], file_path)
        file_path.unlink()
        print(f"removed file {file_path}")
    else:
        return

    directory._scan_folder()

def _update_drawings(file_table: FileTable, dwg_path: Path):
    dwg_number = get_dwg_number_rev(dwg_path)[0]
    
    for file_path in file_table.file_table[dwg_number]:
        # Get index of the file being replaced
        file_name = file_path.name
        ind_length = get_index_length(file_name)+1
        index = file_name[:ind_length]
        
        # Replace file and change name to include index
        new_file = replace_file(dwg_path, file_path, PROJDIR.BACKUP)
        rename_file = new_file.parent.joinpath(index + new_file.name)
        new_file = new_file.rename(rename_file)
        
        # Update Build Table
        file_table.file_table[dwg_number][file_table.file_table[dwg_number].index(file_path)] = new_file

class EcnFileManager():
    
    class EcnFile(NamedTuple):
        ecn_name: str
        ecn_folder: Path
        ecn_drawings: Path
        ecn_file: Path
        
    class EcnChange(NamedTuple):
        level: int
        dwg_number: str
        new_revision: str
        disposition: str
    
    def get_ecn(self, ecn_number: str) -> EcnFile:
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
        
        self.ecn_file = self.EcnFile(ecn_name, ecn_folder, ecn_drawings, ecn_file)
    
    def read_ecn_changes(self):
    
        @dataclass
        class FM00037():
            SHEET: str              = "Bill of Materials"
            DWGS_FIRST_COL: int     = 0  # Column A = 0
            DWGS_LAST_COL: int      = 7  # Reference Column A = 0
            DWGS_FIRST_ROW: int     = 4  # First row with the parent drawings in an ecn
            REV_COL: int            = 11 # Column Containing Revision
            DISPOSITION_COL: int    = 12 # Column Containing Disposition
        
        wb = openpyxl.load_workbook(self.ecn_file, data_only=True)
        ws = wb[FM00037.SHEET]
        ecn_changes: list[EcnFileManager.EcnChange] = list()
        
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
            
            ecn_changes.append(self.EcnChange(i, value, new_revision, row[FM00037.DISPOSITION_COL]))

        self.ecn_changes = ecn_changes
    
    def find_drawings(self):
        self.drawings.clear()
        error_list: list[str] = list()
        for i, change in enumerate(self.ecn_changes):
            if change.disposition != "Running Change":
                continue
            drawing = self.ecn_file.ecn_drawings.joinpath(change.dwg_number + '-' + change.new_revision + '.pdf')
            if not drawing.exists():
                error_list.append(drawing.name)
                continue
            self.drawings[i] = drawing
    
    def __init__(self):
        self.ecn_file: EcnFileManager.EcnFile = None
        self.ecn_changes: list[EcnFileManager.EcnChange] = None
        self.drawings: dict[int, Path] = dict()

class Root(tk.Window):
    def __init__(self):
        super().__init__(themename='darkly')
        self.title("OSI Engineering File Manager")
        self.geometry("1200x750")
        
        self.menubar = tk.Menu(self)
        self.config(menu=self.menubar)
        self.modeSelectionMenu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label='MODE', menu=self.modeSelectionMenu)
                
        self.actionsFrame = tk.Frame(self)
        self.actionsFrame.pack(side='top')
        
class _DrawingViewTree(tk.Treeview):
    
    TREE_HEADERS = ("Product Family", "File Locations")
    
    def populate_tree(self, entries: tuple[str]):
        for i, entry in enumerate(entries):
            self.insert("", 'end', iid=i, values=entry)
    
    def __init__(self, master):
        
        # Create Product Tree
        tk.Treeview.__init__(self, master=master, bootstyle='default', columns=self.TREE_HEADERS, show='headings', height=25)
        self.heading(self.TREE_HEADERS[0], text="Product Family", anchor='w')
        self.heading(self.TREE_HEADERS[1], text="File Locations", anchor='w')
        self.column(self.TREE_HEADERS[0], stretch=False, width=200, anchor='w')
        self.column(self.TREE_HEADERS[1], stretch=False, width=700, anchor='w')
        
class _FileTree(tk.Treeview):
    
    TREE_HEADERS = ("File Type", "File Name")
    
    def clear_tree(self):
        for i, child in enumerate(self.get_children()):
            self.delete(i)
    
    def populate_tree(self, entries: tuple[str]):
        for i, entry in enumerate(entries):
            self.insert("", 'end', iid=i, values=entry)
    
    def return_selection(self):
        # Try Statement blocks errors if nothing is selected
        try:
            return int(self.focus())
        except ValueError:
            return None
    
    def __init__(self, master):
        # Create Tree
        tk.Treeview.__init__(self, master=master, bootstyle='default', columns=self.TREE_HEADERS, show='headings', height=25)
        self.heading(self.TREE_HEADERS[0], text="File Type", anchor='center')
        self.heading(self.TREE_HEADERS[1], text="File Name", anchor='w')
        self.column(self.TREE_HEADERS[0], stretch=False, width=100, anchor='center')
        self.column(self.TREE_HEADERS[1], stretch=False, width=300, anchor='w')
 
class _FilePanel(tk.Frame):
    
    def _clear_frame(self):
        for child in self.winfo_children():
            child.pack_forget()
            
    def refresh(self, mode: int):
        """Refresh Panel Functions

        Args:
            mode (int): an integer that controls command to display\n
            0: Empty Folder, Displays Insert Above, Insert Folder, Prev Folder, Done if applicable\n
            1: Folders, Displays Insert Folder, Delete, Enter Folder, Prev Folder, Done if appliable\n
            2: Files, Displays Insert Above, Insert Below, Delete, Enter Folder, Prev Folder, Open PDF,
             Done if applicable
        """
        self._clear_frame()
        if mode == 0 or mode == 2:
            self.cmd_iabove_button.pack(padx=5, pady=5, side='top')
        if mode == 0 or mode == 2:
            self.cmd_ibelow_button.pack(padx=5, pady=5, side='top')
        if mode == 0 or mode == 1:
            self.cmd_ifolder_button.pack(padx=5, pady=5, side='top')
        if mode == 1 or mode == 2:
            self.cmd_delete_button.pack(padx=5, pady=5, side='top')
        if mode == 1 or mode == 2:
            self.cmd_enterfol_button.pack(padx=5, pady=5, side='top')
        self.cmd_prevfol_button.pack(padx=5, pady=5, side='top')
        if mode == 2:
            self.cmd_openpdf_button.pack(padx=5, pady=5, side='top')
        if self.done_button:
            self.cmd_done_button.pack(padx=5, pady=5, side='top')
    
    def __init__(self, master, mode: int, osi_folder: OsiFolder, file_table: FileTable, return_cmd = None):
        """Create a panel of functions for the _FileTree view

        Args:
            master (_type_): tkinter frame master
            mode (int): an integer that controls command to display\n
            0: Empty Folder, Displays Insert Above, Insert Folder, Prev Folder, Done if applicable\n
            1: Folders, Displays Insert Folder, Delete, Enter Folder, Prev Folder, Done if appliable\n
            2: Files, Displays Insert Above, Insert Below, Delete, Enter Folder, Prev Folder, Open PDF,
             Done if applicable
            file_functions (list): A list of functions each button will command,\n
             if None is supplied as the last function (return function), the return button will not appear
        """
        def _insert_above():
            _insert_file(osi_folder, file_table, True)
            
        def _insert_below():
            _insert_file(osi_folder, file_table, False)
        
        def _delete():
            _delete_selection(osi_folder, file_table)
        
        tk.Frame.__init__(self, master)
        self.cmd_iabove_button = tk.Button(master=self, text="Insert Above", width = 15, command=_insert_file)
        self.cmd_ibelow_button = tk.Button(master=self, text="Insert Below", width = 15, command=_insert_below[1])
        self.cmd_ifolder_button = tk.Button(master=self, text="Insert Folder", width = 15, command=osi_folder._insert_folder)
        self.cmd_delete_button = tk.Button(master=self, text="Delete Selected", width = 15, command=file_functions[3])
        self.cmd_enterfol_button = tk.Button(master=self, text="Enter Folder", width=15, command=osi_folder.enter_folder)
        self.cmd_prevfol_button = tk.Button(master=self, text="Previous Folder", width=15, command=osi_folder.prev_folder)
        self.cmd_openpdf_button = tk.Button(master=self, text="Open PDF", width=15, command=open_pdf)
        self.done_button = False
        if return_cmd != None:
            self.cmd_done_button = tk.Button(master=self, text="Done", width=15, command=return_cmd)
            self.done_button = True
        self.refresh(mode)
        
class _EcnTree(tk.Treeview):
    
    TREE_HEADERS = ("Level", "Drawing Number", "New Revision", "Disposition")
    
    def populate_tree(self, entries: list[tuple[str]]):
        for i, entry in enumerate(entries):
            self.insert("", 'end', iid=i, values=entry)
            
    def return_selection(self):
        # Try Statement blocks errors if nothing is selected
        try:
            return int(self.focus())
        except ValueError:
            return None
    
    def __init__(self, master, ecn_manager: EcnFileManager):
        # Link in Data
        self.ecn_data = ecn_manager
        # Create Tree
        tk.Treeview.__init__(self, master=master, bootstyle='default', columns=self.TREE_HEADERS, show='headings', height=25)
        self.heading(self.TREE_HEADERS[0], text="Level", anchor='center')
        self.heading(self.TREE_HEADERS[1], text="Drawing Number", anchor='w')
        self.heading(self.TREE_HEADERS[2], text="New Revision", anchor='center')
        self.heading(self.TREE_HEADERS[3], text="Disposition", anchor='w')
        self.column(self.TREE_HEADERS[0], stretch=False, width=60, anchor='center')
        self.column(self.TREE_HEADERS[1], stretch=False, width=120, anchor='w')
        self.column(self.TREE_HEADERS[2], stretch=False, width=120, anchor='center')
        self.column(self.TREE_HEADERS[3], stretch=False, width=150, anchor='w')

class _EcnPanel(tk.Frame):
    def __init__(self, master, ecn_manager: EcnFileManager):
        # Link in Data
        self.ecn_data = ecn_manager
        # Create Frame
        tk.Frame.__init__(self, master)
        # Button Approve
        cmd_push_rev_button = tk.Button(master=self, text="Push Revision", width = 15, command=ecn_functions[0])
        cmd_push_rev_button.grid(row=0, column=0, padx=5, pady=5, sticky='nswe')
        # Button See Location
        cmd_setloc_button = tk.Button(master=self, text="See Location", width = 15, command=ecn_functions[1])
        cmd_setloc_button.grid(row=1, column=0, padx=5, pady=5, sticky='nswe')
        # Button Cancel
        cmd_return_button = tk.Button(master=self, text="Return", width = 15, command=ecn_functions[2])
        cmd_return_button.grid(row=3, column=0, padx=5, pady=5, sticky='nswe')  
           
class _ActionWindow(tk.Frame):
    
    def __init__(self, master, cmd_view, cmd_ecn):
        tk.Frame.__init__(self, master)
        
        # View Drawing
        cmd_viewdrawing_button = tk.Button(master=self, text="View Drawing", width=20, command=cmd_view)
        cmd_viewdrawing_button.grid(row=0, column=0, padx=5, pady=5, sticky='nswe')
        self.cmd_viewdrawing_var = tk.StringVar()
        cmd_viewdrawing_entry = tk.Entry(master=self, textvariable=self.cmd_viewdrawing_var, width=20)
        cmd_viewdrawing_entry.grid(row=0, column=1, padx=5, pady=5, sticky='nswe')
        
        # Upload Engineering Change Notice
        cmd_uploadecn_button = tk.Button(master=self, text="Upload ECN", width=20, command=cmd_ecn)
        cmd_uploadecn_button.grid(row=1, column=0, padx=5, pady=5, sticky='nswe')
        self.cmd_uploadecn_var = tk.StringVar()
        cmd_uploadecn_entry = tk.Entry(master=self, textvariable=self.cmd_uploadecn_var, width=20)
        cmd_uploadecn_entry.grid(row=1, column=1, padx=5, pady=5, sticky='nswe')
        
class _DrawingViewWindow(tk.Frame):
    
    def __init__(self, master, file_paths, return_cmd):
        tk.Frame.__init__(self, master)
        
        # Widgets
        drawing_view_frame = _DrawingViewTree(self)
        drawing_view_frame.grid(row=0, column=0, padx=5, pady=5, sticky='nswe')
        # Button to Return
        cmd_return_button = tk.Button(self, text="Done", command=return_cmd)
        cmd_return_button.grid(row=1, column=0, padx=5, pady=5, sticky='nswe')
        
        drawing_view_frame.populate_tree(file_paths)
        
        # Populate Tree with Drawing Locations
        """
        entries = list()
        try:
            for entry in build_table[drawing]:
                entries.append((None, entry))
        except KeyError:
            pass
        """ 

class _EcnWindow(tk.Frame):
        
    def _clear_window(self):
        for widget in self.winfo_children():
            widget.destroy()
    
    def populate_tree(self):
        # Populate Tree
        ecn_change_list = list()
        for change in self.ecn_changes:
            ecn_change_list.append(
                (
                    change.level,
                    change.dwg_number,
                    change.new_revision,
                    change.disposition,
                ))
        self.ecn_tree.populate_tree(ecn_change_list)
    
    def _launch_action_window(self):
        self._clear_window()
        self.ecn_tree = _EcnTree(self)
        self.ecn_tree.grid(row=0, column=1, padx=5, pady=5, sticky='nswe')
        self.ecn_panel = _EcnPanel(self, self.ECN_PANEL_FUNCTIONS)
        self.ecn_panel.grid(row=0, column=0, padx=5, pady=5, sticky='nswe')
        #self.file_window = _FileWindow(self, self.build_table, self.ecn_file, None)
        self.file_window.grid(row=0, column=2, padx=5, pady=5, sticky='nswe')
        self.populate_tree()
        
    def _launch_dwg_view_window(self):
        selection = self.ecn_tree.return_selection()
        if selection == None:
            return
        self._clear_window()
        dwg_number = self.ecn_changes[selection].dwg_number
        window = _DrawingViewWindow(self, self.build_table, dwg_number, self._launch_action_window)
        window.grid(row=0, column=0, padx=5, pady=5, sticky='nswe')
    
    def __init__(self, master, build_table, ecn_number, return_cmd):
        tk.Frame.__init__(self, master)
        
        # Create Data
        self.build_table: dict[str, list[Path]] = build_table
        try:
            self.ecn_changes = read_ecn_changes(self.ecn_file.ecn_file)
        except FileNotFoundError:
            self.ecn_file = None
            self.ecn_changes = list()
        
        # Panel Functions
        self.ECN_PANEL_FUNCTIONS = (
            self._approve_change,           # Approve Button
            self._launch_dwg_view_window,   # See Locations of Files Button
            return_cmd,                     # Return Button
        )
        
        self._launch_action_window()
        
class ProductionFileFrame(tk.Frame):
    """ Class that manager this portion of the program, combines ui and functions """
    
    def _clear_window(self):
        for widget in self.winfo_children():
            widget.destroy()
            
    def _launch_drawing_view(self):
        dwg_number = self.active_frame.cmd_viewdrawing_var.get()
        try:
            dwg_paths = self.file_table.get_file_paths(dwg_number)
        except KeyError:
            Messagebox.ok(f"Part number {dwg_number} not in directory")
            return
        self._clear_window()
        self.active_frame = _DrawingViewWindow(self, dwg_paths, self._launch_action_window)
        self.active_frame.pack(side="top", padx=5, pady=5)
    
    def _launch_directory_window(self):
        osi_folder = OsiFolder(PROJDIR.WORKING)
        
        # Clear Window and Pack New Frame
        self._clear_window()
        active_frame = tk.Frame(self)
        file_panel = _FilePanel(active_frame, 0, osi_folder, self.file_table, self._launch_action_window)
        active_frame.pack(side="top",padx=5, pady=5)
        
    
    # still needs refactored
    def _launch_ecn_window(self):
        ecn_number = self.active_frame.cmd_uploadecn_var.get()
        
        self._clear_window()
        self.active_frame = _EcnWindow(self, self.build_table, ecn_number, self._launch_action_window)
        self.active_frame.pack(side="top", padx=5, pady=5)
            
    def _launch_action_window(self):
        self._clear_window()
        self.active_frame = _ActionWindow(self, self._launch_drawing_view, self._launch_ecn_window)
        self.active_frame.pack(side="top",padx=5, pady=5)
    
    def __init__(self, master):
        tk.Frame.__init__(self, master=master)
        self.file_table = FileTable(PROJDIR.WORKING)
        self._launch_action_window()
        
if __name__ == '__main__':
    root = Root()
    active_window = ProductionFileFrame(root.actionsFrame)
    active_window.pack(side='top')
    root.mainloop()