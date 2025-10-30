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

@dataclass
class OsiFile():
    file_path: Path
    file_name: str
    file_type: str
    
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
                file_name = file_path.stem
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

def serialize_files(directory: OsiFolder, ):
    pass

def open_pdf(self, file: Path):
    """Opens a pdf of the selected file"""
    if file.suffix == ".pdf" or file.suffix == ".PDF" or file.suffix == ".Pdf":
        webbrowser.open_new(file)

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

class _FileWindow(tk.Frame):
    """ A class that displays a file tree window with buttons to manipulate functions"""
    
    # Refactored
    def _check_dir_empty(self) -> bool:
        """Error Checking Function: Verify that root folder is an empty folder

        Returns:
            bool: Returns True if folder contains is empty, Returns False if files or folders are present
        """
        if self.folder_paths.__len__() == 0:
            return True
        else:
            return False
    
    # Refactored
    def _check_directory(self) -> bool:
        """Error Checking Function: Verify that root folder contains only folders

        Returns:
            bool: Returns True if folder contains only directories, Returns False if files are present
        """
        for path in self.folder_paths:
            if path.is_dir():
                continue
            else:
                return False
        return True

    # Refactored
    def _check_no_children(self):
        """Error Checking Function: Verify that selected folder is empty

        Returns:
            bool: Returns True if folder does not contain children, Returns False if children are present,
             or if there is error
        """
        try:
            selection = self.file_tree.return_selection()
            if len(listdir(self.folder_paths[selection])) == 0:
                return True
            else:
                return False
        except:
            return False

    def _error_check_insert(self, file_path: Path) -> int:
        """Checks errors before performing and data altering insert drawing functions

        Returns:
            int: Returns 1 if the drawing file to copy does not exist\n
            Returns 2 if the root folder is a directory\n
            Returns 0 if successful \n
        """
        if not file_path.exists():
            print(FileNotFoundError(f"source file {file_path} to copy to production drive does not exist"))
            return 1
        if self._check_directory():
            print(TypeError(f"cannot insert drawing pdf in directory folder"))
            return 2
        return 0
    
    def _update_index(self, file_name: str, change: int) -> str:
        """Takes a file name with an index in the format "000" and updates it by the change value.

        Args:
            file_name (str): The file name to change the index of. Index must be three numbers at the start of the file name.
            change (int): The integer to change the index by. Negative numbers decriment, Positive numbers incriment

        Returns:
            str: The file name with the updated index in the format "000"
        """
        drawing = file_name[3:]
        index = str(int(file_name[:3]) + change)
        
        for i in range(3 - index.__len__()):
            index = str(0) + index
            
        return index + drawing
    
    def _write_new_index(self, file: Path, change: int):
        file_name = file.name
        file_path = file.parent
        dwg_number = get_dwg_number_rev(file)[0]
        
        file_new = self._update_index(file_name, change)
        file_new_path = file_path.joinpath(file_new)
        file.rename(file_new_path)
        
        build_table_paths: list[Path] = self.build_table[dwg_number]
        build_table_ind = build_table_paths.index(file)
        build_table_paths[build_table_ind] = file_new_path  # Updates Build Table by Reference
    
    def _serialize_files(self, inc_selection: bool, change: int):
        """Uses the current selection in the treeview, and updates the index on all files below the selection
        (and the selection if inc_selection is set to true) by the integer change parameter.
        
        Args:
            inc_selection (bool): True includes the selection when updating indexes
            change (int): Positive values incriments while negative decriment. Updates index by integer supplied.
        """
            
        
        if self._check_directory():
            return
        
        selection = self.file_tree.return_selection()
        for i in range(selection, self.folder_childs.__len__()):
            if not inc_selection:       # Skip first iteration to avoid updating selected file
                inc_selection = True    # Stops this section from looping
                continue
            self._write_new_index(self.folder_paths[i], change)
        
        self._scan_folder()     # Update
        
    def _get_pdf_drawing(self) -> Path:
        """Returns the source path for the new drawing released/updated with the ecn

        Returns:
            Path|int: Path object pointing to an updated/new drawing in the ECN folder's updated drawings folder.
            It is recomend to check the file exists after using this function
        """
        ecn_drawings = self.ecn_file.ecn_drawings
        dwg_number = self.ecn_change.dwg_number
        dwg_rev = self.ecn_change.new_revision
        drawing_src = ecn_drawings.joinpath(dwg_number + '-' + dwg_rev + '.pdf')
        return drawing_src

    # Except for Serials Refactored
    def _insert_file(self, drawing_src: Path, index: str):
        """Inserts the file from the ecn, should be called by either insert above or insert below function

        Args:
            drawing_src (Path): Path object to drawing to insert
            index (str): Index the inserted drawing will have
        """
        
        drawing = Path(copy(src=drawing_src, dst=self.root))
        drawing_name = drawing.name
        drawing_parent = drawing.parent
        
        new_name = index + drawing_name
        new_path = drawing_parent.joinpath(new_name)
        drawing = drawing.rename(new_path)
        
        dwg_number = get_dwg_number_rev(drawing)[0]
        if dwg_number in self.build_table.keys():
            self.build_table[dwg_number].append(drawing)
        else:
            self.build_table[dwg_number] = [drawing]        
        self._scan_folder()
    
    def _insert_above(self):
        """Inserts the file from the ecn above the selection in the treeview"""
        
        selection = self.file_tree.return_selection()
        file_index: str = self.folder_paths[selection].stem[:4]
        drawing_src = self._get_pdf_drawing()
        
        if self._error_check_insert(drawing_src) != 0:
            return

        self._serialize_files(True, 1)
        self._insert_file(drawing_src, file_index)
    
    def _insert_below(self):
        """Inserts the file from the ecn below the selection in the treeview"""
        
        selection = self.file_tree.return_selection()
        file_name = self.folder_childs[selection][1]        # Use selection index to avoid risk of going out of bounds
        file_index = self._update_index(file_name, 1)[:4]   # Add +1 to the selection index to account for inserting below
        drawing_src = self._get_pdf_drawing()               # verify drawings is in ECN folder
        
        if self._error_check_insert(drawing_src) != 0:
            return
        
        self._serialize_files(False, 1)
        self._insert_file(drawing_src, file_index)
        
    # Except for Serials Refactored
    def _delete_selection(self):
        """Deletes the selected file, does not work for directories"""
        selection = self.file_tree.return_selection()
        file_path: Path = self.folder_paths[selection]
        
        if self._check_directory():
            if not self._check_no_children():
                print("This has children")
                return
            if Messagebox.yesno("are you sure, this will permenantly deletes the folder") == "No":
                print("Not Destroy")
                return
            file_path.rmdir()
        else:
            if Messagebox.yesno("are you sure, this will permenantly deletes the file") == 'No':
                print("Not Destroy")
                return
            print("Destroy")
            dwg_number, dwg_rev = get_dwg_number_rev(file_path)
            self._serialize_files(False, -1)    # Lower Serial Nunbers after selected file by 1
            index = self.build_table[dwg_number].index(file_path)   # Remove entry from build table
            self.build_table[dwg_number].pop(index)
            file_path.unlink()
        
        self._scan_folder()        
    
    def _scan_folder(self):
        """ Scans the root directory and find all documents contained. Displays the documents to the treeview """
        self.file_tree.clear_tree()
        self.folder_childs.clear()
        self.folder_paths.clear()
        with scandir(self.root) as dir:
            folder_dict = dict()
            for file in dir:
                file_path = Path(file.path)
                file_name = file_path.stem
                file_type = file_path.suffix
                if file_type == "":
                    file_type = "Folder"
                folder_dict[file_name] = (file_path, file_name, file_type)
            sorted_keys = sorted(folder_dict.keys())
            for key in sorted_keys:
                self.folder_childs.append((folder_dict[key][2], folder_dict[key][1]))
                self.folder_paths.append(folder_dict[key][0])
                
        # Populate the Interface
        self.file_tree.populate_tree(self.folder_childs)
        if self._check_dir_empty():
            self.file_panel.refresh(0)
            return
        if self._check_directory():
            self.file_panel.refresh(1)
            return
        self.file_panel.refresh(2)
    
    # Refactored
    def _enter_folder(self):
        """Set the root directory to the folder selected in treeview"""
        
        selection = self.file_tree.return_selection()
        if not self._check_directory():
            return
        self.root = self.folder_paths[selection]
        self._scan_folder()
    
    def _prev_folder(self):
        """Return to the parent folder of the current root directory, limits to the production drawings folder"""
        if self.root == PROJDIR.WORKING:    # don't let user out of the scope of the program
            return
        self.root = self.root.parent
        self._scan_folder()
    
    # Refactored
    def _open_pdf(self):
        """Opens a pdf of the selected file"""
        file = self.folder_paths[self.file_tree.return_selection()]
        if file.suffix == ".pdf" or file.suffix == ".PDF" or file.suffix == ".Pdf":
            webbrowser.open_new(file)
    
    def __init__(self, master, build_table, ecn_file: EcnFile, ecn_change: EcnChange, return_cmd=None):
        """_summary_

        Args:
            master (_type_): tkinter frame object or equivelant
            build_table (_type_): the dictionary containing all production drawing paths assocoated with dwg_number keys
            ecn_file (EcnFile): EcnFile object for the ecn the _FileWindow class was called from
            ecn_change (EcnChange): EcnChange object for the ecn change the _FileWindow class was called from
            return_cmd (_type_): Command to return to the parent object, If left blank, will not have a return button
        """
        tk.Frame.__init__(self, master)
        
        self.ecn_file = ecn_file
        self.ecn_change = ecn_change
        self.build_table = build_table
        
        self.root = PROJDIR.WORKING
        self.dir_type = None
        self.folder_childs: list[tuple[str]] = list()
        self.folder_paths: list[Path] = list()

        FILE_PANEL_FUNCTIONS = (
            self._insert_above,     # Insert Above
            self._insert_below,     # Insert Below
            None,
            self._delete_selection,      # Delete File
            self._enter_folder,     # Enter Folder
            self._prev_folder,      # Previous Folder
            self._open_pdf,         # Open PDF
            return_cmd,             # Done / Return Command
        )

        # Widgets
        self.file_tree = _FileTree(self)
        self.file_tree.grid(row=0, column=1, padx=5, pady=5, sticky='nswe')
        self.file_panel = _FilePanel(self, 0, FILE_PANEL_FUNCTIONS)
        self.file_panel.grid(row=0, column=0, padx=5, pady=5, sticky='nswe')
        
        self._scan_folder()

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
        self.file_window = _FileWindow(self, self.build_table, self.ecn_file, None)
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