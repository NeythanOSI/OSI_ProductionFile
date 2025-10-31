from ttkbootstrap.dialogs import Messagebox
error = ["FA-00123", "FA-00125", "MSA-00125"]
error_string = "The following are not in the updated drawings folder\n"

for err in error:
    error_string = error_string + err + "\n"
    print(error_string)

Messagebox.ok(error_string)