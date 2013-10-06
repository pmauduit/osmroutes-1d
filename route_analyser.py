#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
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

# check if a branch is not already in the list
def is_in(branches, elem):
    for branch in branches:
        if branch == elem:
            return True
    return False

# clean the equivalent branches
def clean_branches(branches):
    new_branches = []
    for branche in branches:
        rev = list(branche)
        rev.reverse()
        if not is_in(new_branches, rev):
            new_branches.append(branche)
    return new_branches


# calculates the position of each stops on a 1D map
def compute_positions(branches):
    ret = []
    # a dictionnary to keep in cache
    # already visited nodes
    seen = {}
    ypos = 0
    xpos = 0
    for idx, branch in enumerate(branches):
        print "Parsing branch #%d" % idx
        # first branch, apply an arbitrary coordinate for each node
        if seen == {}:
            for stop in branch:
                ancestors =  0 if idx == 0 else 1
                nexts = 0 if idx == len(branch) - 1 else 1
                seen[stop] = { 'x': xpos, 'y': ypos, 'ancestors': ancestors, 'nexts' : nexts }
                xpos += 1
        # else try to find a known node
        else:
            unkn_node = []
            known_node = None
            for idxstop, stop in enumerate(branch):
                saved = seen.get(stop)
                if saved is None:
                    if known_node is None:
                        print "Unknown node"
                        unkn_node.append(stop)
                    else:
                        # empty the unkn_node list
                        xpos = known_node['x'] - 1
                        ypos = known_node['y'] if known_node['ancestors'] == 0 else known_node['y'] + 1
                        while len(unkn_node) > 0:
                            popped = unkn_node.pop()
                            ancestors = 0 if len(unkn_node) == 0 else 1
                            seen[popped] = { 'x': xpos, 'y': ypos, 'ancestors' : ancestors, 'nexts': 1 }
                            xpos -= 1
                        # then add the new unknown node
                        xpos = known_node['x'] + 1
                        ypos = known_node['y'] if known_node['nexts'] == 0 else known_node['y'] + 1
                        nexts = 0 if idxstop == len(branch) - 1 else 1
                        curr_node = { 'x': xpos, 'y': ypos, 'ancestors': 1, 'nexts': nexts }
                        seen[stop] = curr_node
                        known_node = curr_node
                else:
                    print "node found: %s" % saved
                    known_node = saved
                    xpos = saved['x'] - 1
                    ypos = saved['y'] if saved['ancestors'] == 0 else saved['y'] + 1
                    while len(unkn_node) > 0:
                        popped = unkn_node.pop()
                        ancestors = 0 if len(unkn_node) == 0 else 1
                        seen[popped] = { 'x': xpos, 'y': ypos, 'ancestors': ancestors, 'nexts': 1 }
                        xpos -= 1
        print ""
    print "Computing levels finished: %d stops successfully placed" % len(seen.keys())
    return seen

# normalizes the coordinates of each stops
def normalize_coordinates(stops):
    min_x = 0
    min_y = 0
    print "Normalizing levels ..."
    for name,stop in stops.iteritems():
        if min_x > stop['x']:
            min_x = stop['x']
        if min_y > stop['y']:
            min_y = stop['y']
    print "min_x: %d min_y: %d" % (min_x, min_y)
    for name,stop in stops.iteritems():
        stop['x'] -= min_x
        stop['y'] -= min_y
    return stops


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
        # cleaning branches
        #cleaned_branches = clean_branches(datas['branches'])
        #datas['branches'] = cleaned_branches
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
        datas['branches'] = clean_branches(datas['branches'])
        # computes position (coordinates for each stops)
        stops = compute_positions(datas['branches'])
        # normalizes positions (simple translation)
        stops = normalize_coordinates(stops)
        if args.output:
            with open(args.output, "w") as outfile:
                    json.dump(stops, outfile, indent=4)
        else:
            json.dump(stops, sys.stdout, indent=4)
    else:
        parser.print_help()

