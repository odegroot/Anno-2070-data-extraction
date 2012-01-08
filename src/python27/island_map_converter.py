'''
Converts game data files for islands to custom data formats readable by building layout tools
(v0.1 did not work, v0.2 is prove of concept only)

Proposed algorithm:
 1. load data/levels/... scenario+campaign www files - ???
 2. for each www file load all islands
 3. for each island compute all builblocking polygons
 4. draw the polygons and save as png for debugging
 5. convert drawings to usable formats
 + one-time function to copy all related files do src/rda/...

 to do: look at import/export format for http://code.google.com/p/anno-designer/

Created on 1.1.2012

@author: peter.hozak@gmail.com (http://anno2070.wikia.com/wiki/User:DeathApril)

'''


# i guess this will never work on Python 3, but just in case:
from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals
from future_builtins import * #@UnusedWildImport
    #do not use this because of struct.unpack ...
    #try:
    #    str = unicode
    #except NameError:
    #    pass


import math, json, re, os, shutil, sys #@UnusedImport
from pprint import pprint #@UnusedImport
from datetime import datetime
from struct import unpack
from operator import itemgetter
    #.isd files are not well-formed xml, no point in using xml parsers ...
    #from xml.etree import ElementTree as ET
try:
    from PIL import Image, ImageDraw #@UnusedImport
except ImportError:
    print("To download PIL, see http://www.pythonware.com/products/pil/\n")
    raise
try:
    import numpy as np #@UnusedImport
    import matplotlib.nxutils as nx
except ImportError:
    print("To download matplotlib, see http://matplotlib.sourceforge.net/users/installing.html\n")
    raise


__version__ = "0.5"

__folder = ".."
__island_maps = os.path.join(__folder, "rda", "island_maps")
__orig_data_folder = "C:\\Users\\Peter\\Documents\\ANNO 2070" # location of all extracted data files that are not on github
__isd_path = os.path.join(__island_maps, "isd")
__out_path = os.path.join(__island_maps, "converted_isd")

def main():
    isd_list = os.listdir(__isd_path)
    isd_list = ["normal.n_l22.isd"]
    for file_name in isd_list:
        isd_path = os.path.join(__isd_path, file_name)
        out_path = "result.png" #os.path.join(__out_path, file_name[:-4]+".png")
        print(isd_path)
        with open(isd_path, "rb") as f:
            isd_text = f.read()
        # splits to 3 strings - before, inside and after the element
        width = int( re.split(r"</?Width>", isd_text[:100])[1] )
        height = int( re.split(r"</?Height>", isd_text[:100])[1] )
        size = (width, height)
        tiles = [ 255 for y in range(height) for x in range(width) ] #@UnusedVariable
        adjust_tiles(tiles, size, isd_text)
        # test of result
#        png = Image.new("L", size)
#        png.putdata(tiles)
#        png = png.transpose(Image.FLIP_TOP_BOTTOM)
#        png.save(out_path)
    return None


def adjust_tiles(tiles, size, isd_text):
    ChunkMap = re.split(r"<ChunkMap>", isd_text)
    if len(ChunkMap) != 2:
        e = "Previous split should have resulted in 2 strings. {} found".format(len(ChunkMap))
        raise NotImplementedError(e)
    ChunkMap = ChunkMap[1]
    # first 2 characters after <Width> tag in <ChunkMap> => up to 99 chunks (= 1584 x 1584 tiles per island)
    width_chunks = int( re.split(r"<Width>", ChunkMap[:100])[1][:2].strip("<") )
    height_chunks = int( re.split(r"<Height>", ChunkMap[:100])[1][:2].strip("<") )
    elements = re.split(r"<Element>", ChunkMap)[1:]
    f = open("result.txt","w")
    for texture_index in (18, 29, 52, 71, 72, 74, 75, 76, 78, 79, 80, 82, 83, 84, 85, 86, 87, 94, 95, 96, 98, 99, 104):
        f.write("\n{}\n\n".format(texture_index))
        test_lines = [["\u25CB" for i in range(width_chunks)] for i in range(height_chunks)]
        for i in range(len(elements)):
            TexIndexData = re.split(r"<TexIndexData><TextureIndex>{}<[^C]*CDATA\[".format(texture_index), elements[i])[1:]
            if not TexIndexData:
                continue
            #data = TexIndexData[0][:293]
            test_lines[i//height_chunks][i%width_chunks] = "\u25A0"
        for test_line in reversed(test_lines):
            f.write(" ".join(test_line)+"\n")
    return None


def copy_island_files(ext):
    if ext == "isd":
        base_root = "islands\\"
    else:
        base_root = "levels\\"
    for root, dirs, files in os.walk(__orig_data_folder): #@UnusedVariable
        if base_root in root:
            prefix = re.sub(r"\\", ".", re.split(base_root+"\\", root)[1]) + "."
            for f in files:
                if ".{}".format(ext) in f:
                    print(os.path.join(__island_maps, ext, prefix, f))
                    shutil.copy(os.path.join(root, f), os.path.join(__island_maps, ext, prefix+f))


if __name__ == "__main__":
    start = datetime.now()
    #copy_island_files("png") # www, png, isd
    main()
    print("\n{}".format(datetime.now()-start))