from dataclasses import dataclass
from pathlib import Path
from .osi_configfunctions import buildPartRegex, buildProductLines, buildRevRegex

@dataclass
class OSIDIR:
    """Global Dataclass containing the Root Directories in the Engineering Drive"""
    
    CATALOG: Path = Path('X:/OSI CATALOG')
    SYSTEMS: Path = Path('X:/SYSTEMS')

    #CATALOG: Path = Path(r'C:\Users\info\PythonProj\DirectoryProject\OSI CATALOG')
    #SYSTEMS: Path = Path(r'C:\Users\info\PythonProj\DirectoryProject\SYSTEMS')
    
    FABPARTS: Path = Path('X:/FABRICATED PARTS')
    MECHSUB: Path = Path('X:/SUBASSEMBLY/MECHANICAL SUBASSEMBLY')
    ELECSUB: Path = Path('X:/SUBASSEMBLY/ELECTRICAL SUBASSEMBLY')
    PLUMSUB: Path = Path('X:/SUBASSEMBLY/PLUMBING SUBASSEMBLY')
    TANKASS: Path = Path('X:/SUBASSEMBLY/TANK ASSEMBLY')
    TANKSUB: Path = Path('X:/SUBASSEMBLY/TANK SUBASSEMBLY')
    
    COMPARTS: Path = Path('X:/PURCHASED PARTS/COMMERCIAL PARTS')
    ELEPARTS: Path = Path('X:/PURCHASED PARTS/ELECTRCIAL PARTS')
    HDWPARTS: Path = Path('X:/PURCHASED PARTS/HARDWARE')
    MTRPARTS: Path = Path('X:/PURCHASED PARTS/MOTORS')
    PKGPARTS: Path = Path('X:/PURCHASED PARTS/PACKAGING')
    PLMPARTS: Path = Path('X:/PURCHASED PARTS/PIPE HOSE FITTINGS')
    PMPPARTS: Path = Path('X:/PURCHASED PARTS/PUMPS')
    
    GRAITEMS: Path = Path('X:/GRAPHICS ITEMS')
    KITS: Path = Path('X:/KITS')
    MARKETING: Path = Path('X:/MARKETING')
    RENDER: Path = Path('X:/RENDERING')
    TOOLS: Path = Path('X:/TOOLS')
    
@dataclass
class APPCONFIG:
    """ These are shared config files and structures that can be used to make changes to the program
        Without having to recompile the entire progrma """
    STANDA_DWG_CSV: Path = Path('X:/PROGRAMS/DirectoryProject/config/StandardDrawingPrefixes.csv')
    CONFIG_DWG_CSV: Path = Path('X:/PROGRAMS/DirectoryProject/config/ConfigDrawingPrefixes.csv')
    PRODUC_LINE_CSV: Path = Path('X:/PROGRAMS/DirectoryProject/config/ProductLines.csv')
    SYSTEM_FOLDER_STRUCT: Path = Path('X:/PROGRAMS/DirectoryProject/config/System')
    
PART_NUM_REGEX = buildPartRegex(APPCONFIG.CONFIG_DWG_CSV, APPCONFIG.STANDA_DWG_CSV)
REV_REGEX = buildRevRegex()
PROD_FAMILIES = buildProductLines(APPCONFIG.PRODUC_LINE_CSV)