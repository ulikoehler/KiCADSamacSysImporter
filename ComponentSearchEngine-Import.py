#!/usr/bin/env python3
from shutil import copyfileobj
import zipfile
import glob
import os.path
import io
import re

__author__ = "Uli Köhler"
__license__ = "Apache License 2.0"

def_re = re.compile(r"DEF\s+([^\s]+)")
cmp_re = re.compile(r"$CMP\s+([^\s]+)")

class KiCADDocLibrary(object):

    def __init__(self, records=[]):
        self.records = records
        
    @staticmethod
    def read(file):
        # A record is everything between '$CMP ...' line and '$ENDCMP' line
        records = []
        current_record = None
        for line in file:
            line = line.strip()
            if line.startswith('$CMP '):
                current_record = []
            # Add line to record if we have any current record
            if current_record is not None:
                current_record.append(line)
            if line.startswith("$ENDCMP"):
                if current_record is not None:
                    records.append(current_record)
                    current_record = None
        return KiCADDocLibrary(records)

    def write(self, out):
        # Write header
        out.write("EESchema-DOCLIB  Version 2.0\n")
        # Write records
        for rec in self.records:
            out.write("#\n")
            for line in rec:
                out.write(line)
                out.write("\n")
        # Write footer
        out.write("#\n#End Doc Library\n")
    
    @property
    def names(self):
        # Find DEF ... lines
        names = []
        for rec in self.records:
            name = KiCADDocLibrary.record_name(rec)
            if name is not None:
                names.append(name)
        return names
    
    @staticmethod
    def record_name(record):
        """
        Return the name of the given record, or None if not identifiable
        """
        for line in record:
            m = def_re.search(line)
            if m is not None:
                return m.group(1)
        return None
                
    def remove_by_name(self, name_to_remove):
        """
        Remove all records that have a given name
        """
        new_records = []
        for record in self.records:
            if KiCADSchematicSymbolLibrary.record_name(record) != name_to_remove:
                new_records.append(record)
        self.records = new_records

        
class KiCADSchematicSymbolLibrary(object):
    def __init__(self, records=[]):
        self.records = records
        
    @staticmethod
    def read(file):
        # A record is everything between 'DEF ...' line and 'ENDDEF' line
        records = []
        current_record = None
        current_comment_lines = [] # 
        for line in file:
            line = line.strip()
            if line.startswith("#encoding"):
                continue # Ignore - we always use #encoding utf-8
            # Comment line processing
            if line.startswith("#"):
                current_comment_lines.append(line)
            # Start of record
            if line.startswith('DEF '):
                current_record = current_comment_lines
                current_comment_lines = []
            # Add line to record if we have any current record
            if current_record is not None:
                current_record.append(line)
            if line.startswith("ENDDEF"):
                if current_record is not None:
                    records.append(current_record)
                    current_record = None
            # Clear comment lines
            # We can only do this now to avoid clearing them before
            #  they are used in the DEF clause
            if not line.startswith("#"):
                current_comment_lines = []
        return KiCADSchematicSymbolLibrary(records)
    
    @property
    def names(self):
        # Find DEF ... lines
        names = []
        for rec in self.records:
            name = KiCADSchematicSymbolLibrary.record_name(rec)
            if name is not None:
                names.append(name)
        return names
    
    @staticmethod
    def record_name(record):
        """
        Return the name of the given record, or None if not identifiable
        """
        for line in record:
            m = def_re.search(line)
            if m is not None:
                return m.group(1)
        return None
                
    def remove_by_name(self, name_to_remove):
        """
        Remove all records that have a given name
        """
        new_records = []
        for record in self.records:
            if KiCADSchematicSymbolLibrary.record_name(record) != name_to_remove:
                new_records.append(record)
        self.records = new_records
        
    def write(self, out):
        # Write header
        out.write("EESchema-LIBRARY Version 2.4\n#encoding utf-8\n")
        # Write records
        for rec in self.records:
            for line in rec:
                out.write(line)
                out.write("\n")
        # Write footer
        out.write("#\n#End Library\n")

