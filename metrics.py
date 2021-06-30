"""
This module analyzes the commit-graph dictionary created by the main module.
"""
import subgraph
import visual
from git import Repo, Git
from git.objects.commit import Commit


def unique_subgraphs(commit_dict, preset):
    """
    Associates a unique graph with the SHA1 of the commit (or commits) it represents.

    :param commit_dict: the dictionary mapping SHA1 to the graph created by the ``parsing`` module.
    :param type: {str : networkx.MultiDiGraph} 

    :param preset: the subgraph to create for each graph in ``commit_dict``
    :type preset: str

    :returns: a list of tuples that associates a unique graph and the sha1's of the commits it represents 
    :rtype: (networkx.MultiDiGraph, str list) list

    If commit with SHA1 'd6944b9491b294c02fd0c0d9aff3ae56fa069644' and commit with
    SHA1 'b3b0669f716a7b3ed6cd573b57f3f8e12bcd495a' have the same files and folders
    (and thus the same graph when parsed), then:

    >>> unique_subgraphs(commit_dict, "file directory")
    [(<networkx.MultiDiGraph object>, ['d6944b9491b294c02fd0c0d9aff3ae56fa069644', 'b3b0669f716a7b3ed6cd573b57f3f8e12bcd495a']
    """
    graph_commit_pairs = []

    for sha1 in commit_dict:
        graph = commit_dict[sha1]
        new_graph = subgraph.subgraph(graph, *visual.PRESETS[preset][0:2])
        i = 0
        graph_found = False
        
        while (i < len(graph_commit_pairs) and not graph_found):
            if len(graph_commit_pairs) != 0:
                g, c = graph_commit_pairs[i]

                # if graph already in tuple list
                if set(g.nodes) == set(new_graph.nodes) and set(g.edges) == set(new_graph.edges):
                    # add current sha1 to list of sha1 associated with this graph
                    graph_commit_pairs[i][1].append(sha1)
                    graph_found = True

            i += 1

        if not graph_found:
            graph_commit_pairs.append((new_graph, [sha1]))

    return graph_commit_pairs


def get_dates(commits: list[Commit]):
    """
    Gathers the dates of when ``commits`` were made.

    :param commits: the list of commits to analyze.
    :type commits: list[Commit]

    :returns:a dictionary mapping the sha1 of a commit to its commit datetime.
    :rtype: {str : datetime}

    For two commits published one day apart:
    >>> get_dates([commit1, commit2])
    {'d6944b9491b294c02fd0c0d9aff3ae56fa069644': datetime(2021, 5, 24, 22, 48, 38), 'b3b0669f716a7b3ed6cd573b57f3f8e12bcd495a': datetime(2021, 5, 25, 15, 3, 14}
    """
    commit_times = {}

    for commit in commits:
        commit_times.update({commit.hexsha: commit.committed_datetime})

    return commit_times
