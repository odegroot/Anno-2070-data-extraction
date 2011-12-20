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
        
        print('{{Research')
        print('| stars = ' + str(project['ItemQuality.stars']))
        
        try:
            base_icon_wiki_filename = icon_name_map[project['icon.base']]
        except KeyError:
            raise Exception('"{}": "{} item.png",'.format(project['icon.base'], project['affects.engs'][0]))
        
        print('| icon=[[File:{}]]<span style="margin-left: -46px;">[[File:Multiple effects.png]]</span>'.format(base_icon_wiki_filename))
        print('}}\n')
    
    print('|}')

def get_counts_per_category(projects):
    counts = collections.defaultdict(int)
    
    for project in projects:
        counts[project['category']] += 1
    
    return counts

if __name__ == "__main__":
    main()
