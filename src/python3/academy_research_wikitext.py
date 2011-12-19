# coding=utf_8
'''
Generates wikitext for use on http://anno2070.wikia.com/wiki/Academy_Research_Projects

Uses the projects model created by academy_research.py

Created on Dec 19, 2011

@author: Oscar de Groot (Grilse)
'''

import academy_research
import collections

def main():
    eng = academy_research.get_localization('eng')
    projects = academy_research.get_research_project_dicts(eng)
    
    project_counts = get_counts_per_category(projects)
    
    category = None
    subcategory = None
    
    for project in projects:
        if project['category'] != category:
            category = project['category']
            print('\n=={} ({} projects)=='.format(category, project_counts[category]))
        
        if 'subcategory' in project and project['subcategory'] != subcategory:
            subcategory = project['subcategory']
            print('\n==={}==='.format(subcategory))

def get_counts_per_category(projects):
    counts = collections.defaultdict(int)
    
    for project in projects:
        counts[project['category']] += 1
    
    return counts

if __name__ == "__main__":
    main()
