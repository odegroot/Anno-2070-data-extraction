"""
Generates JSON and CSV files with buildings' data.
Python 3.2

Created on 11.2.2011

@author: peter.hozak@gmail.com (http://anno2070.wikia.com/wiki/User:DeathApril)
"""

import os
import shutil
import sys #@UnusedImport
import re
import json
from xml.etree import ElementTree as ET

# globals
__version__ = "0.4.0"
_gameversion = "1.04"
_patchnumber = "5"
_patchnumber_language = "4"
_changelog = {"0.4": ["2012-02-11",
                      "objects instead of *.* keys",
                      "multilingual support - new keys added: Cze, Esp, Fra, Ger, Ita, Pol, Rus + the same for b['Production']['Product'] object"],
              "0.3.2": ["2011-12-31",
                        "ifo files copied to rda _folder => BuildBlocker.* works just fine (i hope)"],
              "0.3.1": ["2011-12-31",
                        "migration to this GitHub project",
                        "from python 2.7 to 3.2",
                        "using data files from rda _folder instead of My Documents,, but .ifo => BuildBlocker.* do not work yet"],
              "0.3": ["2011-12-17",
                      "IconFileName changed, the second number corresponds to IconIndexdo without added +1 (for icons numbered from 0 instead from 1)",
                      "IconWikiaFile added",
                      "Production.Product.BaseGoldPrice added (in default trade price, not in datafile format)",
                      "FarmField.BuildBlocker.* added (for convenience)",
                      "BuildCost.* added",
                      "MaintananceCost.* added",
                      "Unlock.* added"],
              "0.2": ["2011-12-15",
                      "BuildBlocker array of 2 ints split to 2 properties*.x and *.z (so .csv dump of could be 1:1 to JSON)",
                      "ProductName, ProductGUID and ProductEng renamed to Production.Product.* (for naming consistency)",
                      "MaxResidentCount, Faction and Group added",
                      "FarmField.* added + the farmfields themselves can be found in the buildings array by GUID (for farm size)",
                      "Production.* added"]
              }

# TODO v0.4.x: merge eng5.rda guids.txt with eng4.rda icons.txt
_folder = ".."
_assets_path = os.path.join(_folder, "rda", "patch"+_patchnumber, "data", "config", "game", "assets.xml")
_properties_path = os.path.join(_folder, "rda", "patch"+_patchnumber, "data", "config", "game", "properties.xml")
_icons_path = os.path.join(_folder, "rda", "patch"+_patchnumber, "data", "config", "game", "icons.xml")
_icons_txt_path = os.path.join(_folder, "rda", "{lang}"+_patchnumber_language, "data", "loca", "{lang}", "txt", "icons.txt")
_guids_txt_path = os.path.join(_folder, "rda", "{lang}"+_patchnumber_language, "data", "loca", "{lang}", "txt", "guids.txt")
_languages = ["cze", "eng", "esp", "fra", "ger", "ita", "pol", "rus"]

_IconWikiaFiles_path = os.path.join(_folder, "json", "icon_name_map.json")

_orig_data_folder = "C:\\Users\\Peter\\Documents\\ANNO 2070" # location of all extracted data files that are not on github
_ifo_files = os.path.join(_folder, "rda", "ifo_files")

_v = ".".join(__version__.split(".")[:2])
_output_name = os.path.join("json", "list_of_buildings_v" + _v + ".json")
_model_name = os.path.join("json", "list_of_buildings_model_v" + _v + ".json")
_model_url = "https://github.com/odegroot/Anno-2070-data-extraction/blob/master/src/" + _model_name.replace("\\", "/")
_validation_result = set()

