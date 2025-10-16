import re

part_number_text = {
    "FA-012345": "Some description 2021-05-01",
    "FB-678901": "Another description without date",
    "MSA-01235": "More text 12/31/2020",
    "TSA-00100": "Test no date"
}

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

print(part_number_text.keys())