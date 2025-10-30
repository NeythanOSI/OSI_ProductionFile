import ttkbootstrap as tk
from ttkbootstrap.dialogs import Messagebox
from tkinter.filedialog import askopenfilename

from enum import IntEnum
from dataclasses import dataclass
from typing import NamedTuple
from pathlib import Path
from shutil import copy
from os import scandir, listdir, mkdir, walk
import webbrowser

from project_functions import EcnFile, get_ecn, read_ecn_changes, EcnChange, get_drawings, get_dwg_number_rev
from StandardOSILib.osi_directory import OSIDIR
from project_data import PROJDIR, PROJDATA
from StandardOSILib.osi_functions import osi_file_load, osi_file_store, replace_file

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
    
    def __init__(self, start_path: Path = Path(r"X:")):
        self.start_path = start_path
        self.root = start_path
        self.children: list[OsiFolder.FolderChild] = list()    # String is the File Name in the FolderChild object
        self.type = None
        self._scan_folder()

class DrawingDrive():
    """ Collection of data and functions to handle where production drawings are stored """
    
    def get_drawings(Folder: Path) -> dict[str, list[str]]:
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

    def get_index_length(self, file_name: str):
        # Get the ammount of numbers that make up the index, This assumes the index is a numberical number at the start
        for i in range(file_name.__len__()):
            try:
                int(file_name[i])
            except ValueError:
                break
        return i

    def change_index(self, file_name: str, change: int):
        """Takes a file name with an index in the format "index-dwg_number-etc" and updates it by the change value.

            Args:
                file_name (str): The file name to change the index of. Index must be integers at the start of the file name.
                change (int): The integer to change the index by. Negative numbers decriment, Positive numbers incriment

            Returns:
                str: The file name with the updated index in the format it was given
        """
        # Get the ammount of numbers that make up the index, This assumes the index is a numberical number at the start
        i = self.get_index_length(file_name)
        
        drawing = file_name[i:]
        index = str(int(file_name[:i]) + change)
        
        # Index must keep the same number of integers, 000 -> 001, 0002 -> 0001 etc
        for j in range(i - index.__len__()):
            index = str(0) + index
            
        return index + drawing

    def serialize_files(self, selection: int, inc_selection: bool, change: int):
        old_children = list()
        new_children = list()
        for i in range(selection, self.directory.children.__len__()):
            if not inc_selection:       # Skip first iteration to avoid updating selected file
                inc_selection = True    # Stops this section from looping
                continue
            
            
            # Index the child by the change and create a new path for renaming the file
            child = self.directory.children[i]
            old_children.append((get_dwg_number_rev(child.fpath)[0], child.fpath))  # Save data for updating the file_table
            file_name = self.change_index(child.fname, change)
            file_path = child.fpath.parent.joinpath(file_name)
            new_children.append(file_path)  # Keep track for updating file_table
            
            # Update the child
            child.fpath.rename(file_path)
            self.directory.children[selection] = self.directory.FolderChild(file_path, file_name, child.fsuffix, child.ftype)
            
        # Update the build table
        for i, child in enumerate(old_children):
            self.update_file_table(child[0], child[1], new_children[i])
            
        # Do a refresh
        self.directory._scan_folder()

    def _insert_folder(self, folder_name):
        folder = self.directory.root.joinpath(folder_name)
        mkdir(folder)
        self.directory._scan_folder()
    
    def _insert_file(self, selection: int, above: bool = True):
        
        file_path = Path(askopenfilename(initialdir="X:"))
        if file_path.name == "":
            return
        
        if above:
            # Get the selected files index
            selection_name = self.directory.children[selection].fname
            i = self.get_index_length(selection_name)+1
            index = selection_name[:i]
            
            # Serialize up selected file and its below files
            self.serialize_files(selection, True, 1)
        else:
            # Get the selected files index and incriment
            selection_name = self.directory.children[selection].fname
            i = self.get_index_length(selection_name)+1
            index = selection_name[:i]
            index = self.change_index(index, 1)
            
            # Serialize up below files
            self.serialize_files(selection, False, 1)
            
        # Filling below, means stealing the below selected, and indexing below selected
        file_path = Path(copy(src=file_path, dst=self.directory.root))
        file_path_new = file_path.parent.joinpath(index + file_path.name)
        file_path = file_path.rename(file_path_new)
        
        # Add to File Table
        self.add_file_table_entry(get_dwg_number_rev(file_path)[0], file_path)
            
        # Updates
        self.directory._scan_folder()
    
    def _delete_selection(self, selection: int):
        
        def _check_dir_empty() -> bool:
            """Returns: Returns True if folder contains is empty, Returns False if files or folders are present"""
            if self.directory.children.__len__() == 0:
                return True
            else:
                return False
        def _check_directory() -> bool:
            """Returns: Returns True if folder contains only directories, Returns False if files are present"""
            for child in self.directory.children:
                if child.fpath.is_dir():
                    continue
                else:
                    return False
            return True
        def _check_no_children(selection) -> bool:
            """Returns: Returns True if folder does not contain children, Returns False if children are present,
                or if there is error"""
            folder_path = self.directory.children[selection].fpath
            try:
                if len(listdir(folder_path)) == 0:
                    return True
                else:
                    return False
            except:
                return False
            
        file_path: Path = self.directory.children[selection].fpath
        file_type: int = self.directory.children[selection].ftype
        
        if file_type == OsiFolder.FolderType.FOLDER:
            # Code to run for deleting folders
            if not _check_no_children(selection):
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

            self.serialize_files(selection, False, -1)
            self.update_file_table(get_dwg_number_rev(file_path)[0], file_path)
            file_path.unlink()
            print(f"removed file {file_path}")
        else:
            return

        self.directory._scan_folder()

    def __init__(self, directory: OsiFolder):
        self.directory = directory
        self.file_table = get_drawings(self.directory.start_path)

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
    
    def __init__(self, master, mode: int, file_functions: list):
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
        tk.Frame.__init__(self, master)
        self.cmd_iabove_button = tk.Button(master=self, text="Insert Above", width = 15, command=file_functions[0])
        self.cmd_ibelow_button = tk.Button(master=self, text="Insert Below", width = 15, command=file_functions[1])
        self.cmd_ifolder_button = tk.Button(master=self, text="Insert Folder", width = 15, command=file_functions[2])
        self.cmd_delete_button = tk.Button(master=self, text="Delete Selected", width = 15, command=file_functions[3])
        self.cmd_enterfol_button = tk.Button(master=self, text="Enter Folder", width=15, command=file_functions[4])
        self.cmd_prevfol_button = tk.Button(master=self, text="Previous Folder", width=15, command=file_functions[5])
        self.cmd_openpdf_button = tk.Button(master=self, text="Open PDF", width=15, command=file_functions[6])
        self.done_button = False
        if file_functions[7] != None:
            self.cmd_done_button = tk.Button(master=self, text="Done", width=15, command=file_functions[7])
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
    
    def __init__(self, master):
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
    def __init__(self, master, ecn_functions):
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
    
    def __init__(self, master, build_table, drawing, return_cmd):
        tk.Frame.__init__(self, master)
        
        # Widgets
        drawing_view_frame = _DrawingViewTree(self)
        drawing_view_frame.grid(row=0, column=0, padx=5, pady=5, sticky='nswe')
        # Button to Return
        cmd_return_button = tk.Button(self, text="Done", command=return_cmd)
        cmd_return_button.grid(row=1, column=0, padx=5, pady=5, sticky='nswe')
        
        # Populate Tree with Drawing Locations
        entries = list()
        try:
            for entry in build_table[drawing]:
                entries.append((None, entry))
        except KeyError:
            pass
        drawing_view_frame.populate_tree(entries)

