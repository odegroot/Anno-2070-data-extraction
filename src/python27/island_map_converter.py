'''
Converts island .png maps to custom data formats readable by building layout tools

This script should be fully compatible with Python 3, except i found PIL for 2.4 - 2.7 only (and SciPy didn't work on my computer) 

Proposed algorithm:
 1. create a mapping from each color to 3 values - "green" = "buildable", "red" = "blocked", "blue" = "water"
 2. load .png to 2 dimensional list - scipy.misc.imread ??
 3. convert the list and store the result in various formats

 + one-time function to copy all related .png files do src/rda/island_pngs

 to do: look at import/export format for http://code.google.com/p/anno-designer/

Created on 1.1.2012

@author: peter.hozak@gmail.com (http://anno2070.wikia.com/wiki/User:DeathApril)

'''


# Forward compatibility with Py3k
from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals
from future_builtins import * #@UnusedWildImport
try:
    str = unicode #@ReservedAssignment
except NameError:
    pass
import os, sys #@UnusedImport
try:
    from PIL import Image
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
    png = Image.open("..\\rda\\island_pngs\\data3.levels.scenarios.multiplayer.01.png").convert("RGB")
    size = png.size
    pixels = png.load()
    for y in range(size[1]):
        for x in range(size[0]):
            pixels[x, y] = _transform(pixels[x, y])
    png.save("test.png")
    
if __name__ == "__main__":
    test()