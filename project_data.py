"""This module contains data specific to the projects"""

from dataclasses import dataclass
from pathlib import Path

@dataclass
class PROJDIR():
    PROJECT_ROOT: Path = Path(r"X:\RESEARCH AND DEVELOPMENT\DrawingManager")
    PROGRAM: Path = Path(r"X:\RESEARCH AND DEVELOPMENT\DrawingManager\FOL-001-TestProgram#1")
    BACKUP: Path = Path(r"X:\RESEARCH AND DEVELOPMENT\DrawingManager\FOL-003-BackupProgram#1")
    WORKING: Path = Path(r"X:\RESEARCH AND DEVELOPMENT\DrawingManager\FOL-002-TestFolder#1")
    UPDATE_DRAWINGS: Path = Path(r"X:\RESEARCH AND DEVELOPMENT\DrawingManager\FOL-004-UpdatedDrawings")
    CS_500: Path = Path(r"X:\RESEARCH AND DEVELOPMENT\DrawingManager\FOL-005-TestFolder#2\Oil Water Seperators\CoolSkim\CS-500-019")
    BOM: Path = Path(r"X:\RESEARCH AND DEVELOPMENT\DrawingManager\FOL-007-TestFolder#3-BOMPulling")
    
@dataclass
class PROJDATA():
    FILE_TABLE: Path = Path(r"X:\RESEARCH AND DEVELOPMENT\DrawingManager\FOL-001-TestProgram#1\file_table.pickle")