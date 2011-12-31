'''
Generates JSON and CSV files with buildings' data.

Created on 31.12.2011

@author: peter.hozak@gmail.com (http://anno2070.wikia.com/wiki/User:DeathApril)

> this github version of v0.3 is not working with ifo files - they should be added to rda folder first !!!
> more documentation + exception handling (missing data messages) + better coding style in next version ...
'''

from __future__ import division
import json, re #, sys
from xml.etree import ElementTree as ET

__version__ = "0.3.1"

# global settings
# to do: use os.path.join instead of \\
folder = "..\\"
assets_path = folder + "rda\\patch3\\data\\config\\game\\assets.xml"
icons_txt_path = folder + "rda\\eng3\\data\\loca\\eng\\txt\\icons.txt"
guids_txt_path = folder + "rda\\eng3\\data\\loca\\eng\\txt\\guids.txt"
properties_path = folder + "rda\\patch3\\data\\config\\game\\properties.xml"
icons_path = folder + "rda\\patch3\\data\\config\\game\\icons.xml"
IconWikiaFilessource_path = folder + "wikia\\wikia_icons_source.txt"
IconWikiaFiles_path = folder + "wikia\\wikia_icons_map.csv"
output_name = "json\\list_of_buildings_v" + __version__ + ".json"
model_name = "json\\list_of_buildings_model_v" + __version__ + ".json"
model_url = "http://aprilboy.e404.sk/anno2070/" + model_name


def get_building_list():
    AssetGroups = ET.parse(assets_path).findall(".//Group")
    IconFileNames = parse_IconFileNames()
    IconWikiaFiles = parse_IconWikiaFiles()
    Eng = parse_Eng()
    ProductGUIDs = parse_ProductGUIDs()
    BaseGoldPrices = parse_BaseGoldPrices()
    Unlocks = parse_Unlocks()    
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
                    if template == "SimpleObject": # SimpleObjects (farm_field_rows and pirates_props) won't be needed in this database
                        continue
                except: # scientist_academy does not have a Template, so let's ignore it ...
                    continue
                GUID = int(asset.find("Values/Standard/GUID").text)
                Name = asset.find("Values/Standard/Name").text
                b = {"GUID": GUID, "Name": Name}
                try:    b["Eng"] = Eng[GUID]
                except: pass
                try:    b["IconFileName"] = IconFileNames[GUID]
                except: pass
                try:    b["IconWikiaFile"] = IconWikiaFiles[Name]
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
                try:
                    b["FarmField.GUID"] = int(asset.find("Values/Farm/FarmFieldGUID").text)
                    try:    b["FarmField.Count"] = int(asset.find("Values/Farm/FarmfieldCount").text)
                    except: pass
                    try:    b["FarmField.Fertility"] = asset.find("Values/Farm/Fertility").text
                    except: pass
                    try:
                        # this split and join is to add "_field" to the .ifo filename
                        farmifo = b[".ifo"].split("\\")
                        for i in range(-2,0):
                            f = farmifo[i].split("_")
                            farmifo[i] = "_".join(f[0:-1] + ["field"] + [f[-1]])
                        farmifo = "\\".join(farmifo).replace("tycoon.ifo", "tycoons.ifo") # tycoon do not have consistend .ifo filenames for fields 
                        (x, z) = get_BuildBlocker( farmifo )
                        b["FarmField.BuildBlocker.x"] = x
                        b["FarmField.BuildBlocker.z"] = z
                    except: pass
                except: pass
                try:    
                    b["Production.Product.Name"] = asset.find("Values/WareProduction/Product").text
                    #default values:
                    b["Production.ProductionTime"] = 20000 #miliseconds
                    b["Production.ProductionCount"] = 1000 #kilograms
                    b["Production.RawNeeded1"] = 1000
                    b["Production.RawNeeded2"] = 1000
                    try:    b["Production.Product.GUID"] = ProductGUIDs[ b["Production.Product.Name"] ]
                    except: pass
                    try:    b["Production.Product.BaseGoldPrice"] = BaseGoldPrices[ b["Production.Product.Name"] ]
                    except: pass
                    try:    b["Production.Product.Eng"] = Eng[ b["Production.Product.GUID"] ]
                    except: pass
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
                except: pass
                try:
                    for cost in asset.findall("Values/BuildCost/*/*"):
                        try:    
                            if cost.tag == "Credits":
                                b["BuildCost." + cost.tag] = int(cost.text)
                            else:
                                b["BuildCost." + cost.tag] = int(cost.text) // 1000 # in tons
                        except: pass
                except: pass
                try:
                    for cost in asset.findall("Values/MaintenanceCost/*"):
                        try:
                            c = int(cost.text)
                            if "Cost" in cost.tag:
                                c = -c
                            if c % (2 << 10):
                                b["MaintenanceCost." + cost.tag] = c # in Credits
                            else:
                                b["MaintenanceCost." + cost.tag] = c >> 12 # in game eco / power / ... units
                        except: pass
                except: pass
                try:
                    b["Unlock.IntermediateLevel"] = asset.find("Values/BuildCost/NeedsIntermediatelevel").text
                    (count, level) = Unlocks[ b["Unlock.IntermediateLevel"] ]
                    b["Unlock.ResidentCount"] = count
                    b["Unlock.ResidentLevel"] = level
                except: pass
                buildings.append(b)
    return buildings

