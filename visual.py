import dash
import webbrowser as web
import networkx as nx
import dash_cytoscape as cyto
import os
import dash_html_components as html


def get_data(graph: nx.MultiDiGraph):
    """
   Transforms the node and edge data to a form that can be displayed.

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
    app = dash.Dash(__name__)

    app.layout = html.Div([
        cyto.Cytoscape(
            id='subgraph',
            layout={'name': 'concentric'},
            style={'width': '100%', 'height': '750px'},
            elements=get_data(graph)
        )
    ])
    # this url might not be universal
    web.open("http://127.0.0.1:8050/")
    app.run_server(debug=True, use_reloader=False)
