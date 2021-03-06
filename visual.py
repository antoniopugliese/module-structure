"""
This module is used to display the module structure network.

This entire module utilizes dash cytoscape and is entirely based on python. A 
faster, more detailed exploration of the graph is found within the frontend 
directory.

The display function is heavily adapted from this user: https://github.com/xhlulu.
"""

import dash
import dash_cytoscape as cyto
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
import dash_html_components as html
import dash_core_components as dcc
import dash_reusable_components as drc

import plotly.express as px
import pandas as pd
from git.objects.commit import Commit
import networkx as nx
from networkx import MultiDiGraph
import webbrowser as web
import os
import pickle
from datetime import datetime
import redis
import math

import subgraph
import node
import edge
import metrics
import matrix

# for development purposes only. If True, the web browser refreshes whenever
# chanegs are made to this file
DEBUG_MODE = False

# Graph presets. 'name' : ( [included_nodes], [included_edges], layout, show_nodes, description )
### possibly move into a json file ###
PRESETS = {
    'file directory': (['Folder', 'File'], ['Directory'], 'breadthfirst', 'Yes',
                       "The file organization of the repo. Nodes are either folders or Python files. " +
                       "A directed edge from **u** to **v** represents '**u** is the parent folder of **v**.'"),
    'class inheritance': (["Class"], ["Inheritance"], 'cose', 'No',
                          "The classes that inherit from another class defined within the repo. Nodes are Python classes. " +
                          "A directed edge from **u** to **v** represents '**u** is a parent class for **v**.'"),
    'function dependency': (["File", "Class", "Function"], ["Function Call"], 'circle', 'No',
                            "The function calls within the repo. Nodes represent a Python file, function, or class. " +
                            "A directed edge from **u** to **v**  represents '**u** is called by **v**.'"),
    'import dependency': (["File", "Folder"], ["Import"], 'concentric', 'No',
                          "The imports of each Python file. Nodes are Python files or folders (as Python packages). " +
                          "A directed edge from **u** to **v**  represents '**u** is imported by **v**.'"),
    'broad definitions': (["File", "Class", "Function"], ["Definition"], 'cose', 'No',
                          "The organization of Python class and function definitions. Nodes are files, functions, or classes. " +
                          "A directed edge from **u** to **v**  represents '**u** defines **v**.'"),
    'granular definitions': (["File", "Class", "Function", "Variable", "Lambda", "If", "For", "While", "Try"], ["Definition"], 'cose', 'No',
                             "The variables, lambda expressions, if-statements, for loops, while loops, and try-statements defined within Python files." +
                             "A directed edge from **u** to **v**  represents '**u** defines **v**.'"),
    'all': (["File", "Folder", "Class", "Function"], ["Inheritance", "Directory", "Function Call", "Import", "Definition"], 'concentric', 'No',
            "Every type of node and edge displayed at once."),
    'custom': ([], [], 'concentric', 'Yes', "Choose the Node and Edge types to include. ")
}

NODE_SHAPES = {
    node.FolderNode: 'ellipse',
    node.FileNode: 'triangle',
    node.ClassNode: 'rectangle',
    node.FuncNode: 'pentagon',
    node.VarNode: 'pentagon',
    node.LambdaNode: 'hexagon',
    node.IfNode: 'hexagon',
    node.ForNode: 'hexagon',
    node.WhileNode: 'hexagon',
    node.TryNode: 'hexagon',
}

EDGE_STYLE = {
    edge.DirectoryEdge: 'solid',
    edge.DefinitionEdge: 'solid',
    edge.ImportEdge: 'dashed',
    edge.InheritanceEdge: 'dashed',
    edge.FunctionCallEdge: 'dotted',
    edge.VariableEdge: 'dotted'
}


