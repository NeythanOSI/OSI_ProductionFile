from ttkbootstrap.dialogs import Querybox
import ttkbootstrap as tk
from os import mkdir
from project_data import PROJDIR

def _insert_folder():
    root = PROJDIR.WORKING
    folder_name = Querybox.get_string("Type Folder Name")
    if type(folder_name) == None:
        return
    folder = root.joinpath(folder_name)
    mkdir(folder)
    
_insert_folder()
