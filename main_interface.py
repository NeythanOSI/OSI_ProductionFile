import ttkbootstrap as tk
from enum import IntEnum
from project_functions import EcnFile, EcnChange, get_ecn, read_ecn_changes
from StandardOSILib.osi_directory import OSIDIR
from project_data import PROJDIR, PROJDATA
from StandardOSILib.osi_functions import osi_file_load

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
        self.heading(self.TREE_HEADERS[0], text="Product Family")
        self.heading(self.TREE_HEADERS[1], text="File Locations")
        self.column(self.TREE_HEADERS[0], stretch=False, width=200, anchor='w')
        self.column(self.TREE_HEADERS[1], stretch=False, width=700, anchor='w')
        
class ActionWindow(tk.Frame):
    
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
        
class _FileTree(tk.Treeview):
    
    TREE_HEADERS = ("File Type", "File Name")
    
    def __init__(self, master):
        # Create Tree
        tk.Treeview.__init__(self, master=master, bootstyle='default', columns=self.TREE_HEADERS, show='headings', height=25)
        self.heading(self.TREE_HEADERS[0], text="File Type")
        self.heading(self.TREE_HEADERS[1], text="File Name")
        self.column(self.TREE_HEADERS[0], stretch=False, width=200, anchor='center')
        self.column(self.TREE_HEADERS[1], stretch=False, width=200, anchor='center')
        
class _FilePanel(tk.Frame):
    def __init__(self, master, cmd_return):
        tk.Frame.__init__(self, master)
        # Button Insert Above
        cmd_iabove_button = tk.Button(master=self, text="Insert Above", width = 20, command=None)
        cmd_iabove_button.grid(row=0, column=0, padx=5, pady=5, sticky='nswe')
        # Button Insert Below
        cmd_ibelow_button = tk.Button(master=self, text="Insert Below", width = 20, command=None)
        cmd_ibelow_button.grid(row=1, column=0, padx=5, pady=5, sticky='nswe')
        # Enter Folder
        cmd_enterfol_button = tk.Button(master=self, text="Enter Folder", width=20, command=None)
        cmd_enterfol_button.grid(row=2, column=0, padx=5, pady=5, sticky='nswe')
        # Open PDF
        cmd_openpdf_button = tk.Button(master=self, text="Open PDF", width=20, command=None)
        cmd_openpdf_button.grid(row=3, column=0, padx=5, pady=5, sticky='nswe')
        # Done
        cmd_done_button = tk.Button(master=self, text="Done", width=20, command=cmd_return)
        cmd_done_button.grid(row=4, column=0, padx=5, pady=5, sticky='nswe')
        
class _EcnTree(tk.Treeview):
    
    TREE_HEADERS = ("Drawing Number", "New Revision", "Disposition", "Status")
    
    def populate_tree(self, entries: tuple[str]):
        for i, entry in enumerate(entries):
            self.insert("", 'end', iid=i, values=entry)
            
    def return_selection(self, position):
        # Try Statement blocks errors if nothing is selected
        try:
            return int(self.focus())
        except ValueError:
            return None
    
    def __init__(self, master):
        # Create Tree
        tk.Treeview.__init__(self, master=master, bootstyle='default', columns=self.TREE_HEADERS, show='headings', height=25)
        self.heading(self.TREE_HEADERS[0], text="Drawing Number")
        self.heading(self.TREE_HEADERS[1], text="New Revision")
        self.heading(self.TREE_HEADERS[2], text="Disposition")
        self.heading(self.TREE_HEADERS[3], text="Status")
        self.column(self.TREE_HEADERS[0], stretch=False, width=150, anchor='w')
        self.column(self.TREE_HEADERS[1], stretch=False, width=150, anchor='c')
        self.column(self.TREE_HEADERS[2], stretch=False, width=150, anchor='w')
        self.column(self.TREE_HEADERS[3], stretch=False, width=150, anchor='w')
        
        self.bind('<<TreeviewSelect>>', self.return_selection)

class _EcnPanel(tk.Frame):
    def __init__(self, master, ecn_functions):
        tk.Frame.__init__(self, master)
        
        # Button Approve
        cmd_approve_button = tk.Button(master=self, text="Approve", width = 20, command=ecn_functions[0])
        cmd_approve_button.grid(row=0, column=0, padx=5, pady=5, sticky='nswe')
        # Button See Location
        cmd_setloc_button = tk.Button(master=self, text="See Location", width = 20, command=ecn_functions[1])
        cmd_setloc_button.grid(row=1, column=0, padx=5, pady=5, sticky='nswe')
        # Button Set Location
        cmd_setloc_button = tk.Button(master=self, text="Set Location", width = 20, command=ecn_functions[2])
        cmd_setloc_button.grid(row=2, column=0, padx=5, pady=5, sticky='nswe')
        # Button Apply
        cmd_apply_button = tk.Button(master=self, text="Apply", width = 20, command=ecn_functions[3])
        cmd_apply_button.grid(row=3, column=0, padx=5, pady=5, sticky='nswe')
        # Button Cancel
        cmd_cancel_button = tk.Button(master=self, text="Cancel", width = 20, command=ecn_functions[4])
        cmd_cancel_button.grid(row=4, column=0, padx=5, pady=5, sticky='nswe')
        