def get_building_list():
    AssetGroups = ET.parse(_assets_path).findall(".//Group")
    IconFileNames = parse_IconFileNames()
    IconWikiaFiles, IconWikiaFiles_missing = parse_IconWikiaFiles()
    Localisaton = parse_Localisation()
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
                # ___base attributes, localisations and buildblocker___ #
                b = {"GUID": GUID, "Name": Name}
                b["Localisation"] = {}
                for lang in _languages:
                    try:
                        b["Localisation"][lang] = Localisaton[lang][GUID]
                    except KeyError:
                        print("{} (={}) not in Localisation[{}]".format(GUID, Name, lang))
                try:
                    b["IconFileName"] = IconFileNames[GUID]
                    try:
                        b["IconWikiaFile"] = IconWikiaFiles[b["IconFileName"]]
                    except KeyError:
                        if b["IconFileName"] not in IconWikiaFiles_missing:
                            print("{} (={}) not in IconWikiaFiles (icon_name_map.json)".format(b["IconFileName"], Name))
                except KeyError:
                    # known missing GUIDs in icons.xml
                    if GUID not in (10264, 10074, 10018, 10251):
                        print("{} (={}) not in IconFileNames (icons.xml)".format(GUID, Name))
                try:
                    b["Faction"] = faction_name
                except AttributeError:
                    pass
                try:
                    b["Group"] = group_name
                except AttributeError:
                    pass
                try:
                    b["Template"] = template
                except AttributeError:
                    pass
                try:
                    b["InfluenceRadius"] = int(asset.find("Values/Influence/InfluenceRadius").text)
                except AttributeError:
                    pass
                try:
                    b[".ifo"] = (asset.find("Values/Object/Variations/Item/Filename").text.split("\\")[-1][:-3] + "ifo").lower()
                except AttributeError:
                    pass
                try:    b["MaxResidentCount"] = int(asset.find("Values/ResidenceBuilding/MaxResidentCount").text)
                except AttributeError:
                    pass
                try:
                    (x, z) = get_BuildBlocker( b[".ifo"] )
                    b["BuildBlocker"] = {"x": x, "z": z}
                except AttributeError:
                    pass
                # ___farmfield___ #
                try:
                    b["FarmField"] = {"GUID": int(asset.find("Values/Farm/FarmFieldGUID").text)}
                    try:
                        b["FarmField"]["Fertility"] = asset.find("Values/Farm/Fertility").text
                    except AttributeError:
                        pass
                    try:
                        b["FarmField"]["Count"] = int(asset.find("Values/Farm/FarmfieldCount").text)
                        if b["FarmField"]["Count"] > 0:
                            # add "_field" to the .ifo filename
                            farmifo = b[".ifo"]
                            f = farmifo.split("_")
                            farmifo = "_".join(f[0:-1] + ["field"] + [f[-1]])
                            # correct naming inconsistencies
                            if farmifo == "tea_field_plantation.ifo":
                                farmifo = "tea_plantation_field_ecos.ifo"
                            elif farmifo == "algae_farm_field_techs.ifo":
                                farmifo = "algae_farm_field_techs_algae.ifo"
                            else:
                                farmifo = farmifo.replace("tycoon.ifo", "tycoons.ifo")
                            try:
                                (x, z) = get_BuildBlocker( farmifo )
                                b["FarmField"]["BuildBlocker"] = {"x": x, "z": z}
                            except IOError:
                                print("{} file does not exist".format(farmifo))
                    except AttributeError:
                        pass
                except AttributeError:
                    pass
                # ___production___ #
                try:    
                    b["Production"] = {"Product": {"Name": asset.find("Values/WareProduction/Product").text}}
                    #default values:
                    b["Production"]["ProductionTime"] = 20000 #miliseconds
                    b["Production"]["ProductionCount"] = 1000 #kilograms
                    b["Production"]["RawNeeded1"] = 1000
                    b["Production"]["RawNeeded2"] = 1000
                    try:
                        b["Production"]["Product"]["GUID"] = ProductGUIDs[ b["Production"]["Product"]["Name"] ]
                    except KeyError:
                        print("{} not in ProductGUIDs".format(b["Production"]["Product"]["Name"]))
                    try:
                        b["Production"]["Product"]["BaseGoldPrice"] = BaseGoldPrices[ b["Production"]["Product"]["Name"] ]
                    except KeyError:
                        print("{} not in BaseGoldPrices".format(b["Production"]["Product"]["Name"]))
                    b["Production"]["Product"]["Localisation"] = {}
                    for lang in _languages:
                        try:
                            b["Production"]["Product"]["Localisation"][lang] = Localisaton[lang][b["Production"]["Product"]["GUID"]]
                        except KeyError:
                            print("{} (={}) not in Localisation[{}]".format(b["Production"]["Product"]["GUID"], b["Production"]["Product"]["Name"], lang))
                    try:
                        b["Production"]["ProductionTime"] = int(asset.find("Values/WareProduction/ProductionTime").text)
                    except AttributeError:
                        pass
                    TicksPerMinute = 60000 / b["Production"]["ProductionTime"]
                    b["Production"]["ProductionTonsPerMinute"] = ( b["Production"]["ProductionCount"] / 1000 ) * TicksPerMinute 
                    try:
                        ["Production"]["ProductionCount"] = int(asset.find("Values/WareProduction/ProductionCount").text)
                    except AttributeError:
                        pass
                    try:
                        b["Production"]["RawMaterial1"] = asset.find("Values/Factory/RawMaterial1").text
                    except:
                        del b["Production"]["RawNeeded1"]
                    try:
                        b["Production"]["RawMaterial2"] = asset.find("Values/Factory/RawMaterial2").text
                    except:
                        del b["Production"]["RawNeeded2"]
                    try:
                        b["Production"]["RawNeeded1"] = int(asset.find("Values/Factory/RawNeeded1").text)
                        b["Production"]["RawNeeded1TonsPerMinute"] = ( b["Production"]["RawNeeded1"] / 1000 ) * b["Production"]["ProductionTonsPerMinute"]
                    except AttributeError:
                        pass
                    try:
                        b["Production"]["RawNeeded2"] = int(asset.find("Values/Factory/RawNeeded2").text)
                        b["Production"]["RawNeeded2TonsPerMinute"] = ( b["Production"]["RawNeeded2"] / 1000 ) * b["Production"]["ProductionTonsPerMinute"]
                    except AttributeError:
                        pass
                except AttributeError:
                    pass
                # ___costs and unlocks___ #
                try:
                    b["BuildCost"] = {}
                    for cost in asset.findall("Values/BuildCost/*/*"):
                        try:
                            if cost.tag == "Credits":
                                b["BuildCost"][cost.tag] = int(cost.text)
                            else:
                                b["BuildCost"][cost.tag] = int(cost.text) // 1000 # in tons
                        except AttributeError:
                            pass
                except AttributeError:
                    pass
                try:
                    b["MaintenanceCost"] = {}
                    for cost in asset.findall("Values/MaintenanceCost/*"):
                        if not isinstance(cost.text, int):
                            continue
                        c = int(cost.text)
                        if "Cost" in cost.tag:
                            c = -c
                        if c % (2 << 10):
                            b["MaintenanceCost"][cost.tag] = c # in Credits
                        else:
                            b["MaintenanceCost"][cost.tag] = c >> 12 # in game eco / power / ... units
                except AttributeError:
                    pass
                try:
                    b["Unlock"] = {"IntermediateLevel": asset.find("Values/BuildCost/NeedsIntermediatelevel").text}
                    (count, level) = Unlocks[ b["Unlock"]["IntermediateLevel"] ]
                    b["Unlock"]["ResidentCount"] = count
                    b["Unlock"]["ResidentLevel"] = level
                except AttributeError:
                    pass
                except KeyError:
                    print("{} not in Unlocks".format(b["Unlock"]["IntermediateLevel"]))
                buildings.append(b)
    return buildings

