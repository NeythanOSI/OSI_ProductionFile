"""This will need to be appended to the directory project when this is integrated"""
from .osi_directory import OSIDIR

PREFIX_LOOKUP_TABLE = {
    """Dictionary that take the drawing part number prefix as a key, and returns where
    those drawings are stored in the Engineering Directory"""
    # Fabricated Parts
    "FA": OSIDIR.FABPARTS,
    
    # Subassembly 
    "MSA": OSIDIR.MECHSUB,
    'ESA': OSIDIR.ELECSUB,
    "PSA": OSIDIR.PLUMSUB,
    "TA": OSIDIR.TANKASS,
    "TSA": OSIDIR.TANKSUB,
    
    # Purchased Parts
    "C": OSIDIR.COMPARTS,       # Note Prefix is identical to commercial
    "EE": OSIDIR.ELEPARTS,
    "HW": OSIDIR.HDWPARTS,
    "MTR": OSIDIR.MTRPARTS,
    "PKG": OSIDIR.PKGPARTS,
    "P": OSIDIR.PLMPARTS,
    "PM": OSIDIR.PMPPARTS,
    
    # Others
    "GA": OSIDIR.GRAITEMS,
    "KT": OSIDIR.KITS,
    "MKT": OSIDIR.MARKETING,
    "TL": OSIDIR.TOOLS
}