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
    'definitions': (["File", "Class", "Function"], ["Definition"], 'cose', 'No',
                    "The organization of Python class and function definitions. Nodes are files, functions, or classes. " +
                    "A directed edge from **u** to **v**  represents '**u** defines **v**.'"),
    'all': (["File", "Folder", "Class", "Function"], ["Inheritance", "Directory", "Function Call", "Import", "Definition"], 'concentric', 'No',
            "Every type of node and edge displayed at once."),
    'custom': ([], [], 'concentric', 'Yes', "Choose the Node and Edge types to include. ")
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
            'source':  u.get_name(),
            'target': v.get_name()}
    } for u, v, d in graph.edges]

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
        drc.Card(title='Preset Description',
                 id='description-card',
                 children=[],
                 style={'padding': 5,
                        'margin': 5, })
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
            dcc.Store(id='graph-sha1', data={'graph_sha1': commits[0].hexsha})
        ]),
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
                                  style={'width': '100%', 'height': '500px'},
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

    @app.callback(Output('graph', 'layout'),
                  [Input('dropdown-layout', 'value')])
    def update_graph_layout(layout):
        if layout == 'cose':
            # positions will be put in by networkx algorithm
            return {'name': 'preset'}
        return {'name': layout}

    @app.callback([Output('dropdown-node-preferences', 'value'),
                   Output('dropdown-edge-preferences', 'value'),
                   Output('dropdown-layout', 'value'),
                   Output('dropdown-show-empty', 'value'),
                   Output('description-card', 'children')],
                  [Input('dropdown-presets', 'value')])
    def preset_graph(preset):
        if preset == 'custom':
            raise PreventUpdate
        nodes, edges, layout, show_empty, description = PRESETS.get(
            preset, 'invalid preset')
        return (nodes, edges, layout, show_empty, [dcc.Markdown(description)])

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
                  Input('graph-sha1', 'data'),
                  Input('graph', 'layout'),
                   ])
    def update_graph_data(node_list, edge_list, show_empty, data, layout):
        sha1 = data['graph_sha1']
        graph = commit_dict[sha1]
        new_graph = subgraph.subgraph(graph, node_list, edge_list)

        removes = []
        for n in new_graph.nodes:
            if show_empty == "No" and new_graph.degree(n) == 0:
                removes.append(n)

        new_graph.remove_nodes_from(removes)

        if layout['name'] == 'preset':
            # sha1 + _nodes.sort + _edges.sort + _show_empty
            node_list.sort()
            edge_list.sort()
            key = f"{sha1}_{str(node_list)}_{str(edge_list)}_{show_empty}"
            if rs.hexists(repo_name, key):
                # get previously calculated positions
                pos = pickle.loads(rs.hget(repo_name, key))
            else:
                # does not have grouping of trees like cose, but still works.
                # has optional args that can be tweaked to give better results.
                print("Running physics simulation...", end="", flush=True)
                pos = nx.spring_layout(new_graph, scale=500, iterations=500)
                rs.hset(repo_name, key, pickle.dumps(pos))
                print("Done.")
            return get_graph_data(new_graph, positions=pos)
        else:
            return get_graph_data(new_graph)

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
    def generate_stylesheet(node, prev_node_data, graph_data, node_list, edge_list, follower_color, following_color, root_color):
        # always color the roots
        stylesheet = [
            {
                "selector": 'edge',
                'style': {
                    "curve-style": "bezier",
                    "opacity": 0.65
                }
            },
        ]
        sha1 = graph_data['graph_sha1']
        graph = commit_dict[sha1]
        new_graph = subgraph.subgraph(graph, node_list, edge_list)
        for n in new_graph.nodes:
            if new_graph.in_degree(n) == 0 and new_graph.degree(n) != 0:
                stylesheet.append({
                    "selector": 'node[id = "{}"]'.format(n.get_name()),
                    "style": {
                        'background-color': root_color,
                        'opacity': 0.9,
                        "label": "data(label)",
                    }
                })
        if node is None or node['data']['id'] == prev_node_data['prev_node']:
            prev_node_data.update({'prev_node': None})
            return (stylesheet, prev_node_data)

        # if node selected, color the graph to highlight this
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

        prev_node_data.update({'prev_node': node['data']['id']})
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
