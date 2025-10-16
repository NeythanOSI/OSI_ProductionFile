"""Main script used to manually update drawings"""

from StandardOSILib.osi_functions import osi_file_load, osi_file_store, replace_file
from project_data import PROJDATA, PROJDIR
from project_functions import get_available_dwg_revisions

if __name__ == "__main__":
    """Function that starts the program and keeps it running"""
    # Set up variables
    running = True
    mode = 0
    build_table = osi_file_load(PROJDATA.FILE_TABLE)
    exit_str = "Exit!"
    return_str = "Return!"
    
    while running:
    
        while mode == 0:    # Key 0 waits for user to input drawing number
            print("Type Drawing Number to Find Revisions")
            print(f"Type {exit_str} to exit the program")
            user_input = input("> ")
            
            if user_input == exit_str:
                running = False
                break   # To main loop
            
            if user_input in build_table.keys():
                key = user_input
                mode = 1
                break   # To main loop
            else:
                print("Drawing not in Production Drive")
                # Returns to above loop
        
        while mode == 1: # Key 1 prints revisions that currently exist
            for value in build_table[key]:
                print(value)
            print("Select Revision to Update the Above Files to")
            available_revisions = get_available_dwg_revisions(key)
            for value in available_revisions:
                print(f"Revision: {value}")
            print(return_str)
            print(exit_str)
            
            user_input = input("> ")
            
            # Mode Change Block
            if user_input == exit_str:
                running = False
                break       # To main loops
            if user_input == return_str:
                mode = 0    # User Input Drawing Numbers
                break       # To main loops
            if user_input in available_revisions:
                rev = user_input
                mode = 2    # Replace Drawings
                break       # To main loops
            else:
                print("Revision not Available")
                # Returns to above loop
                
        if mode == 2:   # Key 2 updates revisions
            for value in build_table[key]:
                new_file = replace_file(available_revisions[rev], value, PROJDIR.BACKUP)
                build_table[key][build_table[key].index(value)] = new_file
                
            # Update Build Table File
            osi_file_store(build_table, PROJDATA.FILE_TABLE)
            
            # Clean Up
            available_revisions.clear()
            del new_file
            del user_input
            del rev
            del key
            
            # Mode Change Block
            mode = 0    # To main loops