#===============================================================================

def parse_Eng():
    Eng = {}
    for line in open(icons_txt_path, encoding="utf_16"):
        result = re.search("(\\d*)=(.*)", line)
        if result:
            Eng[int(result.group(1))] = result.group(2)
    for line in open(guids_txt_path, encoding="utf_16"):
        result = re.search("(\\d*)=(.*)", line)
        if result:
            Eng[int(result.group(1))] = result.group(2)
    return Eng


def parse_ProductGUIDs():
    ProductGUIDs = {}
    for p in ET.parse(properties_path).findall(".//ProductIconGUID/*"):
        if p.tag != "icon":
            ProductGUIDs[p.tag] = int(p.find("icon").text)
    return ProductGUIDs


def parse_BaseGoldPrices():
    BaseGoldPrices = {}
    for p in ET.parse(properties_path).findall(".//ProductPrices/*"):
        try:    
            BaseGoldPrices[p.tag] = int(int(p.find("BaseGoldPrice").text) * 2.5)
        except: pass
    return BaseGoldPrices


def parse_IconFileNames():
    prefix = "icon_"
    midfix = "_"
    postfix = ".png"
    IconFileNames = {}
    for i in ET.parse(icons_path).findall("i"):
            IconFileID = i.find("Icons/i/IconFileID").text
            try:
                IconIndex = i.find("Icons/i/IconIndex").text
            except:
                IconIndex = "0"
            IconFileNames[int(i.find("GUID").text)] = prefix + IconFileID + midfix + IconIndex + postfix
    return IconFileNames


def parse_IconWikiaFiles():
    IconWikiaFiles = {}
    with open(IconWikiaFiles_path) as f:
        f.readline() # first line contains headers
        for line in f:
            (key, value) = line.strip().replace("\"","").split(";")[0:2]
            IconWikiaFiles[key] = value
    return IconWikiaFiles


def parse_IconWikiaFilesSource():
    '''in the IconWikiaFilessource_path file is the edit>source text of the Icons wikia page
    to be used only once to get icon names from the source code and match them with eng3 and then the map file edited manually'''
     
    buildings = get_building_list()
    WikiaCSVString = "Name;Wikia Icon File;Wikia Label\n"
    def prep(string):
        return re.sub("[ ._-]*", "", string.lower())
    with open(IconWikiaFilessource_path) as f:
        for line in f:
            if ".png" in line and "File:" not in line:
                try:
                    (png, label) = line.strip().replace(";","").split("|")[0:2]
                except:
                    (png, label) = (line.strip().replace(";","").split("|")[0], "")
                name = ""
                for b in buildings:
                    names = [ prep(b["Name"]) ]
                    try:    names.append(prep(b["Eng"]))
                    except: pass
                    try:    names.append(prep(b["IconWikiaFile"]))
                    except: pass
                    try:    names.append(prep(b["Production.Product.Name"]))
                    except: pass
                    try:    names.append(prep(b["Production.Product.Eng"]))
                    except: pass
                    try:    names.append(prep(b["IconFileName"]))
                    except: pass
                    if prep(label) in names or prep(png.split(".")[0]) in names:
                        name = b["Name"]
                        break
                WikiaCSVString += "{0};{1};{2}\n".format(name, png, label)
    return WikiaCSVString


def update_IconWikiaFiles():
    pass # manually for now ...


def get_BuildBlocker(detail_path):
    ifo_path = folder + "data2\\graphics\\buildings\\" + detail_path
    b = ET.parse(ifo_path).find(".//BuildBlocker/Position")
    x = abs(int(b.find("x").text)) >> 11
    z = abs(int(b.find("z").text)) >> 11
    return [x, z]


