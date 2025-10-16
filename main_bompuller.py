"""This looks at the bill of materials of a pdf and pulls all the drawings from that into a folder"""

import re
import os
from pathlib import Path, WindowsPath, PosixPath
from project_data import PROJDIR
from project_functions import get_drawings, get_dwg_number_rev
from StandardOSILib.osi_directory import PART_NUM_REGEX
from PyPDF2 import PdfReader, PdfWriter

def get_bom_part_numbers(file: Path|WindowsPath|PosixPath) -> list[str]:
    print(file.stem)
    
    # Get text from pdf
    pdf_reader = PdfReader(file)
    pdf_page = pdf_reader.pages[0]  # BOM should be on first page
    file_text = pdf_page.extract_text()
    del pdf_reader
    del pdf_page
    
    # Split Lines
    split_file_text = file_text.splitlines()
    del file_text
    
    # Remove lines without part nummbers
    part_number_text = dict()       # Part number is key, line is value
    for line in split_file_text:
        part_number = re.search(PART_NUM_REGEX, line)
        if not part_number:
            continue
        part_number_text[part_number.group(0)] = re.sub(PART_NUM_REGEX, "", line)
        # !!!The part number must be removed from the line, some product codes get picked up by the regex
        # That looks for dates
    del split_file_text
    
    # Remove lines that dont begin with a number (All BOM items have a number at the start of the line)
    remove_lines = list()  
    for key in part_number_text:
        if part_number_text[key][0].isnumeric():
            continue
        remove_lines.append(key)
    for key in remove_lines:
        part_number_text.pop(key)
    del remove_lines
          
    # Remove lines with dates
    remove_lines = list()  
    for key in part_number_text:
        date = re.search(r"\d{2,4}[-\/]\d{2,4}[-\/]\d{2,4}", part_number_text[key])
        if not date:
            continue
        remove_lines.append(key)
    for key in remove_lines:
        part_number_text.pop(key)
    del remove_lines
    
    # Remove lines that share the drawing number with the file name
    remove_lines = list()
    for key in part_number_text:
        if key != get_dwg_number_rev(file)[0]:
            continue
        remove_lines.append(key)
    for key in remove_lines:
        part_number_text.pop(key)
    del remove_lines
    
    return list(part_number_text.keys())
    
parent_drawings: list[Path] = list()
for value in get_drawings(PROJDIR.BOM).values():
    parent_drawings.append(value[0])
    
for file in parent_drawings:
    print(get_bom_part_numbers(file))
    
#print(PART_NUM_REGEX)
        