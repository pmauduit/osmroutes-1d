#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import pprint
import json
import argparse
import copy
from lib.OsmApi import OsmApi

OSM_API = OsmApi()

# Fetches osm data from the API
def get_osm_data(relation_id):
    daugther_relations = []
    colour = None

    mother_relation = OSM_API.RelationGet(relation_id)

    colour = mother_relation['tag'].get('colour', '#000000')
    daughter_relations = [ member['ref'] for member in mother_relation['member']
                            if member['type'] == 'relation'
                            and member.get('ref', None) is not None ]

    branches = []

    # iterating on daughter relations
    for daughter in daughter_relations:
        current_daughter = OSM_API.RelationGet(daughter)
        branche = []
        for member in current_daughter['member']:
            if member['role'] == 'stop':
                current_stop = OSM_API.NodeGet(member['ref']) if member['type'] == 'node' else OSM_API.WayGet(member['ref'])
                name_stop = current_stop['tag'].get('name', None)
                if name_stop is not None:
                    branche.append(name_stop)
        branches.append(branche)
    return { 'colour': colour, 'branches': branches }

# returns true if the 2 branches are equivalent
def equivalent(branch1, branch2):
    if len(branch1) != len(branch2):
        return False
    for i in range(0, len(branch1)):
        if branch1[i] != branch2[i]:
            return False
    return True

def same(b1, b2):
    if len(b1) != len(b2):
        return False
    for idx, _ in enumerate(b1):
        if b1[idx] != b2[idx]:
            return False
    return True

# check if a branch is not already in the list
def is_in(branches, elem):
    for branch in branches:
        if same(branch,elem):
            return True
    return False

# clean the equivalent branches
def clean_branches(branches):
    new_branches = []
    for branche in branches:
        rev = list(branche)
        rev.reverse()
        if not is_in(branches, rev):
            new_branches.append(branche)
    return new_branches


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--relation", help="fetches the data from the OSM API", type=int)
    parser.add_argument("--input", help="Loads the data from a file")
    parser.add_argument("--output", help="Dumps the result of the script into a file")
    args = parser.parse_args()

    # Fetches OSM data via the API
    if args.relation:
        relation_id = int(args.relation)
        datas = get_osm_data(relation_id)
        if args.output:
            with open(args.output, "w") as outfile:
                    json.dump(datas, outfile, indent=4)
        else:
            json.dump(datas, sys.stdout, indent=4)

    # Loads OSM data from a JSON file
    elif args.input:
        json_data = open(args.input).read()
        datas = json.loads(json_data)
        # cleaning branches
        cleaned_branches = clean_branches(datas['branches'])
        datas['branches'] = cleaned_branches
        if args.output:
            with open(args.output, "w") as outfile:
                    json.dump(datas, outfile, indent=4)
        else:
            json.dump(datas, sys.stdout, indent=4)
    else:
        parser.print_help()
