# KiCADSamacSysImporter
A python scripts that imports [SamacSys](https://www.samacsys.com/) [ComponentSearchEngine](https://componentsearchengine.com/) ZIP files into a KiCAD project.

**Note:** This is an unofficial importer scripts written by [Uli Köhler](https://techoverflow.net) in order to make a customizable, platform-independent version of the SamacSys importer that is capable of managing *multiple projects*.

*Note:* This is not a GUI project, but is deliberately focused on making ComponentSearchEngine viable to be used on the command line

## What does KiCADSamacSysImporter do (and what not)

KiCADSamacSysImporter **does**:
* Provide a convenient command-line interface to import components into *project-local* KiCAD libraries
* Automatically import 3D models, schematic symbols and footprints from ZIPs downloaded from [ComponentSearchEngine](https://componentsearchengine.com/)
* Remove duplicately named components

KiCADSamacSysImporter **does not**:
* Automatically download ComponentSearchEngine ZIP files. You need to download them on the [ComponentSearchEngine](https://componentsearchengine.com/) website yourself.
* Provide a GUI

## Required project structure

Copy `ComponentSearchEngine-Import.py` into the root of your project, where your `[project name].pro` file is located, conveniently done using
```sh
wget -qO ComponentSearchEngine-Import.py https://raw.githubusercontent.com/ulikoehler/KiCADSamacSysImporter/master/ComponentSearchEngine-Import.py.py
```
The script will expect `libraries/[project name].lib` for project-local schematic symbols and the `libraries/footprints` folder for footprints plus the `libraries/3D` folder where STEP files will be placed.

The easiest way to generate a project with these files is to use our [open-source KiCAD project initializer script](https://techoverflow.net/2019/11/08/how-to-initialize-your-kicad-project-on-the-command-line/)

## How to use

Note that **you can't run the script from inside this repository**. You need to run it from within your project directory!

**Option 1: Import a specific ZIP file**
```sh
./ComponentSearchEngine-Import.py -f [ZIP file]
```

**Option 2: Import the most recent ZIP file from a directory**:
```sh
./ComponentSearchEngine-Import.py -l ~/Downloads
```
Note that this will select only files matching the glob `~/Downloads/LIB_*.zip`

Also see some related explanations in our blog posts:
* [What are KiCAD .lib files](https://techoverflow.net/2019/11/08/what-are-kicad-lib-files/)
