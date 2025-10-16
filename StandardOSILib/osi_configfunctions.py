""" This python module is specially dedicated to building the config files. 
    The functions are called from the Globals file and data is stored there """

# This module involves reguler expressions which can be very complex, please see the below resources
""" TO WORK WITH REGEXES:  https://regex101.com/ 
    YOUTUBE VIDEO TO HELP: https://www.youtube.com/watch?v=rhzKDrUiJVk&t=1015s 
    PYTHON SPECIFIC REGEX: https://docs.python.org/3/library/re.html 
    PYTHON SPECIFIC REGEX: https://www.w3schools.com/python/python_regex.asp"""

""" Standard Python Library Modules """
import csv
from pathlib import Path
    
def buildPartRegex(ConfigCSV: Path, StandarCSV: Path) -> str:
    """ Dataclass to Create a Regex for OSI Part Numbers, This data class
    should be initated and the varaibles created from it to reveal to other files"""
    """ As Configurations are Added to OSI Catalog and Other Drawing Prefixes this will need to be updated"""

    """ Dictionaries are for storing values constructed from CSV Files
        Then the dictionaries are used to build lists of regex strings
        Then the lists are used to build a large Regex for Looking up Part Numbers"""
    _STDRWDIC: dict[list, list] = dict()

    _CNDRWDIC: dict[list, list] = dict()
    
    _STDRWPRE: list[str] = list()
    
    _CNDRWPRE: list[str] = list()
    
    """ Builds up the Configuration Drawing Names Dictionary for Regex Building"""
    def _productCodeConfigDict():
        csvFile = open(ConfigCSV, 'r')
        csvReader = csv.reader(csvFile)
        configId = None

        for line in csvReader:
            # Rows are recognised as one group by their Id in the first cell
            if line[0] != configId:
                configId = line[0]
                
                # Sets up the dictionary for that group of rows
                _CNDRWDIC[configId] = list()
                
            configBlock = list()
            
            # append to config block all product code options,
            for i, cell in enumerate(line):
                # skip first entry is it will always be the id
                if i == 0:
                    continue
                # csv_reader recognises empty cells so throw them out with continue block
                if cell == '':
                    continue
                configBlock.append(cell)
            
            _CNDRWDIC[configId].append(configBlock)
            
        csvFile.close()
    
    """ Builds up the Standard Drawing Names Dictionary for Regex Building """
    def _drawingConfigDict():
        csvFile = open(StandarCSV, 'r')
        csvReader = csv.reader(csvFile)
        ID = None

        for line in csvReader:
            ID = line[0]                
            _STDRWDIC[ID] = (line[1], line[2])
            
        csvFile.close()

    """ Builds a regex from the Standard Dictionary """
    def _drawingConfigRegex(drawingPrefixInfo) -> str:
        return (r"(" 
                + str(drawingPrefixInfo[0]) 
                + r"(?!([a-z]|[A-Z]|[0-9])))" 
                + r'-(\d{' 
                + str(drawingPrefixInfo[1]) 
                + r'})')
    
    """ Builds a regex from the product configuration dictionary """
    def _productCodeConfigRegex(productCodeTuple) -> str:
        """For every part of the product code, feed the function a tuple
            containing every option, and this will generate the regex expression
            to match the product code in all parser functions"""
        expression = r"("
        for arg in productCodeTuple:
            
            expression += "("
            for code in arg:
                expression += code
                expression += "|"
                
            expression = expression[:-1] + ")-"
            
        expression = expression[:-1] + ")"
        return expression

    """ Note that is a error flag was raised due to errors with csv file
        All operations involving part number regex are stalled """
    _drawingConfigDict()                                                # Build Dictionary
    _productCodeConfigDict()                                            # Build Dictionary
    for key in _CNDRWDIC.keys():                                        # Build Regex
        _CNDRWPRE.append(_productCodeConfigRegex(_CNDRWDIC.get(key)))
    for key in _STDRWDIC.keys():                                        # Build Regex
        _STDRWPRE.append(_drawingConfigRegex(_STDRWDIC.get(key)))
    
    partNumberRegex = str()                                             # Join both Regexes into One
    for prefix in _CNDRWPRE:                
        partNumberRegex = partNumberRegex + prefix + "|"
    for prefix in _STDRWPRE:
        partNumberRegex = partNumberRegex + prefix + "|"
    partNumberRegex = partNumberRegex[:-1]
    
    return partNumberRegex
    
def buildRevRegex() -> str:
    """Please note that this will match 1-3 letters followed by 0-3 numbers,
    This Regex does not discriminate much and should be used with span functions to
    Make sure it is not creating double matches"""
    return r'\b[A-Z][A-Z]?[A-Z]?(?![A-Z]|[a-z])[0-9]?[0-9]?[0-9]?(?![A-Z]|[a-z]|[0-9])'

def buildProductLines(ProductLinesCSV: Path) -> dict:
    with open(ProductLinesCSV, 'r') as csvFile:
        csvReader = csv.reader(csvFile)
        productFamilies: dict[list, list] = dict()
        
        for line in csvReader:
            family = line[0]
            productFamilies[family] = list()
            
            for i, cell in enumerate(line):
                if i == 0 or cell == '':
                    continue
                productFamilies[family].append(cell)
        
        csvFile.close()
        
    return productFamilies