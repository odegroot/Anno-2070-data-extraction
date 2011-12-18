# coding=utf_8
'''
Generates a JSON file with the properties of all research projects.

Created on Dec 18, 2011

@author: Oscar de Groot
'''

import json
import re
from xml.etree import ElementTree as ET

__version__ = "0.1"
__game_version__ = "1.02"

# global settings
folder = "..\\rda\\"
out_folder = "..\\..\\target\\"
assets_path = folder + "patch3\\data\\config\\game\\assets.xml"
icons_txt_path = folder + "eng3\\data\\loca\\eng\\txt\\icons.txt"
guids_txt_path = folder + "eng3\\data\\loca\\eng\\txt\\guids.txt"
properties_path = folder + "patch3\\data\\config\\game\\properties.xml"
icons_path = folder + "patch3\\data\\config\\game\\icons.xml"
icons_prefix = "icon_"
icons_midfix = "_"
icons_postfix =".png"
icons_index_shift = 0
output_name = "list_of_buildings_v" + __version__ + ".json"
model_name = "list_of_buildings_model_v" + __version__ + ".json"
model_url = "http://aprilboy.e404.sk/anno2070/"


def get_building_list():
    AssetGroups = ET.parse(assets_path).findall(".//Group")
    IconFileNames = parse_IconFileNames()
    Eng1 = parse_Eng1()
    ProductGUIDs = parse_ProductGUIDs()
    buildings = []
    
    for top_group in AssetGroups:
        if top_group.find("Name").text == "Buildings":
            break
    
    for faction in top_group.findall("Groups/Group"):
        faction_name = faction.find("Name").text
        for group in faction.findall(".//Groups/Group"):
            group_name = group.find("Name").text
            if group_name == "farmfield":
                group_name = "farmfields"
            for asset in group.findall("Assets/Asset"):
                try:
                    template = asset.find("Template").text
                    if template == "SimpleObject":
                        # SimpleObjects (farm_field_rows and pirates_props) won't be needed in this database
                        continue
                except:
                    # scientist_academy does not even hava a Template property, wtf ???
                    continue
                GUID = int(asset.find("Values/Standard/GUID").text)
                Name = asset.find("Values/Standard/Name").text
                b = {"GUID": GUID, "Name": Name}
                try:    b["Eng1"] = Eng1[GUID]
                except: pass
                try:    b["IconFileName"] = IconFileNames[GUID]
                except: pass
                try:    b["Faction"] = faction_name
                except: pass
                try:    b["Group"] = group_name
                except: pass
                try:    b["Template"] = template
                except: pass
                try:    b["InfluenceRadius"] = int(asset.find("Values/Influence/InfluenceRadius").text)
                except: pass
                try:    b[".ifo"] = asset.find("Values/Object/Variations/Item/Filename").text.replace(".cfg",".ifo").replace("data\\graphics\\buildings\\", "")
                except: pass
                try:    b["MaxResidentCount"] = int(asset.find("Values/ResidenceBuilding/MaxResidentCount").text)
                except: pass
                try:
                        (x, z) = get_BuildBlocker( b[".ifo"] )
                        b["BuildBlocker.x"] = x
                        b["BuildBlocker.z"] = z
                except: pass
                
                try:    b["FarmField.GUID"] = int(asset.find("Values/Farm/FarmFieldGUID").text)
                except: pass
                if "FarmField.GUID" in b:
                        try:    b["FarmField.Count"] = int(asset.find("Values/Farm/FarmfieldCount").text)
                        except: pass
                        try:    b["FarmField.Fertility"] = asset.find("Values/Farm/Fertility").text
                        except: pass
                
                try:    
                        b["Production.Product.Name"] = asset.find("Values/WareProduction/Product").text
                        #default values:
                        b["Production.ProductionTime"] = 20000 #miliseconds
                        b["Production.ProductionCount"] = 1000 #kilograms
                        b["Production.RawNeeded1"] = 1000
                        b["Production.RawNeeded2"] = 1000
                except: pass
                if "Production.Product.Name" in b:
                        try:    b["Production.Product.GUID"] = ProductGUIDs[ b["Production.Product.Name"] ]
                        except: pass
                        try:    b["Production.Product.Eng1"] = Eng1[ b["Production.Product.GUID"] ]
                        except: raise
                        try:    b["Production.ProductionTime"] = int(asset.find("Values/WareProduction/ProductionTime").text)
                        except: pass
                        try:    b["Production.ProductionCount"] = int(asset.find("Values/WareProduction/ProductionCount").text)
                        except: pass
                        try:    b["Production.RawMaterial1"] = asset.find("Values/Factory/RawMaterial1").text
                        except: del b["Production.RawNeeded1"]
                        try:    b["Production.RawMaterial2"] = asset.find("Values/Factory/RawMaterial2").text
                        except: del b["Production.RawNeeded2"]
                        try:    b["Production.RawNeeded1"] = int(asset.find("Values/Factory/RawNeeded1").text)
                        except: pass
                        try:    b["Production.RawNeeded2"] = int(asset.find("Values/Factory/RawNeeded2").text)
                        except: pass
                        TicksPerMinute = 60000 / b["Production.ProductionTime"]
                        b["Production.ProductionTonsPerMinute"] = ( b["Production.ProductionCount"] / 1000 ) * TicksPerMinute 
                        try:    b["Production.RawNeeded1TonsPerMinute"] = ( b["Production.RawNeeded1"] / 1000 ) * b["Production.ProductionTonsPerMinute"]
                        except: pass
                        try:    b["Production.RawNeeded2TonsPerMinute"] = ( b["Production.RawNeeded2"] / 1000 ) * b["Production.ProductionTonsPerMinute"]
                        except: pass
                buildings.append(b)
    return buildings

