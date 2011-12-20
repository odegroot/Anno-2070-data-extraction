# coding=utf_8
'''
Generates wikitext for use on http://anno2070.wikia.com/wiki/Academy_Research_Projects

Uses the projects model created by academy_research.py

Created on Dec 19, 2011

@author: Oscar de Groot (Grilse)
'''

import academy_research
import collections
import json
import os
import textwrap

__project_root = os.path.join('..', '..')
__icon_name_map_path = os.path.join(__project_root, 'src', 'json', 'icon_name_map.json')

def main():
    eng = academy_research.get_localization('eng')
    projects = academy_research.get_research_project_dicts(eng)
    with open(__icon_name_map_path, encoding='utf_8') as file:
        icon_name_map = json.load(file)['data']
    
    project_counts = get_counts_per_category(projects)
    
    category = None
    subcategory = None
    table_open = False
    
    for project in projects:
        # Section and table headers - creates section headers and open/closes tables as applicable.
        # Assumens that the list of projects is grouped by category (which it is).
        if project['category'] != category:
            if table_open:
                print('|}')
                table_open = False
            category = project['category']
            print('\n=={} ({} projects)=='.format(category, project_counts[category]))
        
        if 'subcategory' in project and project['subcategory'] != subcategory:
            if table_open:
                print('|}')
                table_open = False
            subcategory = project['subcategory']
            print('\n==={}===\n'.format(subcategory))
        
        if not table_open:
            print('{{Research-header}}\n')
            table_open = True
        
        # Creates a template call for the current research project.
        stars = str(project['ItemQuality.stars'])
        name = project['Name.eng']
        desc = project['description.eng']
        try:
            base_icon_wiki_filename = icon_name_map[project['icon.base']]
        except KeyError:
            raise Exception('"{}": "{} item.png",'.format(project['icon.base'], project['affects.engs'][0]))
        
        if 'icon.overlay' in project:
            overlay_icon_wiki_filename = icon_name_map[project['icon.overlay']]
            overlay_icon_wikitext = '<span style="margin-left: -46px;">[[File:{}]]</span>'.format(overlay_icon_wiki_filename)
        else:
            overlay_icon_wikitext = ''
        
        effects = []
        if 'effect.ActiveCost.text' in project:
            effects.append('[[File:Balance-icon.png|20px|Maintenance costs]] ' + project['effect.ActiveCost.text'])
        if 'effect.ActiveEcoEffect.text' in project:
            effects.append('[[File:Ecobal-icon.png|20px|Eco effect]] ' + project['effect.ActiveEcoEffect.text'])
        if 'effect.ActiveEnergyProduction.text' in project:
            effects.append('[[File:Energy-icon.png|20px|Energy production]] ' + project['effect.ActiveEnergyProduction.text'])
        if 'effect.ActiveEnergyCost.text' in project:
            effects.append('[[File:Energy-icon.png|20px|Energy cost]] ' + project['effect.ActiveEnergyCost.text'])
            
        if 'effect.AdditionalDisasterProbability' in project:
            effects.append('[[File:Disaster.png|20px|Probability of accidents]] {}%'.format(project['effect.AdditionalDisasterProbability']))
            
        effects_wikitext = ' <br/> '.join(effects)
        
        print(textwrap.dedent(
            '''
            {{{{Research
            |stars={}
            |icon=[[File:{}]]{}
            |name={}
            |effect={}
            |desc={}
            }}}}
            '''.format(stars, base_icon_wiki_filename, overlay_icon_wikitext, name, effects_wikitext, desc)
        ))
    
    print('|}') # close the last table.

def get_counts_per_category(projects):
    counts = collections.defaultdict(int)
    
    for project in projects:
        counts[project['category']] += 1
    
    return counts

if __name__ == "__main__":
    main()