class _EcnWindow(tk.Frame):
    
    def _approve_change(self):
        """Pushes the new revision for ecn change with running change disposition """
        selection = self.ecn_tree.return_selection()
        ecn_change: EcnChange = self.ecn_changes[selection]
        
        if ecn_change.disposition != "Running Change":
            return
        
        ecn_drawings = self.ecn_file.ecn_drawings
        
        dwg_number = ecn_change.dwg_number
        dwg_rev = ecn_change.new_revision
        dwg_name = dwg_number + '-' + dwg_rev + '.pdf'
        dwg_src = ecn_drawings.joinpath(dwg_name)
        
        if not dwg_src.exists():
            print(f"source file {dwg_src} to copy to production drive does not exist")
            return
        
        for value in self.build_table[dwg_number]:
            index = value.name[:4]
            
            prod_file = replace_file(dwg_src, value, PROJDIR.BACKUP)
            
            file_path = prod_file.parent
            file_name = prod_file.name
            file_name = index + file_name
            
            new_file = file_path.joinpath(file_name)
            prod_file = prod_file.rename(new_file)
            
            self.build_table[dwg_number][self.build_table[dwg_number].index(value)] = prod_file
    
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
            self.ecn_file = get_ecn(ecn_number)
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
    
    def _clear_window(self):
        for widget in self.winfo_children():
            widget.destroy()
            
    def _launch_action_window(self):
        self._clear_window()
        self.active_frame = _ActionWindow(self, self._launch_drawing_view, self._launch_ecn_window)
        self.active_frame.pack(side="top",padx=5, pady=5)
    
    def _launch_drawing_view(self):
        dwg_number = self.active_frame.cmd_viewdrawing_var.get()
        self._clear_window()
        self.active_frame = _DrawingViewWindow(self, self.build_table, dwg_number, self._launch_action_window)
        self.active_frame.pack(side="top", padx=5, pady=5)
    
    def _launch_ecn_window(self):
        ecn_number = self.active_frame.cmd_uploadecn_var.get()
        self._clear_window()
        self.active_frame = _EcnWindow(self, self.build_table, ecn_number, self._launch_action_window)
        self.active_frame.pack(side="top", padx=5, pady=5)
    
    def _launch_file_window(self):
        """Window that allows naviation through the production files, and adds new files where they belong"""
        self._clear_window()
        self.active_frame = tk.Frame(self)
        self.active_frame.pack(side="top", padx=5, pady=5)
    
    def __init__(self, master):
        tk.Frame.__init__(self, master=master)
        self._launch_action_window()
        
        # Globals
        
        # Figure out how to thread the build table for better performance at a later date
        self.build_table: dict[str, list[Path]] = get_drawings(PROJDIR.WORKING)
        osi_file_store(self.build_table, PROJDATA.FILE_TABLE)
        for key in self.build_table.keys():
            print(f"{key} : {self.build_table[key]}")
        
if __name__ == '__main__':
    root = Root()
    active_window = ProductionFileFrame(root.actionsFrame)
    active_window.pack(side='top')
    root.mainloop()