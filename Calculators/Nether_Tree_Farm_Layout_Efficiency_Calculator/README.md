# Nether-Tree-Farm-Layout-Efficiency-Calculator
made by ncolyer on the 17/03/2023

A program that takes an input of a 7x27x7 (XYZ) schematic in the .litematic format, representing the blocks a given
nether tree farm layout harvests per cycle, and decodes the 3D data inside that file to compare it to pre-calculated
heatmaps in a .xlsx file to work out the average stems, shroomlights and wart blocks harvested per cycle for that
nether tree farm layout

TUTORIAL/SHOWCASE VID GODO WATCH FIRST: https://youtu.be/mShxTNPfXZc

For more info on how this and the heatmaps were made visit the Huge Fungi Huggers Discord Server: https://discord.gg/EKKkyfcPPV

Make sure you install the required libraries with the following commands:
- `pip install litemapy`
- `pip install openpyxl`

Credit to SmylerMC for the litemapy library:
- https://github.com/SmylerMC/litemapy/tree/9d9c159bce3eab33ffa820c7630ac97c8bef7a7a
Litematica by Masa:
- https://www.curseforge.com/minecraft/mc-mods/litematica
Python IDE (PyCharm):
- https://www.jetbrains.com/pycharm/download/#section=windows

HOW TO USE:
1. MAKE SURE YOU RUN THE PYTHON FILE IN THE SAME FOLDER/DIRECTORY AS THE `heatmaps.xlsx` FILE!
2. Load into a minecraft world and select a 7x27x7 area with litematica with the bottom of it centred on the block above a nylium block
3. From there use the following key to replicate your nether tree farm's piston layout:
	- Red Concrete: Any block within your farms layout that isn't affected by Vines Region Manipulation (VRM) aka vrm0
	- Blue Concrete: A block within your layout that sits 1 block above a VRM wart block aka vrm1
	- Cyan Concrete: A block within your layout that sits 2 blocks above a VRM wart block aka vrm2
 	- Light Blue Concrete: A block within your layout that sits 3 blocks above a VRM wart block aka vrm3
	- Air: A block that your piston layout doesn't harvest
4. Save the schematic to a new folder in your .minecraft\schematics folder called `ntf_heatmap_layouts`
5. Open up and run the `HugeFungusHeatmapCalculator.py` file using a Python editor of your choice
6. Follow the instructions/prompts it prints to terminal and happy nether tree farming 

- Note you can include any other blocks within the 7x27x7 area and the calculator will still run fine and 
	it'll just print a msg to the log notifying you which blocks were invalid and where they're 
	positioned within the selection

- The included 'full_vrm0_layout.litematic' file is an entire nether tree and if you run that through the calculator
  it should return the average stems shroomlights and wart blocks to within 9 significant figures

Please feel free to message me on discord @ncolyer#4256
