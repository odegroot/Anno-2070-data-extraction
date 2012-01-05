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


import json, re, os, sys #@UnusedImport
from pprint import pprint #@UnusedImport
from datetime import datetime
from struct import unpack
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

__version__ = "0.3"
__sample_offset_x = 1<<11
__sample_offset_y = __sample_offset_x

def coordinates_from_bytes(b, unpack_string):
    # it looks like standard CDATA[] contains 20 bytes (160 bits) = hopefully 5 x longs (32-bit integers), little endian byte order
    # (16, x, 0, y, 0) where x and y are coordinates in subtiles (1 tile = 2**12 x 2**12 subtiles)
    x0, x1, y0, y1 = (4,8,12,16)
    x = unpack(str(unpack_string), b[x0:x1])[0]
    y = unpack(str(unpack_string), b[y0:y1])[0]
    if type(x) == float:
        x = int(x * (1<<12))
        y = int(y * (1<<12))
    return (x, y)

def adjust_tiles(tiles, size, isd_text, element_name, polygons_split, out_color, unpack_string="<l"):
    element = re.split(r"</?{}>".format(element_name), isd_text) # splits to 3 strings - before, inside and after the element
    if len(element) != 3:
        e = "Previous split should have resulted in 3 strings. {} found".format(len(element))
        raise NotImplementedError(e)
    element = element[1]
    if polygons_split:
        polygons = re.split(r"{}".format(polygons_split, flags=re.DOTALL), element)
    else:
        polygons = [element]
    
    width = size[0]
    height = size[1]
    # list for tiles - accessed by [y*width + x]
    # which points should be sampled from polygons - multiple access needed => list comprehension
    sample_points = [ (x*(1<<12)+__sample_offset_x, y*(1<<12)+__sample_offset_y) for y in range(height) for x in range(width) ]
    
    for i in range(len(polygons)):
        polygon = re.sub(r"^[^[]*\[|][^]]*$", b"", polygons[i])
        points = re.split(r"]<.*?>CDATA\[", polygon, flags=re.DOTALL)
        min_x = width
        min_y = height
        max_x = 0
        max_y = 0
        for j in range(len(points)):
            p = points[j]
            if len(p) not in (20, 16):
                e = "Each polygon point should be 20 or 16 bytes. {} bytes found in point {}/0-{} in polygon {}/0-{}:".format(len(p), j, len(points)-1, i, len(polygons)-1)
                print(p)
                raise NotImplementedError(e)
            x, y = coordinates_from_bytes(p, unpack_string)
            points[j] = (x, y)
            x = x >> 12
            y = y >> 12
            min_x = min(min_x, x)
            min_y = min(min_y, y)
            max_x = max(max_x, x)
            max_y = max(max_y, y)
        
        #print(min_x, min_y, max_x, max_y)
        tiles_needed = [ y*width + x for x in range(min_x, max_x+1) for y in range(min_y, max_y+1) ]
        sample_points_needed = [ sample_points[y*width + x] for x in range(min_x, max_x+1) for y in range(min_y, max_y+1) ]
        # http://matplotlib.sourceforge.net/faq/howto_faq.html#test-whether-a-point-is-inside-a-polygon
        mask = nx.points_inside_poly(np.array(sample_points_needed, int), np.array(points, int))
        for k in range(len(tiles_needed)):
            if mask[k]:
                tiles[tiles_needed[k]] = out_color
                
    return None

def test_isd():
    isd_path = "..//rda//island_maps//data3.levels.islands.normal.n_l22.isd"
    print("{}".format(isd_path.split(".")[-2]))
    with open(isd_path, "rb") as f:
        isd_text = f.read()
    
    width = 240
    height = 240
    size = (width, height)
    
    tiles = [ 0 for y in range(height) for x in range(width) ] #@UnusedVariable
    adjust_tiles(tiles, size, isd_text,
                 "SurfLines",
                 None,
                 150,
                 "<f") # looks like a float instead of subtiles
    adjust_tiles(tiles, size, isd_text,
                 "CoastBuildingLines",
                 "</Points>[^P]*Points>",
                 50)
    adjust_tiles(tiles, size, isd_text,
                 "BuildBlockerShapes",
                 "</Polygon>\r\n</i>\r\n<i><Polygon>",
                 255)
    
    # test of result
    png = Image.new("L", size)
    png.putdata(tiles)
    png = png.transpose(Image.FLIP_TOP_BOTTOM)
    png.save("result.png")
    
    return None

if __name__ == "__main__":
    start = datetime.now()
    test_isd()
    print("\n{}".format(datetime.now()-start))