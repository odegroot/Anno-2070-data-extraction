'''
Placeholder for future script - Converts island .png maps to custom data formats readable by building layout tools

Created on 1.1.2012

@author: peter.hozak@gmail.com (http://anno2070.wikia.com/wiki/User:DeathApril)

'''

# proposed algorithm:
# 1. create a mapping from each color to 3 values - "green" = "buildable", "red" = "blocked", "blue" = "water"
# 2. load .png to 2 dimensional list - scipy.misc.imsave ??
# 3. convert the list and store the result in various formats

# + one-time function to copy all related .png files do src/rda/island_pngs


# to do: look at import/export format for http://code.google.com/p/anno-designer/
# to do: figure out how to manage dependencies like "import scipy"