def get_graph_data(graph: nx.MultiDiGraph, positions=None):
    """
    Transforms the node and edge data to a format that can be displayed.

   :param graph: the graph of the data
   :type graph: networkx.MultiDiGraph

   :param positions: The networkx positions of the nodes that will be used if provided.
   :type positions: {Node : (int,int)} 

   :return: a list of all node and edge data in the graph
   :rtype: str list
    """
    if not positions:
        n_list = [{
            'data': {
                'id': node.get_name(),
                'label': node.get_name().split(os.sep)[-1]}
        } for node in graph.nodes]
    else:
        n_list = [{
            'data': {
                'id': node.get_name(),
                'label': node.get_name().split(os.sep)[-1]},
            'position': {'x': positions[node][0], 'y':positions[node][1]}
        } for node in graph.nodes]

    e_list = [{
        'data': {
            'id': f'{str(type(d))}{d.__hash__}',
            'source':  u.get_name(),
            'target': v.get_name()}
    } for u, v, d in graph.edges(data='edge')]

    return n_list + e_list


def get_commit_data(commits, commit_dict, preset='all', matrix_type='adjacency', spectrum_type='eigenvalue'):
    """
    Computes data from the provided commits that can be graphed.

    :param commits: the commit objects to analyze
    :type commits: git.objects.commit.Commit list

    :param commit_dict: the sha1-graph dictionary for the repo
    :type commit_dict: {str : networkx.MultiDiGraph}

    :param preset: the subgraph preset to analyze the commit graphs with. Defaults to 'all'.
    :type preset: str

    :return: the data to plot on a x-axis and y-axis, respectively.
    :rtype: tuple
    """
    subgraphs = metrics.unique_subgraphs(commit_dict, preset)
    commit_times = metrics.get_dates(commits)

    x = []
    y = []

    for graph, sha1_list in subgraphs:

        # Graph energy for testing
        mat = matrix.graph_to_matrix(graph, matrix=matrix_type)
        eig_vals = matrix.analyze_matrix(mat, type=spectrum_type)[0]
        energy = 0
        for val in eig_vals:
            energy += abs(val)

        # create data points
        for sha1 in sha1_list:
            try:
                date = commit_times[sha1]
                x.append(date)
                y.append(energy)
            except KeyError:
                pass

    return (x, y)