def parse_Eng1():
    Eng1 = {}
    
    # The text files are encoded in UTF-16.
    for line in open(icons_txt_path, encoding="utf_16_le"): 
        result = re.search("(\\d*)=(.*)", line)
        if result:
            Eng1[int(result.group(1))] = result.group(2)
    for line in open(guids_txt_path, encoding="utf_16_le"):
        result = re.search("(\\d*)=(.*)", line)
        if result:
            Eng1[int(result.group(1))] = result.group(2)
    return Eng1

def parse_ProductGUIDs():
    ProductGUIDs = {}
    
    for p in ET.parse(properties_path).findall(".//ProductIconGUID/*"):
        if p.tag != "icon":
            ProductGUIDs[p.tag] = int(p.find("icon").text)
    return ProductGUIDs

def parse_IconFileNames():
    IconFileNames = {}
    
    for i in ET.parse(icons_path).findall("i"):
            IconFileID = i.find("Icons/i/IconFileID").text
            try:
                IconIndex = str(int(i.find("Icons/i/IconIndex").text) + icons_index_shift)
            except:
                IconIndex = "1"
            IconFileNames[int(i.find("GUID").text)] = icons_prefix + IconFileID + icons_midfix + IconIndex + icons_postfix
    return IconFileNames

def get_BuildBlocker(detail_path):
    ifo_path = folder + "data2\\graphics\\buildings\\" + detail_path
    b = ET.parse(ifo_path).find(".//BuildBlocker/Position")
    
    x = abs(int(b.find("x").text)) >> 11
    z = abs(int(b.find("z").text)) >> 11
    return [x, z]

def validate(buildings, model):
    valid_keys = model["buildings"].keys()
    result = set()
    for b in buildings:
        for k in b.keys():
            if k not in valid_keys:
                result.add(k)
    if result:
        text_result = "Invalid keys not found in model:\n\n"
        for r in result:
            text_result += r + "\n"
    else:
        text_result = "ok"
        
    return text_result

def out_json(buildings, model):
    json.dump(model,
              fp=open(out_folder + model_name, mode="w", encoding="utf_8"),
              indent=2,
              sort_keys=True)
    json.dump({"_version": __version__,
               "_model": model_url + model_name,
               "buildings": buildings},
              fp=open(out_folder + output_name, mode="w", encoding="utf_8"),
              indent=2,
              sort_keys=True)

def out_css(buildings, model):
    pass

#===============================================================================

