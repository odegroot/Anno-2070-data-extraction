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
#from xml.etree import ElementTree as ET # not working :((
try:
    from PIL import Image, ImageDraw
except ImportError:
    print("To download PIL, see http://www.pythonware.com/products/pil/")
    raise


__version__ = "0.3"
__first_bit_shift = 6
__final_bit_shift = 12 - __first_bit_shift


def _transform(rgb):
    # to do: create a mapping from actual .png colors ;))
    r, g, b = rgb
    if b > max(r,g):
        rgb = (0, 0, 255)
    elif g > 80 or g > 35 and g > r:
        rgb = (0, 255, 0)
    else:
        rgb = (255, 0, 0)
    return rgb

def coordinates_from_bytes(b):
    # it looks like the CDATA[] contains 20 bytes (160 bits) = hopefully 5 x longs (32-bit integers), little endian byte order
    # (16, x, 0, y, 0) where x and y are coordinates in subtiles (1 tile = 2**12 subtiles)
    try: # python 3.2
        x = int.from_bytes(b[4:8], 'little')
        y = int.from_bytes(b[12:16], 'little')
    except AttributeError: # python 2.7
        from struct import unpack
        x = unpack(str("<l"), b[4:8])[0]
        y = unpack(str("<l"), b[12:16])[0]
    # + 1<<11 is here to shift coordinates from corners to the center of tiles (found out by trial and error)
    # >> __first_bit_shift helps to lower the resolution of subtiles to acceptable levels to draw polygons (performance issues)
    x = (x + (1<<11)) >> __first_bit_shift
    y = (y + (1<<11)) >> __first_bit_shift
    return (x, y)

def convert_polygons_to_tiles(polygons, island_size, out_test_file=None):
    size = [i << __final_bit_shift for i in island_size] # island size is a tuple (x,y) x=width, y=height
    
    png = Image.new("RGBA", size)
    draw = ImageDraw.Draw(png)
    print("Computing polygons:")
    for i in range(len(polygons)):
        print("   polygon {}".format(i))
        polygon = [(x, size[1]-y) for x, y in polygons[i]]
        draw.polygon(polygon, fill=(255,0,0))
    del draw
    
    png = png.resize(island_size)
    if out_test_file:
        png.save(out_test_file)
    
    pixels = png.load()
    tiles = "" # internal text format - 1 letter for each pixel
    for y in range(island_size[1]):
        for x in range(island_size[0]):
            p = pixels[x, y]
            if p == (0,0,0,0):
                tiles += " "
            elif p == (255,0,0,255):
                tiles += "r"
            elif p == (0,255,0,255):
                tiles += "G"
            elif p == (0,0,255,255):
                tiles += "b"
            else:
                tiles += "?"
        tiles += "\n"
    return tiles

def test_isd():
    isd_path = "..//rda//island_maps//data3.levels.islands.normal.n_l22.isd"
    with open(isd_path, "rb") as f:
        isd_text = f.read()
    BuildBlocker = re.split(r"</?BuildBlockerShapes>", isd_text) # splits to 3 strings - before, inside and after the element
    if len(BuildBlocker) != 3:
        e = "Previous split should have resulted in 3 strings. {} found in {}".format(len(BuildBlocker), isd_path)
        raise NotImplementedError(e)
    BuildBlocker = BuildBlocker[1].strip(b"</i>Polygon\n\r")
    polygons = re.split(r"</Polygon>\r\n</i>\r\n<i><Polygon>", BuildBlocker)
    for i in range(len(polygons)):
        polygon = polygons[i].strip(b"</i>\n\rCDATA[]")
        points = re.split(r"]</i>\r\n<i>CDATA\[", polygon)
        for j in range(len(points)):
            p = points[j]
            if len(p) != 20:
                e = "Each polygon should be 20 bytes. {} bytes found in polygon {} in {}".format(len(p), i, isd_path)
                raise NotImplementedError(e)
            x, y = coordinates_from_bytes(p)
            points[j] = (x, y)
        polygons[i] = points
    tiles = convert_polygons_to_tiles(polygons, (240,240), "result.png")
    
    with open("result.txt", "w") as f:
        f.write(tiles)
    return None

if __name__ == "__main__":
    test_isd()
    