'''
Converts game data files for islands to custom data formats readable by building layout tools


Proposed algorithm:
 ?!?
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

import os, sys #@UnusedImport
try:
    from PIL import Image, ImageDraw
except ImportError:
    print("To download PIL, see http://www.pythonware.com/products/pil/")
    raise

__version__ = "0.1"

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

def test():
    # it looks like the CDATA[] contains 20 bytes (160 bits) = hopefully 5 x 32-bit ints, little endian byte order
    # first number is always 16, third and fifth are 0
    # second and fourth numbers are hopefully coordinates in subtiles (1 tile = 2**11 subtiles)
    bit_shift = 11
    polygon = []
    with open("test.isd", "rb") as f:
        while True:
            i_coordinates = f.read(20)
            if not i_coordinates:
                break
            try: # python 3.2
                x = int.from_bytes(i_coordinates[4:8], 'little') >> bit_shift
                z = int.from_bytes(i_coordinates[12:16], 'little') >> bit_shift
            except AttributeError: # python 2.7
                from struct import unpack
                x = unpack(str("<l"), i_coordinates[4:8])[0] >> bit_shift
                z = unpack(str("<l"), i_coordinates[12:16])[0] >> bit_shift
            polygon.append((x, z))
    print(polygon)
    
    

if __name__ == "__main__":
    test()
    #print(2**11)
    