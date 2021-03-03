""" Utilities for converting metabolic maps from Escher to Vega format

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2021-02-06
:Copyright: 2021, Center for Reproducible Biomedical Modeling
:License: MIT
"""

import bezier
import json
import math
import numpy
import os

__all__ = ['escher_to_vega']


def escher_to_vega(escher_filename, vega_filename, reaction_fluxes=None,
                   max_width_height=800, legend_padding=20, legend_width=40,
                   arrow_head_gap=16., indent=2):
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
        if node["node_type"] == "metabolite":
            metabolite = {}

            metabolite["id"] = id
            metabolite["biggId"] = node['bigg_id']
            metabolite["name"] = node['name']

            metabolite["x"] = (node["x"] - min_x) * coordinate_scale
            metabolite["y"] = (node["y"] - min_y) * coordinate_scale

            if node.get('node_is_primary', False):
                metabolite['size'] = 10 ** 2 * coordinate_scale
            else:
                metabolite['size'] = 20 ** 2 * coordinate_scale

            if "label_x" in node:
                metabolite["labelX"] = (node["label_x"] - min_x) * coordinate_scale
                metabolite["labelY"] = (node["label_y"] - min_y) * coordinate_scale

            reaction_ids = set()
            for rxn_id, reaction in escher[1]['reactions'].items():
                for segment in reaction["segments"].values():
                    if segment["from_node_id"] == id or segment["to_node_id"] == id:
                        reaction_ids.add(rxn_id)
                        break
            metabolite['reactionIds'] = list(reaction_ids)
            metabolite['metaboliteIds'] = []

            related_metabolite_ids = set()
            for reaction_id in reaction_ids:
                reaction = escher[1]['reactions'][reaction_id]

                for segment in reaction["segments"].values():
                    from_node = nodes[segment["from_node_id"]]
                    to_node = nodes[segment["to_node_id"]]

                    if from_node["node_type"] == "metabolite":
                        related_metabolite_ids.add(segment["from_node_id"])
                    if to_node['node_type'] == 'metabolite':
                        related_metabolite_ids.add(segment["to_node_id"])
            metabolite['relatedMetaboliteIds'] = list(related_metabolite_ids)

            metabolites.append(metabolite)

    # convert reaction paths to Vega
    reaction_segment_coordinates = []
    reaction_arrow_head_coordinates = []
    reaction_labels = []
    for id, reaction in escher[1]['reactions'].items():
        metabolite_ids = set()
        for rxn_id, other_reaction in escher[1]['reactions'].items():
            if other_reaction['bigg_id'] == reaction['bigg_id']:
                for segment in reaction["segments"].values():
                    from_node = nodes[segment["from_node_id"]]
                    to_node = nodes[segment["to_node_id"]]

                    if from_node["node_type"] == "metabolite":
                        metabolite_ids.add(segment["from_node_id"])
                    if to_node['node_type'] == 'metabolite':
                        metabolite_ids.add(segment["to_node_id"])
        metabolite_ids = list(metabolite_ids)

        reaction_labels.append({
            "id": id,
            "biggId": reaction["bigg_id"],
            "x": (reaction["label_x"] - min_x) * coordinate_scale,
            "y": (reaction["label_y"] - min_y) * coordinate_scale,
            'metaboliteIds': metabolite_ids,
            'relatedMetaboliteIds': [],
        })

        for segment in reaction["segments"].values():
            from_node = nodes[segment["from_node_id"]]
            to_node = nodes[segment["to_node_id"]]

            if from_node['node_type'] == 'metabolite':
                if segment['b1']:
                    points = [
                        [from_node['x'], from_node['y']],
                        [segment['b1']['x'], segment['b1']['y']],
                        [segment['b2']['x'], segment['b2']['y']],
                        [to_node['x'], to_node['y']],
                    ]
                    segment_len = bezier.Curve(numpy.array(points).transpose(), degree=3).length
                    t = min(1., arrow_head_gap / segment_len)
                    x0, y0 = bezier_point(points, t)
                    angle = bezier_angle(points, t) - 90.
                else:
                    segment_len = math.sqrt((from_node['x'] - to_node['x']) ** 2 (from_node['y'] - to_node['y']) ** 2)
                    angle = math.atan2(from_node['y'] - to_node['y'], from_node['x'] - to_node['x'])
                    t = min(1., arrow_head_gap / segment_len)
                    x0 = from_node["x"] * (1 - t) + to_node["x"] * t
                    y0 = from_node["y"] * (1 - t) + to_node["y"] * t

                reaction_arrow_head_coordinates.append({
                    'id': id,
                    'biggId': reaction['bigg_id'],
                    'start': True,
                    'x': (x0 - min_x) * coordinate_scale,
                    'y': (y0 - min_y) * coordinate_scale,
                    'angle': angle,
                    'metaboliteIds': metabolite_ids,
                    'relatedMetaboliteIds': [],
                })
            else:
                x0 = from_node["x"]
                y0 = from_node["y"]

            if to_node['node_type'] == 'metabolite':
                if segment['b1']:
                    points = [
                        [from_node['x'], from_node['y']],
                        [segment['b1']['x'], segment['b1']['y']],
                        [segment['b2']['x'], segment['b2']['y']],
                        [to_node['x'], to_node['y']],
                    ]
                    segment_len = bezier.Curve(numpy.array(points).transpose(), degree=3).length
                    t = max(0., 1. - arrow_head_gap / segment_len)
                    x3, y3 = bezier_point(points, t)
                    angle = bezier_angle(points, t) + 90.
                else:
                    segment_len = math.sqrt((from_node['x'] - to_node['x']) ** 2 (from_node['y'] - to_node['y']) ** 2)
                    angle = math.atan2(to_node['y'] - from_node['y'], to_node['x'] - from_node['x'])
                    t = max(0., 1. - arrow_head_gap / segment_len)
                    x3 = from_node["x"] * (1 - t) + to_node["x"] * t
                    y3 = from_node["y"] * (1 - t) + to_node["y"] * t

                reaction_arrow_head_coordinates.append({
                    'id': id,
                    'biggId': reaction['bigg_id'],
                    'start': False,
                    'x': (x3 - min_x) * coordinate_scale,
                    'y': (y3 - min_y) * coordinate_scale,
                    'angle': angle,
                    'metaboliteIds': metabolite_ids,
                    'relatedMetaboliteIds': [],
                })
            else:
                x3 = to_node["x"]
                y3 = to_node["y"]

            if segment["b1"]:
                reaction_segment_coordinates.append({
                    "id": id,
                    "biggId": reaction["bigg_id"],
                    "name": reaction["name"],
                    'type': 'curve',
                    'x0': (x0 - min_x) * coordinate_scale,
                    'y0': (y0 - min_y) * coordinate_scale,
                    'x1': (segment["b1"]["x"] - min_x) * coordinate_scale,
                    'y1': (segment["b1"]["y"] - min_y) * coordinate_scale,
                    'x2': (segment["b2"]["x"] - min_x) * coordinate_scale,
                    'y2': (segment["b2"]["y"] - min_y) * coordinate_scale,
                    'x3': (x3 - min_x) * coordinate_scale,
                    'y3': (y3 - min_y) * coordinate_scale,
                    'metaboliteIds': metabolite_ids,
                    'relatedMetaboliteIds': [],
                })
            else:
                reaction_segment_coordinates.append({
                    "id": id,
                    "biggId": reaction["bigg_id"],
                    "name": reaction["name"],
                    'type': 'line',
                    'x0': (x0 - min_x) * coordinate_scale,
                    'y0': (y0 - min_y) * coordinate_scale,
                    'x1': (x3 - min_x) * coordinate_scale,
                    'y1': (y3 - min_y) * coordinate_scale,
                    'metaboliteIds': metabolite_ids,
                    'relatedMetaboliteIds': [],
                })

    # reaction flux data
    reaction_fluxes = reaction_fluxes or {}
    vega_reaction_fluxes = []
    for reaction in escher[1]['reactions'].values():
        id = reaction['bigg_id']
        flux = reaction_fluxes.get(id, None)
        if flux is not None:
            vega_reaction_fluxes.append({
                'biggId': id,
                'flux': flux
            })

    # insert metabolite circles and reaction paths into Vega template
    with open(os.path.join(os.path.dirname(__file__), 'escher_to_vega.template.json'), 'r') as file:
        vega = json.load(file)

    vega['width'] = width + legend_padding + legend_width
    vega['height'] = height

    map_width_signal = next(signal for signal in vega['signals'] if signal['name'] == 'mapWidth')
    map_width_signal['value'] = width

    map_height_signal = next(signal for signal in vega['signals'] if signal['name'] == 'mapHeight')
    map_height_signal['value'] = height

    metabolite_stroke_width_signal = next(signal for signal in vega['signals'] if signal['name'] == 'metaboliteStrokeWidthData')
    metabolite_stroke_width_signal['value'] = 2 * coordinate_scale

    reaction_stroke_width_signal = next(signal for signal in vega['signals'] if signal['name'] == 'reactionStrokeWidthData')
    reaction_stroke_width_signal['value'] = 18 * coordinate_scale

    arrow_head_stroke_width_signal = next(signal for signal in vega['signals'] if signal['name'] == 'arrowHeadStrokeWidthData')
    arrow_head_stroke_width_signal['value'] = 1 * coordinate_scale

    metabolites_data = next(data for data in vega['data'] if data['name'] == 'metabolitesData')
    metabolites_data['values'] = metabolites

    reactions_data = next(data for data in vega['data'] if data['name'] == 'reactionSegmentCoordinatesData')
    reactions_data['values'] = reaction_segment_coordinates

    reactions_data = next(data for data in vega['data'] if data['name'] == 'reactionArrowHeadCoordinatesData')
    reactions_data['values'] = reaction_arrow_head_coordinates

    reactions_data = next(data for data in vega['data'] if data['name'] == 'reactionLabelsData')
    reactions_data['values'] = reaction_labels

    reaction_fluxes_data = next(data for data in vega['data'] if data['name'] == 'reactionFluxes')
    reaction_fluxes_data['values'] = vega_reaction_fluxes

    legend = vega['legends'][0]
    legend["legendX"] = width + legend_padding
    legend["gradientLength"] = height - 2 * legend["legendY"] - legend["titleFontSize"] - legend["titlePadding"]

    # save Vega-formatted map
    with open(vega_filename, 'w') as file:
        json.dump(vega, file, indent=indent)


def bezier_point(points, t):
    return (
        (
            ((1. - t) ** 3.) * points[0][0]
            + 3. * t * ((1. - t) ** 2.) * points[1][0]
            + (3. * t ** 2.) * (1. - t) * points[2][0]
            + (t ** 3.) * points[3][0]
        ),
        (
            ((1. - t) ** 3.) * points[0][1]
            + 3. * t * ((1. - t) ** 2.) * points[1][1]
            + 3. * (t ** 2.) * (1. - t) * points[2][1]
            + (t ** 3.) * points[3][1]
        ),
    )


def bezier_angle(points, t):
    dx = (
        (1 - t) ** 2 * (points[1][0] - points[0][0])
        + 2 * t * (1 - t) * (points[2][0] - points[1][0])
        + t ** 2 * (points[3][0] - points[2][0])
    )
    dy = (
        (1 - t) ** 2 * (points[1][1] - points[0][1])
        + 2 * t * (1 - t) * (points[2][1] - points[1][1])
        + t ** 2 * (points[3][1] - points[2][1])
    )
    return math.atan2(dy, dx) * 180 / math.pi