#===============================================================================

def parse_Localisation():
    Localisation = {}
    for lang in _languages:
        Localisation[lang] = {}
        with open(_icons_txt_path.format(lang=lang), encoding="utf_16") as f:
            for line in f:
                result = re.search("(\\d*)=(.*)", line)
                if result:
                    Localisation[lang][int(result.group(1))] = result.group(2)
        with open(_guids_txt_path.format(lang=lang), encoding="utf_16") as f:
            for line in f:
                result = re.search("(\\d*)=(.*)", line)
                if result:
                    Localisation[lang][int(result.group(1))] = result.group(2)
    return Localisation

def parse_ProductGUIDs():
    ProductGUIDs = {}
    for p in ET.parse(_properties_path).findall(".//ProductIconGUID/*"):
        if p.tag != "icon":
            ProductGUIDs[p.tag] = int(p.find("icon").text)
    return ProductGUIDs

def parse_BaseGoldPrices():
    BaseGoldPrices = {}
    for p in ET.parse(_properties_path).findall(".//ProductPrices/*"):
        try:    
            BaseGoldPrices[p.tag] = int(int(p.find("BaseGoldPrice").text) * 2.5)
        except AttributeError: pass
    return BaseGoldPrices

def parse_IconFileNames():
    prefix = "icon_"
    midfix = "_"
    postfix = ".png"
    IconFileNames = {}
    for i in ET.parse(_icons_path).findall("i"):
            IconFileID = i.find("Icons/i/IconFileID").text
            try:
                IconIndex = i.find("Icons/i/IconIndex").text
            except:
                IconIndex = "0"
            IconFileNames[int(i.find("GUID").text)] = prefix + IconFileID + midfix + IconIndex + postfix
    return IconFileNames