def ControlTab():
    """
    The component that changes the settings and layout of the graph.
    """
    return dcc.Tab(label='Control Panel', children=[
        drc.NamedRadioItems(id='radio-mode', name='Choose graph mode', options=drc.DropdownOptionsList(
            'exploration',
            'overview'
        ), value='exploration'),
        drc.NamedDropdown(
            name='Presets',
            id='dropdown-presets',
            options=drc.DropdownOptionsList(
                *PRESETS
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
        # hide color choosing for now
        html.Div(id='choose-colors-container', hidden=True, children=[
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
        ]),
        drc.NamedDropdown(
            name='Show 0 Degree Nodes',
            id='dropdown-show-empty',
            options=drc.DropdownOptionsList(
                "Yes", "No"),
            value="Yes",
            clearable=False,
        ),
        drc.Card(title='Preset Description',
                 id='description-card',
                 children=[],
                 style={'padding': 5,
                        'margin': 5, }),
        drc.NamedCard(title='Legend', id='legend-card', size=1, children=[
            cyto.Cytoscape(id='legend-graph', layout={'name': 'grid', 'columns': 3},
                           style={'width': '100%', 'height': '150px'},
                           elements=[],
                           stylesheet=[],
                           pan={'x': 0, 'y': 25},
                           userPanningEnabled=False,
                           userZoomingEnabled=False
                           )],
                      style={'padding': 5,
                             'margin': 10, }
                      )
    ])


def AnalysisTab(dates: list[datetime], commits):
    """
    The component that allows for many commits to be analyzed,and to choose the
    current commit to graph.
    """
    return dcc.Tab(label='Analysis', children=[
        dcc.Checklist(
            id='choose-commit', options=[{'label': 'Choose Commit', 'value': 'show'}]),
        html.Div(id='commit-chooser', hidden=True, children=[
            drc.NamedDropdown(id='dropdown-commit-picker', name='Pick Commit SHA1',
                              options=[{'label': commit.hexsha, 'value': commit.hexsha} for commit in commits], clearable=False, value=commits[0].hexsha),
            html.Div(id='commit-picked', children=[]), ]),
        dcc.Checklist(
            id='show-commits', options=[{'label': 'Show commit history', 'value': 'show'}]),
        html.Div(id='commit-chart-options', hidden=True, children=[
            drc.NamedRangeSlider(name='Pick Date Range', id='slider-date-picker',
                                 min=0, max=len(dates) - 1, step=1, value=[0, len(dates) - 1],
                                 allowCross=False
                                 ),
            html.Div(id='date-picked', children=[]),
            drc.NamedDropdown(
                name='Matrix Type',
                id='dropdown-matrix-type',
                options=drc.DropdownOptionsList(
                    *matrix.MATRIX),
                value='adjacency',
                clearable=False),
            drc.NamedDropdown(
                name='Spectrum Type',
                id='dropdown-spectrum-type',
                options=drc.DropdownOptionsList(
                    *matrix.SPECTRUM),
                value='eigenvalue',
                clearable=False)
        ]),
    ])


# possible move to subgraph.py
def get_roots(graph):
    """
    Lists the id's of the roots of ``graph``.
    """
    roots = []
    for n in graph.nodes:
        # if n is a root
        if graph.in_degree(n) == 0 and graph.degree(n) != 0:
            roots.append(n.get_name())

    return roots


def display(repo_name: str, rs: redis.Redis, commits: list[Commit], commit_dict: dict[str, MultiDiGraph]):
    """
    Creates the Dash app and runs the development server.

    :param commits: the list of Commit objects of the repo to display.
    :type commits: Commit list

    :param commit_dict: the dictionary produced by the main module mapping SHA1 to relationship graph of each commit.
    :type commit_dict: {str, MultiDiGraph} dict
    """
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
        html.Div(children=[
            dcc.Store(id='prev-node', data={'prev_node': None}),
            dcc.Store(id='graph-sha1', data={'graph_sha1': commits[0].hexsha}),
            dcc.Store(id='exploration-nodes', data={'nodes': []})
        ]),
        html.Div(id='empty-container', hidden=True, children=[]),
        html.Div(className='eight columns',
                 style={'width': '70%',
                        'position': 'relative',
                        'float': 'left',
                        'font-size': 16,
                        }, children=[
                     drc.Card(id='graph-container', style={'padding': 5, 'margin': 5},
                              children=[cyto.Cytoscape(
                                  id='graph',
                                  layout={'name': 'concentric'},
                                  style={'width': '100%', 'height': '750px'},
                                  elements=[],
                                  stylesheet=default_stylesheet),
                     ]),
                     drc.Card(style={'padding': 5, 'margin': 5},
                              id='commit-chart-container', hidden=True,
                              children=[dcc.Graph(id="commit-chart", figure={}, style={'height': '250px'})
                                        ]),
                 ]),
        html.Div(className='four columns',
                 style={'width': '30%',
                        'position': 'relative',
                        'float': 'left'}, children=[
                     dcc.Tabs(id='tabs', children=[
                         ControlTab(),
                         AnalysisTab(
                             list(metrics.get_dates(commits).values()), commits),
                     ]),
                 ])
    ])

    @app.callback([Output('legend-graph', 'elements'), Output('legend-graph', 'stylesheet')], [Input('dropdown-node-preferences', 'value'),
                                                                                               Input('dropdown-edge-preferences', 'value')])
    def update_legend(node_list, edge_list):
        elems = []
        stylesheet = []

        for n in node_list:
            type = subgraph.str_to_node(n)
            shape = NODE_SHAPES.get(type)

            elems.append({
                'data': {
                    'id': n,
                    'label': n},
            })

            stylesheet.append({
                'selector': 'node[id = "{}"]'.format(n),
                'style': {
                    'label': 'data(label)',
                    'shape': shape
                }
            })

        return elems, stylesheet

    @app.callback(Output('exploration-nodes', 'data'),
                  [Input('radio-mode', 'value'),
                   Input('exploration-nodes', 'data'),
                   Input('graph-sha1', 'data'),
                   Input('dropdown-node-preferences', 'value'),
                   Input('dropdown-edge-preferences', 'value'),
                   Input('graph', 'tapNode')
                   ])
    def set_exploration_nodes(mode, explore_data, graph_sha1, node_list, edge_list, tapped_node):
        if mode == 'overview':
            return dash.no_update

        allowed_nodes = explore_data['nodes']

        # get graph
        sha1 = graph_sha1['graph_sha1']
        graph = commit_dict[sha1]
        new_graph = subgraph.subgraph(graph, node_list, edge_list)

        # if tapped node is not a leaf, dont update
        if tapped_node != None:
            target_id = tapped_node['data']['id']
            for n in new_graph.nodes:
                if n.get_name() == target_id:
                    # if all children are already in allowed_nodes, dont update
                    # since empty set is always a subset, this also prevents update
                    # for nodes with no children to add
                    children = set(
                        map(lambda n: n.get_name(), new_graph.successors(n)))
                    if children.issubset(set(allowed_nodes)):
                        raise PreventUpdate

        # determine if preset was changed to trigger this callback
        ctx = dash.callback_context
        preset_changed = False
        for event in ctx.triggered:
            prop_id = event['prop_id']
            if prop_id == 'dropdown-node-preferences.value' or prop_id == 'dropdown-edge-preferences.value':
                preset_changed = True
                break

        if preset_changed:
            allowed_nodes = []
            # only allow roots at first
            for n in new_graph.nodes:
                # if n is a root
                if new_graph.in_degree(n) == 0 and new_graph.degree(n) != 0:
                    allowed_nodes.append(n.get_name())
                    for direct_child in new_graph.successors(n):
                        allowed_nodes.append(direct_child.get_name())
        elif tapped_node != None:
            # add tapped node's children
            for n in new_graph.nodes:
                if n.get_name() == tapped_node['data']['id']:
                    for direct_child in new_graph.successors(n):
                        allowed_nodes.append(direct_child.get_name())
                    break

        return {'nodes': allowed_nodes}

    @app.callback(Output('graph', 'layout'),
                  [Input('dropdown-layout', 'value')], [State('graph-sha1', 'data'), State('dropdown-node-preferences', 'value'),
                                                        State('dropdown-edge-preferences', 'value')])
    def update_graph_layout(layout, graph_sha1, node_list, edge_list):
        # get graph
        sha1 = graph_sha1['graph_sha1']
        graph = commit_dict[sha1]
        new_graph = subgraph.subgraph(graph, node_list, edge_list)

        if layout == 'cose':
            return {'name': 'cose', 'animate': False, 'numIter': 500}
        elif layout == 'breadthfirst':
            roots = get_roots(new_graph)
            return {'name': 'breadthfirst', 'roots': roots}
        elif layout == 'concentric':
            return {'name': 'concentric', 'spacingFactor': 0.5}

        return {'name': layout}

    @app.callback([Output('dropdown-node-preferences', 'value'),
                   Output('dropdown-edge-preferences', 'value'),
                   Output('dropdown-layout', 'value'),
                   Output('dropdown-show-empty', 'value'),
                   Output('description-card', 'children')],
                  [Input('dropdown-presets', 'value')])
    def preset_graph(preset):
        if preset == 'custom':
            return (dash.no_update, dash.no_update, dash.no_update, dash.no_update, [dcc.Markdown(PRESETS.get('custom')[4])])
        nodes, edges, layout, show_empty, description = PRESETS.get(
            preset, 'invalid preset')
        return (nodes, edges, layout, show_empty, [dcc.Markdown(description)])

    @app.callback(Output('preferences-container', 'hidden'),
                  [Input('dropdown-presets', 'value')])
    def unhide_preferences(preset):
        return (False if preset == 'custom' else True)

    @app.callback(Output('graph', 'elements'),
                  [Input('dropdown-node-preferences', 'value'),
                  Input('dropdown-edge-preferences', 'value'),
                  Input('dropdown-show-empty', 'value'),
                  Input('graph-sha1', 'data'),
                  Input('exploration-nodes', 'data'),
                  Input('radio-mode', 'value')
                   ])
    def update_graph_data(node_list, edge_list, show_empty, graph_sha1, explore_nodes, mode):
        # get graph
        sha1 = graph_sha1['graph_sha1']
        graph = commit_dict[sha1]
        new_graph = subgraph.subgraph(graph, node_list, edge_list)

        removes = []
        for n in new_graph.nodes:
            if show_empty == "No" and new_graph.degree(n) == 0:
                removes.append(n)

        # remove unexplored nodes if in explore mode
        if mode == 'exploration':
            allowed_nodes = explore_nodes['nodes']
            for n in new_graph.nodes:
                if n.get_name() not in allowed_nodes:
                    removes.append(n)

        new_graph.remove_nodes_from(removes)

        return get_graph_data(new_graph)

    def color_nodes(elements, stylesheet, tapped_node, following_color, follower_color):
        """
        Highlights ``tapped_node`` as well as its parent and children nodes. 
        Prerequisites: ``tapped_node`` cannot be ``None``.
        """
        node_id = tapped_node['data']['id']
        for edge in elements:
            try:
                if edge['data']['source'] == node_id:
                    stylesheet.append({
                        "selector": 'node[id = "{}"]'.format(edge['data']['target']),
                        "style": {
                            'background-color': following_color,
                            'opacity': 0.9,
                            "label": "data(label)"
                        }
                    })
                    stylesheet.append({
                        "selector": 'edge[source= "{}"]'.format(node_id),
                        "style": {
                            "mid-target-arrow-color": following_color,
                            "mid-target-arrow-shape": 'triangle-backcurve',
                            "line-color": following_color,
                            'opacity': 0.7,
                            'z-index': 5000,
                            'arrow-scale': 3
                        }
                    })

                if edge['data']['target'] == node_id:
                    stylesheet.append({
                        "selector": 'node[id = "{}"]'.format(edge['data']['source']),
                        "style": {
                            'background-color': follower_color,
                            'opacity': 0.9,
                            'z-index': 9999,
                            "label": "data(label)",
                        }
                    })
                    stylesheet.append({
                        "selector": 'edge[target= "{}"]'.format(node_id),
                        "style": {
                            "mid-target-arrow-color": follower_color,
                            "mid-target-arrow-shape": 'triangle-backcurve',
                            "line-color": follower_color,
                            'opacity': 0.7,
                            'z-index': 5000,
                            'arrow-scale': 3
                        }
                    })
            except KeyError:
                pass

    @app.callback([Output('graph', 'stylesheet'), Output('prev-node', 'data')],
                  [Input('graph', 'tapNode'),
                   Input('prev-node', 'data'),
                   Input('graph-sha1', 'data'),
                   Input('dropdown-node-preferences', 'value'),
                   Input('dropdown-edge-preferences', 'value'),
                   Input('input-follower-color', 'value'),
                   Input('input-following-color', 'value'),
                   Input('input-root-color', 'value')
                   ])
    def generate_stylesheet(tapped_node, prev_node_data, graph_data, node_list, edge_list, follower_color, following_color, root_color):
        # always color the roots
        stylesheet = [
            {
                'selector': 'edge',
                'style': {
                    'opacity': 0.5,
                    "curve-style": "bezier",
                }}
        ]
        sha1 = graph_data['graph_sha1']
        graph = commit_dict[sha1]
        new_graph = subgraph.subgraph(graph, node_list, edge_list)
        for n in new_graph.nodes:
            shape = NODE_SHAPES.get(type(n))
            size = len(list(new_graph.successors(n)))*2 + 20

            if new_graph.in_degree(n) == 0 and new_graph.degree(n) != 0:
                stylesheet.append({
                    "selector": 'node[id = "{}"]'.format(n.get_name()),
                    "style": {
                        'background-color': root_color,
                        'opacity': 0.9,
                        'label': 'data(label)',
                        'shape': shape,
                        'width': size,
                        'height': size
                    }
                })
            else:
                stylesheet.append({
                    "selector": 'node[id = "{}"]'.format(n.get_name()),
                    "style": {'shape': shape,
                                'width': size,
                                'height': size
                              }
                })

        for u, v, d in new_graph.edges(data=True):
            line_style = EDGE_STYLE.get(type(d['edge']))

            stylesheet.append({
                "selector": 'edge[id = "{}"]'.format(f"{str(type(d['edge']))}{d['edge'].__hash__}"),
                "style": {'line-style': line_style}
            })

        if tapped_node is None or tapped_node['data']['id'] == prev_node_data['prev_node']:
            prev_node_data.update({'prev_node': None})
            return (stylesheet, prev_node_data)

        # if node selected, color the graph to highlight this
        stylesheet += [{
            "selector": 'node',
            'style': {
                'opacity': 0.3,
            }
        }, {
            'selector': 'edge',
            'style': {
                'opacity': 0.2,
                "curve-style": "bezier",
            }
        }, {
            "selector": 'node[id = "{}"]'.format(tapped_node['data']['id']),
            "style": {
                'background-color': '#B10DC9',
                "opacity": 1,

                "label": "data(label)",
                "color": "#B10DC9",
                "text-opacity": 1,
                "font-size": 16,
                'z-index': 9999
            }
        }]

        new_elements = get_graph_data(new_graph)
        color_nodes(new_elements, stylesheet, tapped_node,
                    following_color, follower_color)

        prev_node_data.update({'prev_node': tapped_node['data']['id']})
        return (stylesheet, prev_node_data)

    @app.callback(Output('graph', 'tapNode'),
                  Input('dropdown-presets', 'value'),
                  Input('graph-sha1', 'data'))
    def reset_selection(preset, data):
        return None

    @app.callback([Output("commit-chart", "figure"),
                   Output("commit-chart-container", "hidden"),
                   Output('date-picked', 'children'),
                   Output('commit-chart-options', 'hidden')],
                  [Input("show-commits", "value"),
                   Input('commit-chart', 'figure'),
                   Input('dropdown-presets', 'value'),
                   Input('slider-date-picker', 'value'),
                   Input('dropdown-matrix-type', 'value'),
                   Input('dropdown-spectrum-type', 'value')
                   ])
    def update_line_chart(show_commits, current_fig, preset, range, m_type, s_type):
        if not show_commits:
            return (current_fig, True, '', True)
        else:
            min_index, max_index = range
            dates = list(metrics.get_dates(commits).values())

            # commits are in reverse chronological order
            min_date = dates[(-1 - min_index) % len(dates)]
            max_date = dates[(-1 - max_index) % len(dates)]

            # only give commits within the date range
            new_commits = [commit for commit in commits
                           if min_date <= commit.committed_datetime <= max_date]

            msg = f"You have selected {min_date.strftime('%x')} to {max_date.strftime('%x')}."

            x, y = get_commit_data(
                new_commits, commit_dict, preset, matrix_type=m_type, spectrum_type=s_type)
            df = pd.DataFrame(
                {'Commit Date': x, 'Graph Energy': y})

            fig = px.scatter(df, x="Commit Date",
                             y="Graph Energy",)

            return (fig, False, msg, False)

    @app.callback([Output('commit-chooser', 'hidden'),
                   Output('commit-picked', 'children'),
                   Output('graph-sha1', 'data')],
                  [Input("choose-commit", "value"),
                   Input('dropdown-commit-picker', 'value'),
                   Input('graph-sha1', 'data')])
    def update_commit_selection(choose_commit, sha1, data):
        if not choose_commit:
            return (True, '', data)
        else:
            msg = f'You have selected commit with SHA1:\n{sha1}'
            data.update({'graph_sha1': sha1})

            return (False, msg, data)

    # this url might not be universal
    web.open("http://127.0.0.1:8050/")
    if DEBUG_MODE:
        app.run_server(debug=True)
    else:
        app.run_server(debug=True, use_reloader=False)