def parse_Unlocks():
    Unlocks = {}
    for p in ET.parse(properties_path).findall(".//SortedLevels")[1].getchildren():
        for i in p.findall("levels/Item"):
            try:    Unlocks[i.find("IntermediateLevel").text] = ( int(i.find("ResidentCount").text), p.tag )
            except: pass
    return Unlocks

#===============================================================================

def validate(buildings, model):
    valid_keys = model.keys()
    result = set()
    for b in buildings:
        for k in b.keys():
            if k not in valid_keys:
                result.add("\"{0}\": \"\",".format(k))
                break
            t = model[k].split(":")[0]
            if t not in ("text", "int", "float", "int(+/-)", "float(+/-)"):
                result.add("unknown type <{0}> for key: {1}".format(t, k))
            elif t == "text" and not isinstance(b[k], str) or t[:3] == "int" and not isinstance(b[k], int) or t[:3] == "float" and not isinstance(b[k], float):
                result.add("{0} should be <{1}> type, but for b[\"Name\"] = {2} the value is: {3}".format(k, t, b["Name"], b[k]))
    if result:
        text_result = "Invalid keys not found in model:\n\n"
        for r in result:
            text_result += r + "\n"
    else:
        text_result = "ok"
        
    return text_result

def out_json(buildings, model):
    json.dump(model,
              fp=open(folder + model_name, "w"),
              indent=2,
              sort_keys=True)
    json.dump({"_version": __version__,
               "_model": model_url,
               "buildings": buildings},
              fp=open(folder + output_name, "w"),
              indent=2,
              sort_keys=True)
    return None

def out_csv(objects, model, object_type):
    csv  = "This is a csv dump for anno data version {0}, see model {1} ...\n".format(__version__, model_url,)
    csv += "To calculate with the data in spreadsheet formulas, try something like the following instead of fixed ranges (order of columns might change in future versions):\n"
    csv += "\" =INDEX(data_range;MATCH($A2;OFFSET(data_first_column;0;MATCH('Eng';data_headers;0)-1);0);MATCH(B$1;data_headers;0))\"\n\n"
    headers = sorted(model[object_type].keys())
    for h in headers:
        csv += "{0};".format(h)
    csv += "\n"
    for b in objects:
        for h in headers:
            try:    temp = b[h]
            except: temp = ""
            csv += "{0};".format(temp)
        csv += "\n"
    # csv currently supports only 1 export object - "buildings" list for now, multiple csv files in future
    with open(folder + output_name.replace("json", "csv"), "w") as f:
        f.write(csv)
    return None
             

#===============================================================================

