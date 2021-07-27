/** */
const get_node = (id, nodes) => {
  return nodes.find(elem => id === elem["id"])
}

/** */
const subgraph = (g, node_types, edge_types) => {
  // gather allowed nodes
  sub_nodes = []
  for (let n of g["nodes"]) {
    if (node_types.includes(n["type"])) {
      sub_nodes.push(n)
    }
  }

  // gather allowed edges
  sub_edges = []
  for (let e of g["edges"]) {
    s_node = get_node(e["source"], sub_nodes)
    t_node = get_node(e["target"], sub_nodes)

    // only include if both nodes allowed and edge type is allowed
    if (s_node !== undefined && t_node !== undefined &&
      edge_types.includes(e["type"])) {
      sub_edges.push(e)
    }
  }

  return { "nodes": sub_nodes, "edges": sub_edges }
}

/** */
const format_as_tree = (node, directory_data) => {
  let children = []
  for (let e of directory_data["edges"]) {
    if (e.source === node.id && e.target !== node.id) {
      t_node = get_node(e.target, directory_data["nodes"])
      children.push(format_as_tree(t_node, directory_data))
    }
  }

  return { "name": node.id, "children": children }
}

function changeGraph(graph, nodes, edges) {
  graph = subgraph(graph, nodes, edges)
  graph = format_as_tree({id: "snorkel", type: "FolderNode", graph})
  main.redefine("data", graph);
}

/* TESTS */
// const fs = require('fs')
// const path = require('path')

// j_string = fs.readFileSync('./module_data/39dc1c46adcb3b8500b4e232fbe0efc41e65f0e1.json')
// g = JSON.parse(j_string)

// console.log(subgraph(g, ["FileNode"], ["DirectoryEdge"]))

