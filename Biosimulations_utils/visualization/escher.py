""" Utilities for converting metabolic maps from Escher to Vega format

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2021-02-06
:Copyright: 2021, Center for Reproducible Biomedical Modeling
:License: MIT
"""

import json
import math
import os

__all__ = ['escher_to_vega']


def escher_to_vega(escher_filename, vega_filename, reaction_fluxes=None,
                   max_width_height=500, legend_padding=60, legend_width=40, indent=2):
    """ Convert a metabolic pathway map from Escher format to Vega format.

    Args:
        escher_filename (:obj:`str`): path to the map in Escher format
        vega_filename (:obj:`str`): path to save the map in Vega format
        reaction_fluxes (:obj:`dict`, optional): dictionary that maps the id of each reaction to its predicted flux.
        max_width_height (:obj:`int`): maximum height/width of the metabolic map in pixels
        legend_padding (:obj:`int`): horizontal spacing between the metabolic map and legend in pixels
        legend_width (:obj:`int`): legend width in pixels, including the width of the title
        indent (:obj:`int` or :obj:`None`, optional): indentation
    """
    # read the Escher version of the map
    with open(escher_filename, 'r') as file:
        escher = json.load(file)

    # determine the extent (min/max x/y) of the map
    min_x = math.inf
    min_y = math.inf
    max_x = -math.inf
    max_y = -math.inf

    nodes = escher[1]['nodes']
    for node in nodes.values():
        min_x = min(min_x, node['x'])
        min_y = min(min_y, node['y'])
        max_x = max(max_x, node['x'])
        max_y = max(max_y, node['y'])

        if 'label_x' in node:
            min_x = min(min_x, node['label_x'])
            min_y = min(min_y, node['label_y'])
            max_x = max(max_x, node['label_x'])
            max_y = max(max_y, node['label_y'])

    for reaction in escher[1]['reactions'].values():
        if 'label_x' in reaction:
            min_x = min(min_x, reaction['label_x'])
            min_y = min(min_y, reaction['label_y'])
            max_x = max(max_x, reaction['label_x'])
            max_y = max(max_y, reaction['label_y'])

    escher_width = max_x - min_x
    escher_height = max_y - min_y

    if escher_width > escher_height:
        width = max_width_height
        coordinate_scale = width / escher_width
        height = escher_height * coordinate_scale
    else:
        height = max_width_height
        coordinate_scale = height / escher_height
        width = escher_width * coordinate_scale

    # convert metabolite circle nodes to Vega
    metabolites = []
    for id, node in nodes.items():
        node["id"] = id

        node["x"] = (node["x"] - min_x) * coordinate_scale
        node["y"] = (node["y"] - min_y) * coordinate_scale

        if "label_x" in node:
            node["label_x"] = (node["label_x"] - min_x) * coordinate_scale
            node["label_y"] = (node["label_y"] - min_y) * coordinate_scale

        if node["node_type"] == "metabolite":
            metabolites.append(node)

    # convert reaction paths to Vega
    reactions = []
    for id, reaction in escher[1]['reactions'].items():
        reaction["id"] = id

        reaction["label_x"] = (reaction["label_x"] - min_x) * coordinate_scale
        reaction["label_y"] = (reaction["label_y"] - min_x) * coordinate_scale

        reaction["path"] = []
        for segment in reaction["segments"].values():
            from_node = nodes[segment["from_node_id"]]
            to_node = nodes[segment["to_node_id"]]

            if segment["b1"]:
                segment_path = [
                    'M{},{}'.format(from_node["x"], from_node["y"]),
                    'C{},{}'.format((segment["b1"]["x"] - min_x) * coordinate_scale, (segment["b2"]["y"] - min_y) * coordinate_scale),
                    '{},{}'.format((segment["b2"]["x"] - min_x) * coordinate_scale, (segment["b2"]["y"] - min_y) * coordinate_scale),
                    '{},{}'.format(to_node["x"], to_node["y"]),
                ]
            else:
                segment_path = [
                    'M{},{}'.format(from_node["x"], from_node["y"]),
                    'L{},{}'.format(to_node["x"], to_node["y"]),
                ]

            reaction["path"].append(" ".join(segment_path))

        reaction["path"] = ''.join(reaction["path"])

        reactions.append(reaction)

    # reaction flux data
    reaction_fluxes = reaction_fluxes or {}
    vega_reaction_fluxes = []
    for reaction in reactions:
        flux = reaction_fluxes.get(reaction["id"], None)
        if flux is not None:
            vega_reaction_fluxes.append({
                'id': reaction['id'],
                'flux': flux
            })

    # insert metabolite circles and reaction paths into Vega template
    with open(os.path.join(os.path.dirname(__file__), 'escher_to_vega.template.json'), 'r') as file:
        vega = json.load(file)

    vega['width'] = width + legend_padding + legend_width
    vega['height'] = height

    metabolites_data = next(data for data in vega['data'] if data['name'] == 'metabolites')
    metabolites_data['values'] = metabolites

    reactions_data = next(data for data in vega['data'] if data['name'] == 'reactions')
    reactions_data['values'] = reactions

    reaction_fluxes_data = next(data for data in vega['data'] if data['name'] == 'reactionFluxes')
    reaction_fluxes_data['values'] = vega_reaction_fluxes

    legend = vega['legends'][0]
    legend["legendX"] = width + legend_padding
    legend["gradientLength"] = height - 2 * legend["legendY"] - legend["titleFontSize"] - legend["titlePadding"]

    # save Vega-formatted map
    with open(vega_filename, 'w') as file:
        json.dump(vega, file, indent=indent)
