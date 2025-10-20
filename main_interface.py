import ttkbootstrap as tk
from enum import IntEnum

class Root(tk.Window):
    def __init__(self):
        super().__init__(themename='darkly')
        self.title("OSI Engineering File Manager")
        self.geometry("800x500")
        
        self.menubar = tk.Menu(self)
        self.config(menu=self.menubar)
        self.modeSelectionMenu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label='MODE', menu=self.modeSelectionMenu)
                
        self.actionsFrame = tk.Frame(self)
        self.actionsFrame.pack(side='top')
        
class _DrawingViewTree(tk.Treeview):
    
    TREE_HEADERS = ("Product Family", "File Locations")
    
    def __init__(self, master):
        
        # Create Product Tree
        tk.Treeview.__init__(self, master=master, bootstyle='default', columns=self.TREE_HEADERS, show='headings', height=25)
        self.heading(self.TREE_HEADERS[0], text="Product Family")
        self.heading(self.TREE_HEADERS[1], text="File Locations")
        self.column(self.TREE_HEADERS[0], stretch=False, width=100, anchor='center')
        self.column(self.TREE_HEADERS[1], stretch=False, width=500, anchor='center')
        
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
    
    def __init__(self, master):
        # Create Tree
        tk.Treeview.__init__(self, master=master, bootstyle='default', columns=self.TREE_HEADERS, show='headings', height=25)
        self.heading(self.TREE_HEADERS[0], text="Drawing Number")
        self.heading(self.TREE_HEADERS[1], text="New Revision")
        self.heading(self.TREE_HEADERS[2], text="Disposition")
        self.heading(self.TREE_HEADERS[3], text="Status")
        self.column(self.TREE_HEADERS[0], stretch=False, width=120, anchor='center')
        self.column(self.TREE_HEADERS[1], stretch=False, width=100, anchor='center')
        self.column(self.TREE_HEADERS[2], stretch=False, width=100, anchor='center')
        self.column(self.TREE_HEADERS[3], stretch=False, width=100, anchor='center')

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
        
class ProductionFileFrame(tk.Frame):
    
    def _clear_window(self):
        for widget in self.winfo_children():
            widget.destroy()
            
    def _launch_action_window(self):
        self._clear_window()
        self.active_frame = ActionWindow(self, self._launch_drawing_view_action, self._launch_ecn_window)
        self.active_frame.pack(side="top",padx=5, pady=5)
            
    def _launch_drawing_view(self, command):
        self._clear_window()
        self.active_frame = tk.Frame(self)
        self.active_frame.pack(side="top", padx=5, pady=5)
        
        # Widgets
        drawing_view_frame = _DrawingViewTree(self.active_frame)
        drawing_view_frame.grid(row=0, column=0, padx=5, pady=5, sticky='nswe')
        # Button to Return
        cmd_return_button = tk.Button(self.active_frame, text="Done", command=command)
        cmd_return_button.grid(row=1, column=0, padx=5, pady=5, sticky='nswe')
    def _launch_drawing_view_action(self):
        self._launch_drawing_view(command=self._launch_action_window)
    def _launch_drawing_view_ecn(self):
        self._launch_drawing_view(command=self._launch_ecn_window)
    
    def _launch_ecn_window(self):
        self._clear_window()
        self.active_frame = tk.Frame(self)
        self.active_frame.pack(side="top", padx=5, pady=5)
        
        # Functions
        ECN_PANEL_FUNCTIONS = (
            None,
            self._launch_drawing_view_ecn,
            self._launch_file_window,
            self._launch_action_window,
            self._launch_action_window
        )
        
        # Widgets
        self.ecn_tree = _EcnTree(self.active_frame)
        self.ecn_tree.grid(row=0, column=1, padx=5, pady=5, sticky='nswe')
        self.ecn_panel = _EcnPanel(self.active_frame, ECN_PANEL_FUNCTIONS)
        self.ecn_panel.grid(row=0, column=0, padx=5, pady=5, sticky='nswe')
    
    def _launch_file_window(self):
        self._clear_window()
        self.active_frame = tk.Frame(self)
        self.active_frame.pack(side="top", padx=5, pady=5)
        
        # Widgets
        self.file_tree = _FileTree(self.active_frame)
        self.file_tree.grid(row=0, column=1, padx=5, pady=5, sticky='nswe')
        self.file_panel = _FilePanel(self.active_frame, self._launch_ecn_window)
        self.file_panel.grid(row=0, column=0, padx=5, pady=5, sticky='nswe')
    
    def __init__(self, master):
        tk.Frame.__init__(self, master=master)
        self._launch_action_window()
        
if __name__ == '__main__':
    root = Root()
    active_window = ProductionFileFrame(root.actionsFrame)
    active_window.pack(side='top')
    root.mainloop()