def parse_IconWikiaFiles():
    with open(_IconWikiaFiles_path) as f:
        temp = json.load(f)
    IconWikiaFiles = temp["data"]
    IconWikiaFiles_missing = temp["missing_data"]
    return IconWikiaFiles, IconWikiaFiles_missing

def get_BuildBlocker(ifo):
    b = ET.parse(os.path.join(_ifo_files, ifo)).find(".//BuildBlocker/Position")
    x = abs(int(b.find("x").text)) >> 11
    z = abs(int(b.find("z").text)) >> 11
    return [x, z]

def copy_ifo_files():
    buildings = get_building_list()
    ifos = []
    for b in buildings:
        ifos.append(b[".ifo"])
    for root, dirs, files in os.walk(_orig_data_folder): #@UnusedVariable
        for f in files:
            if f in ifos:
                shutil.copy(os.path.join(root, f), _ifo_files)
    return None

def parse_Unlocks():
    Unlocks = {}
    for p in ET.parse(_properties_path).findall(".//SortedLevels")[1].getchildren():
        for i in p.findall("levels/Item"):
            try:
                key = i.find("IntermediateLevel").text
                value = ( int(i.find("ResidentCount").text), p.tag )
                Unlocks[key] = value
                if key[-1] == "1":
                    Unlocks[key[:-1]] = (0, key[:-1].replace("Intermediate", ""))
            except AttributeError:
                pass
    return Unlocks

#===============================================================================

def validate(buildings, model):
    """validation of buildings dict values using types from model dict values
       recursive if both buildings and model value is dict"""
    valid_keys = model.keys()
    for b in buildings:
        for k in b.keys():
            if k not in valid_keys:
                _validation_result.add("\"{0}\": \"\",".format(k))
                continue
            mk = model[k]
            bk = b[k]
            if isinstance(mk, dict):
                if not isinstance(bk, dict):
                    _validation_result.add("expected dict in {0}, found {0} instead".format(k, type(bk)))
                validate([bk], mk)
            elif isinstance(mk, str):
                if not (mk.startswith("text") or
                        mk.startswith("int") or
                        mk.startswith("float")):
                    _validation_result.add("unknown type <{0}> for key: {1}".format(mk, k))
                elif (mk.startswith("text") and not isinstance(bk, str) or
                      mk.startswith("int") and not isinstance(bk, int) or
                      mk.startswith("float") and not isinstance(bk, float) and not isinstance(bk, int)):
                    _validation_result.add("{0} should be <{1}> type, but somewhere the value is: {2}".format(k, mk, bk))
            else:
                _validation_result.add("expected data type for {0} in the model: {1}".format(k, type(mk)))
    if _validation_result:
        text_result = "Invalid keys not found in model:\n\n"
        for r in _validation_result:
            text_result += r + "\n"
    else:
        text_result = "Validation ok."
        
    return text_result