def main():
    model = {"_description": "this is a list of Anno 2070 buildings with properties that help fan-made tools in there .. i tried to name the properties somewhat close to actual xml elements in game data files .. you can contact me on http://anno2070.wikia.com/wiki/User:DeathApril or peter.hozak@gmail.com",
             "_version": __version__,
             "_gameversion": "v1.02 (patch3.rda)",
             "_missing_keys": "not all objects use all the keys in this model, please check for KeyError exceptions before working with them (e.g. Production.RawNeeded2Material will be missing for factories with 1 input only)",
             "_changelog": {"0.3": ["2011-12-17",
                                    "IconFileName changed, the second number corresponds to IconIndexdo without added +1 (for icons numbered from 0 instead from 1)",
                                    "IconWikiaFile added",
                                    "Production.Product.BaseGoldPrice added (in default trade price, not in datafile format)",
                                    "FarmField.BuildBlocker.* added (for convenience)",
                                    "BuildCost.* added",
                                    "MaintananceCost.* added",
                                    "Unlock.* added"
                                    ],
                            "0.2": ["2011-12-15",
                                    "BuildBlocker array of 2 ints split to 2 properties *.x and *.z (so .csv dump of could be 1:1 to JSON)",
                                    "ProductName, ProductGUID and ProductEng renamed to Production.Product.* (for naming consistency)",
                                    "MaxResidentCount, Faction and Group added",
                                    "FarmField.* added + the farmfields themselves can be found in the buildings array by GUID (for farm size)",
                                    "Production.* added"
                                    ]
                            },
             "buildings": {"GUID": "int: GUID as appears in assets.xml and other files",
                           "Name": "text: base name that appears in data files",
                           "Eng": "text: english localisation labels from Eng.rda for building GUID",
                           "IconFileName": "text: filename from the folder http://odegroot.nl/anno2070/img/orig/icon/ (or see icon folder in the zip file from http://odegroot.nl/anno2070/all_icons.php (first number is IconFileID, the second is IconIndex)",
                           "IconWikiaFile": "text: filename from the folder http://odegroot.nl/anno2070/img/orig/icon/ (or see icon folder in the zip file from http://odegroot.nl/anno2070/all_icons.php (first number is IconFileID, the second is IconIndex)",
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
                           "FarmField.BuildBlocker.x": "int: copy of x dimension from the farmfield building BuildBlocker.x property (farms only)",
                           "FarmField.BuildBlocker.z": "int: copy of x dimension from the farmfield building BuildBlocker.z property (farms only)",
                           
                           "Production.Product.Name": "text: name of product (factories and farms only)",
                           "Production.Product.GUID": "int: GUID of product (factories and farms only)",
                           "Production.Product.Eng": "text: english localisation labels from latest Eng*.rda for product GUID (factories and farms only)",
                           "Production.Product.BaseGoldPrice": "int: default trade price of product in credits [2.5 times the number from properties.xml //ProductPrices/*/BaseGoldPrice] (factories and farms only)",
                           "Production.ProductionTime": "int: miliseconds (factories and farms only)",
                           "Production.ProductionCount": "int: kilograms (factories and farms only)",
                           "Production.ProductionTonsPerMinute": "float: tons per minute, calculated (factories and farms only)",
                           "Production.RawMaterial1": "text: reference to Production.Product.Name of 1st supplier factory/farm (factories only)",
                           "Production.RawMaterial2": "text: reference to Production.Product.Name of 2nd supplier factory/farm (factories only)",
                           "Production.RawNeeded1": "int: kilograms (factories only)",
                           "Production.RawNeeded2": "int: kilograms (factories only)",
                           "Production.RawNeeded1TonsPerMinute": "float: tons per minute, calculated (factories only)",
                           "Production.RawNeeded2TonsPerMinute": "float: tons per minute, calculated (factories only)",
                           
                           "BuildCost.Credits": "int: credis needet to build",
                           "BuildCost.BuildingModules": "int: raw material needed to build in kilograms",
                           "BuildCost.Wood": "int: raw material needed to build in kilograms",
                           "BuildCost.Glass": "int: raw material needed to build in kilograms",
                           "BuildCost.Carbon": "int: raw material needed to build in kilograms",
                           "BuildCost.Concrete": "int: raw material needed to build in kilograms",
                           "BuildCost.Steel": "int: raw material needed to build in kilograms",
                           "BuildCost.Tools": "int: raw material needed to build in kilograms",
                           "BuildCost.Weapons": "int: raw material needed to build in kilograms",
                           "BuildCost.HeavyWeapons": "int: raw material needed to build in kilograms",
                           "BuildCost.AdvancedWeapons": "int: raw material needed to build in kilograms",
                           
                           "MaintenanceCost.ActiveCost": "int: credits for maintsenance per tick",
                           "MaintenanceCost.InactiveCost": "int: credits for maintenance of paused building per tick",
                           "MaintenanceCost.ActiveEcoEffect": "float(+/-): eco effect (game unit)",
                           "MaintenanceCost.InactiveEcoEffect": "float(+/-): eco effect of paused building (game unit)",
                           "MaintenanceCost.ActiveEnergyCost": "float: energy consumption (game unit)",
                           "MaintenanceCost.InactiveEnergyCost": "float: energy consumption of paused building (game unit)",
                           "MaintenanceCost.EcoEffectFadingSpeed": "float: game unit",
                           "MaintenanceCost.InitTime": "float: miliseconds",
                           "MaintenanceCost.ActiveEnergyProduction": "float: game unit",
                           "MaintenanceCost.InactiveEnergyProduction": "float: game unit",
                           "MaintenanceCost.MinimumEnergyLevel": "float: game unit",
                           "MaintenanceCost.ActiveAtStart": "float: game unit",
                            
                           "Unlock.IntermediateLevel": "text: NeedsIntermediatelevel from assets.xml to pair the building to properties.xml's SortedLevels/IntermediateLevel",
                           "Unlock.ResidentCount": "int: number of residents from properties.xml",
                           "Unlock.ResidentLevel": "text: workers, employees, engineers or executives",
                           }
             } 
    
    #print parse_IconWikiaFilesSource()
    
    buildings = get_building_list()
    print(validate(buildings, model["buildings"]))
    out_json(buildings, model)
    out_csv(buildings, model, "buildings")


if __name__ == "__main__":
    main()