def main():
    buildings = get_building_list()
    model = {"_description": "this is a list of Anno 2070 buildings with properties that help fan-made tools in there .. i tried to name the properties somewhat close to actual xml elements in game data files .. you can contact me on http://anno2070.wikia.com/wiki/User:DeathApril or peter.hozak@gmail.com",
             "_version": "0.2",
             "_changelog": {"0.2": ["2011-12-15",
                                    "BuildBlocker array of 2 ints split to 2 properties *.x and *.z (so .csv dump of could be 1:1 to JSON)",
                                    "ProductName, ProductGUID and ProductEng1 renamed to Production.Product.* (for naming consistency)",
                                    "MaxResidentCount, Faction and Group added",
                                    "FarmField.* added + the farmfields themselves can be found in the buildings array by GUID (for farm size)",
                                    "Production.* added"
                                    ],
                            "0.3": ["planned before 2011-12-31",
                                    "BuildCost.* added",
                                    "MaintananceCost.* added",
                                    "Unlock.* added"
                                    ]
                            },
             "buildings": {"GUID": "int: GUID as appears in assets.xml and other files",
                           "Name": "text: base name that appears in data files",
                           "Eng1": "text: english localisation labels from Eng1.rda for building GUID",
                           "IconFileName": "text: filename from the folder http://odegroot.nl/anno2070/img/orig/icon/ (or see icon folder in the zip file from http://odegroot.nl/anno2070/all_icons.php (first number is IconFileID, the second is IconIndex+1)",
                           "Faction": "text: tycoons, ecos, techs, others, ... ",
                           "Group": "text: residence, public, production, special, ... (farms and factories are both production, see template)",
                           "Template":"text: type of building",
                           "InfluenceRadius": "int: radius from the center of the building in tiles",
                           ".ifo": "text: path to .ifo of data2.rda data\graphics\buildings, based on the first Object/Variations/Item/Filename for each asset",
                           "MaxResidentCount": "int: max. number of inhabitants (houses only)",
                           
                           "BuildBlocker.x": "int: 'x' dimension of the building in tiles (right shift by 11 bits of the number found in BuildBlocker/x element in .ifo file",
                           "BuildBlocker.z": "int: 'z' dimension of the building in tiles (right shift by 11 bits of the number found in BuildBlocker/z element in .ifo file",
                           
                           "FarmField.GUID": "int: GUID of a farmfield (farms only)",
                           "FarmField.Count": "int: number of farmfields needed (farms only)",
                           "FarmField.Fertility": "text: type of fertility needed on island (farms only)",
                           
                           "Production.Product.Name": "text: name of product (factories and farms only)",
                           "Production.Product.GUID": "int: GUID of product (factories and farms only)",
                           "Production.Product.Eng1": "text: english localisation labels from Eng1.rda for product GUID (factories and farms only)",
                           "Production.ProductionTime": "int: miliseconds (factories and farms only)",
                           "Production.ProductionCount": "int: kilograms (factories and farms only)",
                           "Production.ProductionTonsPerMinute": "float: tons per minute, calculated (factories and farms only)",
                           "Production.RawMaterial1": "text: reference to Production.Product.Name of 1st supplier factory/farm (factories only)",
                           "Production.RawMaterial2": "text: reference to Production.Product.Name of 2nd supplier factory/farm (factories only)",
                           "Production.RawNeeded1": "int: kilograms (factories only)",
                           "Production.RawNeeded2": "int: kilograms (factories only)",
                           "Production.RawNeeded1TonsPerMinute": "float: tons per minute, calculated (factories only)",
                           "Production.RawNeeded2TonsPerMinute": "float: tons per minute, calculated (factories only)",
                           
                           #v0.3 to do
                           "BuildCost.Credits": "int: credis needet to build",
                           "BuildCost.BuildingModules": "int: building modules needed to build",
                           "BuildCost. ...": "...",
                           "BuildCost. ...": "...",
                           "BuildCost. ...": "...",
                           
                           #v0.3 to do
                           "MaintenanceCost.ActiveCost": "int: credits for maintsenance per ? seconds",
                           "MaintenanceCost.InactiveCost": "int: credits for maintenance of paused building per ? seconds",
                           "MaintenanceCost.ActiveEcoEffect": "int(+/-): eco effect (right shift by ? bits)",
                           "MaintenanceCost.InactiveEcoEffect": "int(+/-): eco effect of paused building (right shift by ? bits)",
                           "MaintenanceCost.ActiveEnergyCost": "int: energy consumption (right shift by ? bits)",
                           "MaintenanceCost.InactiveEnergyCost": "int: energy consumption of paused building (right shift by ? bits)",
                           
                           #v0.3 to do
                           "Unlock.IntermediateLevel": "text: NeedsIntermediatelevel from assets.xml to pair the building to properties.xml's SortedLevels/IntermediateLevel",
                           "Unlock.ResidentCount": "int: number of residents from properties.xml",
                           "Unlock.ResidentLevel": "text: workers, employees, engineers or executives",
                           }
             }
    
    print(validate(buildings, model))
    out_json(buildings, model)
    
        

if __name__ == "__main__":
    main()