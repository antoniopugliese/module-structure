"""
This module is used to display the module structure network.

The display function is heavily adapted from this user: https://github.com/xhlulu.
"""

import dash
import dash_cytoscape as cyto
from dash.dependencies import Input, Output
from dash.exceptions import PreventUpdate
import dash_html_components as html
import dash_core_components as dcc
import dash_reusable_components as drc

import webbrowser as web
import networkx as nx
import os

import subgraph

# for development purposes only. If True, the web browser refreshes whenever
# chanegs are made to this file
DEBUG_MODE = False

# Graph presets. 'name' : ( [included_nodes], [included_edges], layout, show_nodes )
PRESETS = {
    'file directory': (['Folder', 'File'], ['Directory'], 'breadthfirst', 'Yes'),
    'class inheritance': (["Class"], ["Inheritance"], 'cose', 'No'),
    'function dependency': (["File", "Class", "Function"], ["Function Call"], 'circle', 'No'),
    'import dependency': (["File"], ["Import"], 'concentric', 'No'),
    'definitions': (["File", "Folder", "Class", "Function"], ["Definition"], 'cose', 'No',),
    'custom': ([], [], 'concentric', 'Yes')
}


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
                         id='graph',
                         layout={'name': 'concentric'},
                         style={'width': '100%', 'height': '750px'},
                         elements=[],
                     )
                 ]),
        html.Div(hidden=True, children=[
                 dcc.Store(id='prev-node', data=None)]),
        html.Div(className='four columns',
                 style={'width': '30%',
                        'position': 'relative',
                        'float': 'left'}, children=[
                     dcc.Tabs(id='tabs', children=[
                         dcc.Tab(label='Control Panel', children=[
                             drc.NamedDropdown(
                                 name='Presets',
                                 id='dropdown-presets',
                                 options=drc.DropdownOptionsList(
                                     'file directory',
                                     'class inheritance',
                                     'import dependency',
                                     'function dependency',
                                     'definitions',
                                     'custom'
                                 ),
                                 value='file directory',
                                 clearable=False
                             ),
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
                             html.Div(id='preferences-container', hidden=True, children=[
                                 drc.NamedDropdown(
                                     name='Node Preferences',
                                     id='dropdown-node-preferences',
                                     options=drc.DropdownOptionsList(
                                         *subgraph.NODES),
                                     value=[],
                                     clearable=False,
                                     multi=True
                                 ),
                                 drc.NamedDropdown(
                                     name='Edge Preferences',
                                     id='dropdown-edge-preferences',
                                     options=drc.DropdownOptionsList(
                                         *subgraph.EDGES),
                                     value=[],
                                     clearable=False,
                                     multi=True
                                 ), ]),
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
                             drc.NamedInput(
                                 name='Root Color',
                                 id='input-root-color',
                                 type='text',
                                 value='#000000',
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

    @app.callback(Output('graph', 'layout'),
                  [Input('dropdown-layout', 'value')])
    def update_graph_layout(layout):
        return {'name': layout}

    # might be a way to combine these into one function
    @app.callback([Output('dropdown-node-preferences', 'value'),
                   Output('dropdown-edge-preferences', 'value'),
                   Output('dropdown-layout', 'value'),
                   Output('dropdown-show-empty', 'value')],
                  [Input('dropdown-presets', 'value')])
    def preset_graph(preset):
        if preset == 'custom':
            raise PreventUpdate
        nodes, edges, layout, show_empty = PRESETS.get(
            preset, 'invalid preset')
        return (nodes, edges, layout, show_empty)

    @app.callback(Output('preferences-container', 'hidden'),
                  [Input('dropdown-presets', 'value')])
    def unhide_preferences(preset):
        if preset == "custom":
            return False
        else:
            return True

    @app.callback(Output('graph', 'elements'),
                  [Input('dropdown-node-preferences', 'value'),
                  Input('dropdown-edge-preferences', 'value'),
                  Input('dropdown-show-empty', 'value'),
                  Input('input-root-color', 'value')])
    def update_graph_data(node_list, edge_list, show_empty, root_color):
        stylesheet = default_stylesheet
        new_graph = subgraph.subgraph(graph, node_list, edge_list)

        # iterates through all nodes and colors root nodes and removes nodes
        # according to user preference
        removes = []
        for n in new_graph.nodes:
            if show_empty == "No" and new_graph.degree(n) == 0:
                removes.append(n)
            if new_graph.in_degree(n) == 0 and new_graph.out_degree != 0:
                stylesheet.append({
                    "selector": 'node[id = "{}"]'.format(n.get_name()),
                    "style": {
                        'background-color': root_color,
                        'opacity': 0.9,
                        "label": "data(label)",
                    }
                })

        new_graph.remove_nodes_from(removes)
        return get_data(new_graph)

    @app.callback([Output('graph', 'stylesheet'), Output('prev-node', 'data')],
                  [Input('graph', 'tapNode'),
                   Input('prev-node', 'data'),
                   Input('input-follower-color', 'value'),
                   Input('input-following-color', 'value')])
    def generate_stylesheet(node, prev_node_data, follower_color, following_color):
        if node is None or node['data']['id'] == prev_node_data['prev_node']:
            return (default_stylesheet, {'prev_node': None})

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

        return (stylesheet, {'prev_node': node['data']['id']})

    # this url might not be universal
    web.open("http://127.0.0.1:8050/")
    if DEBUG_MODE:
        app.run_server(debug=True)
    else:
        app.run_server(debug=True, use_reloader=False)
