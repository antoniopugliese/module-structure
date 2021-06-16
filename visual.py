"""
This module is used to display the module structure network.

The display function is heavily adapted from this user: https://github.com/xhlulu.
"""

import dash
import dash_cytoscape as cyto
from dash.dependencies import Input, Output
import dash_html_components as html
import dash_core_components as dcc
import dash_reusable_components as drc

import webbrowser as web
import networkx as nx
import os

import subgraph


def get_data(graph: nx.MultiDiGraph):
    """
    Transforms the node and edge data to a format that can be displayed.

   :param graph: the graph of the data
   :type graph: networkx.MultiDiGraph
    """
    n_list = [{
        'data': {
            'id': node.get_name(),
            'label': node.get_name().split(os.sep)[-1]}
    } for node in graph.nodes]

    e_list = [{
        'data': {
            'source':  u.get_name(),
            'target': v.get_name()}
    } for u, v, d in graph.edges]

    return n_list + e_list


def display(graph):
    """
    Creates the Dash app and runs the development server.

    :param graph: the graph to display 
    :type graph: networkx.MultiDiGraph
    """
    styles = {
        'json-output': {
            'overflow-y': 'scroll',
            'height': 'calc(50% - 25px)',
            'border': 'thin lightgrey solid'
        },
        'tab': {
            'height': 'calc(98vh - 105px)'
        }
    }

    default_stylesheet = [
        {
            "selector": 'edge',
            'style': {
                "curve-style": "bezier",
                "opacity": 0.65
            }
        },
    ]

    app = dash.Dash(__name__)
    app.layout = html.Div([
        html.Div(className='eight columns',
                 style={'width': '70%',
                        'position': 'relative',
                        'float': 'left',
                        'font-size': 16
                        }, children=[
                     cyto.Cytoscape(
                         id='subgraph',
                         layout={'name': 'concentric'},
                         style={'width': '100%', 'height': '750px'},
                         elements=[],
                     )
                 ]),

        html.Div(className='four columns',
                 style={'width': '30%',
                        'position': 'relative',
                        'float': 'left'}, children=[
                     dcc.Tabs(id='tabs', children=[
                         dcc.Tab(label='Control Panel', children=[
                             drc.NamedDropdown(
                                 name='Layout',
                                 id='dropdown-layout',
                                 options=drc.DropdownOptionsList(
                                     'grid',
                                     'random',
                                     'circle',
                                     'concentric',
                                     'breadthfirst',
                                     'cose'
                                 ),
                                 value='breadthfirst',
                                 clearable=False
                             ),
                             drc.NamedDropdown(
                                 name='Node Preferences',
                                 id='dropdown-node-preferences',
                                 options=drc.DropdownOptionsList(
                                     *subgraph.NODES),
                                 value=['Folder', 'File'],
                                 clearable=False,
                                 multi=True
                             ),
                             drc.NamedDropdown(
                                 name='Edge Preferences',
                                 id='dropdown-edge-preferences',
                                 options=drc.DropdownOptionsList(
                                     *subgraph.EDGES),
                                 value=['Directory'],
                                 clearable=False,
                                 multi=True
                             ),
                             drc.NamedInput(
                                 name='Followers Color',
                                 id='input-follower-color',
                                 type='text',
                                 value='#0074D9',
                             ),
                             drc.NamedInput(
                                 name='Following Color',
                                 id='input-following-color',
                                 type='text',
                                 value='#FF4136',
                             ),
                             drc.NamedDropdown(
                                 name='Show 0 Degree Nodes',
                                 id='dropdown-show-empty',
                                 options=drc.DropdownOptionsList(
                                     "Yes", "No"),
                                 value="Yes",
                                 clearable=False,
                             ),
                         ]),
                     ]),
                 ])
    ])

    @app.callback(Output('subgraph', 'layout'),
                  [Input('dropdown-layout', 'value')])
    def update_graph_layout(layout):
        return {'name': layout}

    @app.callback(Output('subgraph', 'elements'),
                  [Input('dropdown-node-preferences', 'value'),
                  Input('dropdown-edge-preferences', 'value'),
                  Input('dropdown-show-empty', 'value')])
    def update_graph_data(node_list, edge_list, show_empty):
        new_graph = subgraph.subgraph(graph, node_list, edge_list)
        if show_empty == "No":
            removes = []
            for n in new_graph.nodes:
                if new_graph.degree(n) == 0:
                    removes.append(n)
            new_graph.remove_nodes_from(removes)
        return get_data(new_graph)

    @app.callback(Output('subgraph', 'stylesheet'),
                  [Input('subgraph', 'tapNode'),
                   Input('input-follower-color', 'value'),
                   Input('input-following-color', 'value'),
                   ])
    def generate_stylesheet(node, follower_color, following_color):
        if not node:
            return default_stylesheet

        stylesheet = [{
            "selector": 'node',
            'style': {
                'opacity': 0.3,
                'shape': 'ellipse',
            }
        }, {
            'selector': 'edge',
            'style': {
                'opacity': 0.2,
                "curve-style": "bezier",
            }
        }, {
            "selector": 'node[id = "{}"]'.format(node['data']['id']),
            "style": {
                'background-color': '#B10DC9',
                "border-color": "purple",
                "border-width": 2,
                "border-opacity": 1,
                "opacity": 1,

                "label": "data(label)",
                "color": "#B10DC9",
                "text-opacity": 1,
                "font-size": 16,
                'z-index': 9999
            }
        }]

        for edge in node['edgesData']:
            if edge['source'] == node['data']['id']:
                stylesheet.append({
                    "selector": 'node[id = "{}"]'.format(edge['target']),
                    "style": {
                        'background-color': following_color,
                        'opacity': 0.9,
                        "label": "data(label)",
                    }
                })
                stylesheet.append({
                    "selector": 'edge[id= "{}"]'.format(edge['id']),
                    "style": {
                        "mid-target-arrow-color": following_color,
                        "mid-target-arrow-shape": "vee",
                        "line-color": following_color,
                        'opacity': 0.9,
                        'z-index': 5000,
                    }
                })

            if edge['target'] == node['data']['id']:
                stylesheet.append({
                    "selector": 'node[id = "{}"]'.format(edge['source']),
                    "style": {
                        'background-color': follower_color,
                        'opacity': 0.9,
                        'z-index': 9999,
                        "label": "data(label)",
                    }
                })
                stylesheet.append({
                    "selector": 'edge[id= "{}"]'.format(edge['id']),
                    "style": {
                        "mid-target-arrow-color": follower_color,
                        "mid-target-arrow-shape": "vee",
                        "line-color": follower_color,
                        'opacity': 1,
                        'z-index': 5000
                    }
                })

        return stylesheet

    # this url might not be universal
    web.open("http://127.0.0.1:8050/")
    app.run_server(debug=True, use_reloader=False)
