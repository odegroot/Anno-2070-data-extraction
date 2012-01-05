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


# Forward compatibility with Py3k
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
from datetime import datetime, timedelta
#from xml.etree import ElementTree as ET # not working :((
try:
    from PIL import Image, ImageDraw #@UnusedImport
except ImportError:
    print("To download PIL, see http://www.pythonware.com/products/pil/")
    raise
try:
    import numpy as np #@UnusedImport
    import matplotlib.nxutils as nx
except ImportError:
    print("To download matplotlib, see http://matplotlib.sourceforge.net/users/installing.html")
    raise

__version__ = "0.3"
__first_bit_shift = 0 # the bigger this number is, the better performance, but more false-positives of blocked tiles in result
__final_bit_shift = 12 - __first_bit_shift
__sample_offset_x = (1<<11)
__sample_offset_y = __sample_offset_x

def coordinates_from_bytes(b):
    # it looks like the CDATA[] contains 20 bytes (160 bits) = hopefully 5 x longs (32-bit integers), little endian byte order
    # (16, x, 0, y, 0) where x and y are coordinates in subtiles (1 tile = 2**12 x 2**12 subtiles)
    try: # python 3.2
        x = int.from_bytes(b[4:8], 'little')
        y = int.from_bytes(b[12:16], 'little')
    except AttributeError: # python 2.7
        from struct import unpack
        x = unpack(str("<l"), b[4:8])[0]
        y = unpack(str("<l"), b[12:16])[0]
    # >> __first_bit_shift helps to lower the resolution of subtiles to acceptable levels to draw polygons (performance issues)
    x = x >> __first_bit_shift
    y = y >> __first_bit_shift
    return (x, y)

def test_isd():
    isd_path = "..//rda//island_maps//data3.levels.islands.normal.n_l22.isd"
    print("{}".format(isd_path.split(".")[-2]))
    with open(isd_path, "rb") as f:
        isd_text = f.read()
    
    BuildBlocker = re.split(r"</?BuildBlockerShapes>", isd_text) # splits to 3 strings - before, inside and after the element
    if len(BuildBlocker) != 3:
        e = "Previous split should have resulted in 3 strings. {} found in {}".format(len(BuildBlocker), isd_path)
        raise NotImplementedError(e)
    BuildBlocker = BuildBlocker[1].strip(b"</i>Polygon\n\r")
    polygons = re.split(r"</Polygon>\r\n</i>\r\n<i><Polygon>", BuildBlocker)
    
    width = 240
    height = 240
    island_size = (width, height)
    # list for tiles - accessed by [y*width + x]
    tiles = [ 0 for y in range(height) for x in range(width) ] #@UnusedVariable
    # which points should be sampled from polygons - multiple access needed => list comprehension
    sample_points = [ (x*(1<<__final_bit_shift)+__sample_offset_x, y*(1<<__final_bit_shift)+__sample_offset_y) for y in range(height) for x in range(width) ]
    for i in range(len(polygons)):
        polygon = polygons[i].strip(b"</i>\n\rCDATA[]")
        points = re.split(r"]</i>\r\n<i>CDATA\[", polygon)
        min_x = island_size[0]
        min_y = island_size[1]
        max_x = 0
        max_y = 0
        for j in range(len(points)):
            p = points[j]
            if len(p) != 20:
                e = "Each polygon should be 20 bytes. {} bytes found in polygon {} in {}".format(len(p), i, isd_path)
                raise NotImplementedError(e)
            x, y = coordinates_from_bytes(p)
            points[j] = (x, y)
            min_x = min(min_x, x>>12)
            min_y = min(min_y, y>>12)
            max_x = max(max_x, x>>12)
            max_y = max(max_y, y>>12)
        
        tiles_needed = [ y*width + x for x in range(min_x, max_x+1) for y in range(min_y, max_y+1) ]
        sample_points_needed = [ sample_points[y*width + x] for x in range(min_x, max_x+1) for y in range(min_y, max_y+1) ]
        # http://matplotlib.sourceforge.net/faq/howto_faq.html#test-whether-a-point-is-inside-a-polygon
        mask = nx.points_inside_poly(np.array(sample_points_needed, int), np.array(points, int))
        for k in range(len(tiles_needed)):
            if mask[k]:
                tiles[tiles_needed[k]] = 255 
    
    # test of result
    png = Image.new("L", island_size)
    png.putdata(tiles)
    png = png.transpose(Image.FLIP_TOP_BOTTOM)
    png.save("result.png")
    
    return None

if __name__ == "__main__":
    start = datetime.now()
    test_isd()
    print("\n{}".format(datetime.now()-start))