def out_json(buildings, model):
    json.dump(model,
              fp=open(os.path.join(_folder, _model_name), "w"),
              indent=2,
              sort_keys=True)
    json.dump({"_version": __version__,
               "_model": _model_url,
               "buildings": buildings},
              fp=open(os.path.join(_folder, _output_name), "w"),
              indent=2,
              sort_keys=True)
    return None

def out_csv(objects, model, object_type):
    # TODO: make compatible with multi-level objects
    csv  = "This is a csv dump for anno data version {0}, see model {1} ...\n".format(__version__, _model_url,)
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
    with open(_folder + _output_name.replace("json", "csv"), "w") as f:
        f.write(csv)
    return None
             

#===============================================================================

def main():
    model = {"_description": "this is a list of Anno 2070 buildings with properties that help fan-made tools in there .. i tried to name the properties somewhat close to actual xml elements in game data files .. you can contact me on http://anno2070.wikia.com/wiki/User:DeathApril or peter.hozak@gmail.com",
             "_version": __version__,
             "_gameversion": "{} (patch{}.rda)".format(_gameversion, _patchnumber),
             "_missing_keys": "not all objects use all the keys in this model, please check for KeyError exceptions before working with them (e.g. Production.RawNeeded2Material will be missing for factories with 1 input only)",
             "_changelog": _changelog,
             "buildings": {"GUID": "int: GUID as appears in assets.xml and other files",
                           "Name": "text: base name that appears in data files",
                           "IconFileName": "text: filename from the _folder http://odegroot.nl/anno2070/img/orig/icon/ (or see icon _folder in the zip file from http://odegroot.nl/anno2070/all_icons.php (first number is IconFileID, the second is IconIndex)",
                           "IconWikiaFile": "text: filename from the _folder http://odegroot.nl/anno2070/img/orig/icon/ (or see icon _folder in the zip file from http://odegroot.nl/anno2070/all_icons.php (first number is IconFileID, the second is IconIndex)",
                           "Faction": "text: tycoons, ecos, techs, others, ... ",
                           "Group": "text: residence, public, production, special, ... (farms and factories are both production, see template)",
                           "Template":"text: type of building",
                           "InfluenceRadius": "int: radius from the center of the building in tiles",
                           ".ifo": "text: path to .ifo of data2.rda data\graphics\buildings, based on the first Object/Variations/Item/Filename for each asset",
                           "MaxResidentCount": "int: max. number of inhabitants (houses only)",
                           
                           "Localisation": {
                               "cze": "text: czech labels from cze*.rda for building GUID",
                               "eng": "text: english labels from eng*.rda for building GUID",
                               "esp": "text: spanish labels from esp*.rda for building GUID",
                               "fra": "text: french labels from fra*.rda for building GUID",
                               "ger": "text: german labels from ger*.rda for building GUID",
                               "ita": "text: italian labels from ita*.rda for building GUID",
                               "pol": "text: polish labels from pol*.rda for building GUID",
                               "rus": "text: russian labels from rus*.rda for building GUID"
                               },
                           
                           "BuildBlocker": {
                               "x": "int: 'x' dimension of the building in tiles (right shift by 11 bits of the number found in BuildBlocker/x element in .ifo file",
                               "z": "int: 'z' dimension of the building in tiles (right shift by 11 bits of the number found in BuildBlocker/z element in .ifo file"
                               },
                           
                           "FarmField": {
                               "GUID": "int: GUID of a farmfield",
                               "Count": "int: number of farmfields needed",
                               "Fertility": "text: type of fertility needed on island",
                               "BuildBlocker": {
                                   "x": "int: copy of x dimension from the farmfield building BuildBlocker.x property",
                                   "z": "int: copy of x dimension from the farmfield building BuildBlocker.z property"
                                   }
                               },
                           
                           "Production": {
                               "Product": {
                                   "Name": "text: name of product",
                                   "GUID": "int: GUID of product",
                                   "BaseGoldPrice": "int: default trade price of product in credits [2.5 times the number from properties.xml //ProductPrices/*/BaseGoldPrice]",
                                   "Localisation": {
                                       "cze": "text: czech labels from cze*.rda for product GUID",
                                       "eng": "text: english labels from eng*.rda for product GUID",
                                       "esp": "text: spanish labels from esp*.rda for product GUID",
                                       "fra": "text: french labels from fra*.rda for product GUID",
                                       "ger": "text: german labels from ger*.rda for product GUID",
                                       "ita": "text: italian labels from ita*.rda for product GUID",
                                       "pol": "text: polish labels from pol*.rda for product GUID",
                                       "rus": "text: russian labels from rus*.rda for product GUID"
                                   }
                                   },
                               "ProductionTime": "int: miliseconds",
                               "ProductionCount": "int: kilograms",
                               "ProductionTonsPerMinute": "float: tons per minute, calculated",
                               "RawMaterial1": "text: reference to Product.Name of 1st supplier factory/farm (factories only)",
                               "RawMaterial2": "text: reference to Product.Name of 2nd supplier factory/farm (factories only)",
                               "RawNeeded1": "int: kilograms (factories only)",
                               "RawNeeded2": "int: kilograms (factories only)",
                               "RawNeeded1TonsPerMinute": "float: tons per minute, calculated (factories only)",
                               "RawNeeded2TonsPerMinute": "float: tons per minute, calculated (factories only)"
                               },
                           
                           "BuildCost": {
                               "Credits": "int: credis needet to build",
                               "BuildingModules": "int: raw material needed to build in kilograms",
                               "Wood": "int: raw material needed to build in kilograms",
                               "Glass": "int: raw material needed to build in kilograms",
                               "Carbon": "int: raw material needed to build in kilograms",
                               "Concrete": "int: raw material needed to build in kilograms",
                               "Steel": "int: raw material needed to build in kilograms",
                               "Tools": "int: raw material needed to build in kilograms",
                               "Weapons": "int: raw material needed to build in kilograms",
                               "HeavyWeapons": "int: raw material needed to build in kilograms",
                               "AdvancedWeapons": "int: raw material needed to build in kilograms"
                               },
                           
                           "MaintenanceCost": {
                               "ActiveCost": "int: credits for maintsenance per tick",
                               "InactiveCost": "int: credits for maintenance of paused building per tick",
                               "ActiveEcoEffect": "float(+/-): eco effect (game unit)",
                               "InactiveEcoEffect": "float(+/-): eco effect of paused building (game unit)",
                               "ActiveEnergyCost": "float: energy consumption (game unit)",
                               "InactiveEnergyCost": "float: energy consumption of paused building (game unit)",
                               "EcoEffectFadingSpeed": "float: game unit",
                               "InitTime": "float: miliseconds",
                               "ActiveEnergyProduction": "float: game unit",
                               "InactiveEnergyProduction": "float: game unit",
                               "MinimumEnergyLevel": "float: game unit",
                               "ActiveAtStart": "float: game unit"
                               },
                           
                           "Unlock": {
                               "IntermediateLevel": "text: NeedsIntermediatelevel from assets.xml to pair the building to properties.xml's SortedLevels/IntermediateLevel",
                               "ResidentCount": "int: number of residents from properties.xml",
                               "ResidentLevel": "text: workers, employees, engineers or executives"
                               }
                           }
             } 
    
    #copy_ifo_files()
    
    buildings = get_building_list()
    
    print(validate(buildings, model["buildings"]))
    out_json(buildings, model)
    
    # csv does not work with multi-level objects yet...
    #out_csv(buildings, model, "buildings")


if __name__ == "__main__":
    main()
