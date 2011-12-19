# coding=utf_8
'''
Parses icons.xml and creates a mapping from GUIDs to icon filenames, including overlays.

Created on Dec 19, 2011

@author: Oscar de Groot (Grilse)
'''

import os
import xml.etree.ElementTree as ET

__game_version  = "Anno 2070 v1.02"

__project_root  = os.path.join('..', '..')
__rda_folder    = os.path.join(__project_root, "src", "rda")
__icons_xml     = os.path.join(__rda_folder, "patch3", "data", "config", "game", "icons.xml")
#__icon_folder   = 'http://odegroot.nl/anno2070/img/orig/icon/'

def get_guid_to_icon_dict():
    IconFileNames = {}
    
    for i in ET.parse(__icons_xml).findall("i"):
        GUID = i.findtext("GUID")
        
        icon_base = None
        icon_overlay = None
        icons = i.findall('Icons/i')
        
        for icon in icons:
            # VariationID determines what kind of icon this is.
            # Possible values and their meaning are defined in data/config/gui/iconvariations.xml
            # 0/None is the primary icon
            # 13 is an overlay icon.
            # 64 is Toggled, 192 is Toggled Hover
            if icon.findtext('VariationID') == None:
                if icon_base == None:
                    icon_base = icon
                else:
                    raise Exception(GUID + ' has multiple base icons.')
            elif icon.findtext('VariationID') == '13':
                if icon_overlay == None:
                    icon_overlay = icon
                else:
                    raise Exception(GUID + ' has multiple overlay icons.')
            elif icon.findtext('VariationID') == '64':
                if icon_base == None:
                    icon_base = icon
            else:
                # Ignore other icon variations.
                pass
        
        if icon_base == None: raise Exception(GUID + ' has no base icon.')
        
        IconFileID = icon_base.findtext("IconFileID")
        IconIndex = icon_base.findtext("IconIndex") or '0'
            
        IconFileNames[GUID] = { 'icon.base': "icon_{}_{}.png".format(IconFileID, IconIndex) }
        
        if icon_overlay != None :
            IconFileNames[GUID]['icon.overlay'] = "icon_{}_{}.png".format(icon_overlay.findtext("IconFileID"), icon_overlay.findtext("IconIndex"))
            pass
        
    return IconFileNames