class _EcnFrame(tk.Frame):
    def __init__(self, master):
        tk.Frame.__init__(self, master)
        # Widgets
        self.ecn_tree = _EcnTree(self.active_frame)
        self.ecn_tree.grid(row=0, column=1, padx=5, pady=5, sticky='nswe')
        self.ecn_panel = _EcnPanel(self.active_frame, ECN_PANEL_FUNCTIONS)
        self.ecn_panel.grid(row=0, column=0, padx=5, pady=5, sticky='nswe')
        
class ProductionFileFrame(tk.Frame):
    
    def _clear_window(self):
        for widget in self.winfo_children():
            widget.destroy()
            
    def _clear_data(self):
        self.ecn_changes = None
        self.ecn_file = None
            
    def _launch_action_window(self):
        self._clear_window()
        self._clear_data()
        self.active_frame = ActionWindow(self, self._launch_drawing_view_action, self._launch_ecn_window_instance)
        self.active_frame.pack(side="top",padx=5, pady=5)
    
    def _launch_drawing_view(self, drawing, command):
        self._clear_window()
        self.active_frame = tk.Frame(self)
        self.active_frame.pack(side="top", padx=5, pady=5)
        
        # Widgets
        drawing_view_frame = _DrawingViewTree(self.active_frame)
        drawing_view_frame.grid(row=0, column=0, padx=5, pady=5, sticky='nswe')
        # Button to Return
        cmd_return_button = tk.Button(self.active_frame, text="Done", command=command)
        cmd_return_button.grid(row=1, column=0, padx=5, pady=5, sticky='nswe')
        
        # Populate Tree with Drawing Locations
        entries = list()
        for entry in self.build_table[drawing]:
            entries.append((None, entry))
        drawing_view_frame.populate_tree(entries)
    def _launch_drawing_view_action(self):  # Launches from the main window
        dwg_number = self.active_frame.cmd_viewdrawing_var.get()
        self._launch_drawing_view(drawing = dwg_number, command=self._launch_action_window)
    def _launch_drawing_view_ecn(self):     # Launches from the ecn window
        self._launch_drawing_view(drawing = None, command=self._launch_ecn_window_return)
    
    def _launch_ecn_window_instance(self):
        """Use this function when launching a brand new instance of the ECN Window"""
        ecn_number = self.active_frame.cmd_uploadecn_var.get()
        self.ecn_file = get_ecn(ecn_number)
        self.ecn_changes = read_ecn_changes(self.ecn_file.ecn_file)
        self._launch_ecn_window_return()
        
    def _launch_ecn_window_return(self):
        """This function returns to the current instance of the ECN Window"""
        # Get Variables from the Action Window
        
        self._clear_window()
        self.active_frame = tk.Frame(self)
        self.active_frame.pack(side="top", padx=5, pady=5)
        
        # Functions
        ECN_PANEL_FUNCTIONS = (
            None,                           # Approve Button   
            self._launch_drawing_view_ecn,  # See Location of Files Button
            self._launch_file_window,       # Set new File Locations Button
            self._launch_action_window,     # Apply Button
            self._launch_action_window      # Cancel Button
        )
        
        # Widgets
        self.ecn_tree = _EcnTree(self.active_frame)
        self.ecn_tree.grid(row=0, column=1, padx=5, pady=5, sticky='nswe')
        self.ecn_panel = _EcnPanel(self.active_frame, ECN_PANEL_FUNCTIONS)
        self.ecn_panel.grid(row=0, column=0, padx=5, pady=5, sticky='nswe')
        
        # Populate Tree
        ecn_change_list = list()
        for change in self.ecn_changes:
            ecn_change_list.append((change.dwg_number, change.new_revision, change.disposition, change.status))
        self.ecn_tree.populate_tree(ecn_change_list)
    
    def _launch_file_window(self):
        """Window that allows naviation through the production files, and adds new files where they belong"""
        self._clear_window()
        self.active_frame = tk.Frame(self)
        self.active_frame.pack(side="top", padx=5, pady=5)
        
        # Widgets
        file_tree = _FileTree(self.active_frame)
        file_tree.grid(row=0, column=1, padx=5, pady=5, sticky='nswe')
        file_panel = _FilePanel(self.active_frame, self._launch_ecn_window_return)
        file_panel.grid(row=0, column=0, padx=5, pady=5, sticky='nswe')
    
    def __init__(self, master):
        tk.Frame.__init__(self, master=master)
        self._launch_action_window()
        
        # Globals
        self.build_table = osi_file_load(PROJDATA.FILE_TABLE)
        self.ecn_file = None
        self.ecn_changes = None
        
if __name__ == '__main__':
    root = Root()
    active_window = ProductionFileFrame(root.actionsFrame)
    active_window.pack(side='top')
    root.mainloop()