def identify_project_name(directory="."):
    """
    Identify the project name by identifying the project file
    """
    project_files = glob.glob(os.path.join(directory, "*.pro"))
    if len(project_files) == 1:
        return project_files[0].rpartition(".")[0] # Just the prefix without ".pro"
    else:
        raise(f'Found {len(project_files)} .pro files instead of the expected 1: {project_files}')

def extract_relevant_files(filename):
    """
    Extract only KiCAD-relevant files from a ComponentSearchEngine ZIP files
    """
    with zipfile.ZipFile(filename) as thezip:
        for zipinfo in thezip.infolist():
            partname = zipinfo.filename.partition("/")[0] # = name of the toplevel dir
            filename_without_tldir = zipinfo.filename.partition("/")[-1]
            second_level_dir = filename_without_tldir.partition("/")[0]
            # Skip files which are not relevant
            if not second_level_dir in ["KiCad", "3D"]:
                continue
            with thezip.open(zipinfo) as thefile:
                yield partname, filename_without_tldir, thefile

def import_zip(filename, dry_run=False):
    for partname, filename, handle in extract_relevant_files(filename):
        canonical = filename.rpartition("/")[-1]
        ext = filename.rpartition(".")[-1]

        if ext == 'stp': # 3D model
            if not dry_run:
                with open(f"libraries/3D/{canonical}", "wb") as outfile:
                    copyfileobj(handle, outfile)
        elif ext == 'kicad_mod': # Footprint
            if not dry_run:
                with open(f"libraries/footprints/{canonical}", "wb") as outfile:
                    copyfileobj(handle, outfile)
        elif ext == 'lib': # Schematic symbol
            new_lib = KiCADSchematicSymbolLibrary.read(io.TextIOWrapper(handle, encoding="utf-8"))
            # Get name of the one record to insert
            name_to_insert = KiCADSchematicSymbolLibrary.record_name(new_lib.records[0])
            # Insert into library
            project_name = identify_project_name()
            with open(f"libraries/{project_name}.lib", "r+") as libfile:
                current_lib = KiCADSchematicSymbolLibrary.read(libfile)
                # Remove old records with that name
                current_lib.remove_by_name(name_to_insert)
                # Insert new record with that name
                current_lib.records.append(new_lib.records[0])
                # Write updated library
                if not dry_run:
                    current_lib.write(libfile)
        elif ext == 'dcm': # Schematic symbol
            new_lib = KiCADDocLibrary.read(io.TextIOWrapper(handle, encoding="utf-8"))
            # Get name of the one record to insert
            name_to_insert = KiCADDocLibrary.record_name(new_lib.records[0])
            # Insert into library
            project_name = identify_project_name()
            with open(f"libraries/{project_name}.dcm", "r+") as libfile:
                libdata = libfile.read()
                current_doclib = KiCADDocLibrary.read(libfile)
                # Remove old records with that name
                current_doclib.remove_by_name(name_to_insert)
                # Insert new record with that name
                current_doclib.records.append(new_lib.records[0])
                # Write updated library
                if not dry_run:
                    current_doclib.write(libfile)
        elif ext in ['stl', 'wrl', 'mod']:
            pass # Ignore those files
        else:
            print(filename)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("-f", "--files", nargs="*", help="Select a specific file to import")
    parser.add_argument("-l", "--latest", help="Import the most recently changed files from the given directory.")
    parser.add_argument("-n", "--number", type=int, default=1, help="For -l/--latest: How many to import")
    parser.add_argument("-d", "--dry", action="store_true", help="Do not modify or copy libraries, just print what would be done")
    args = parser.parse_args()

    if args.latest:
        print(f"Importing latest {args.number} LIB_*.zip file(s) in {args.latest}...")
        all_files = glob.glob(os.path.join(args.latest, "LIB_*.zip"))
        most_recently_modified_zips = sorted(all_files, key=lambda t: -os.stat(t).st_mtime)
        # Import each file
        to_import = most_recently_modified_zips[:args.number]
        for file in to_import:
            print(f"Importing {file}")
            import_zip(file, args.dry)

    if args.files is not None:
        for file in args.files:
            print(f"Importing {file}")
            import_zip(file, args.dry)
