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


const PRESETS = {
  'file directory': [
    ['FolderNode', 'FileNode'], ['DirectoryEdge'], 'tree', true,
    "The file organization of the repo. Nodes are either folders or Python files. " +
    "A directed edge from **u** to **v** represents '**u** is the parent folder of **v**.'"],
  'class inheritance': [
    ["ClassNode"], ["InheritanceNode"], 'force directed', false,
    "The classes that inherit from another class defined within the repo. Nodes are Python classes. " +
    "A directed edge from **u** to **v** represents '**u** is a parent class for **v**.'"],
  'function dependency': [
    ["FileNode", "ClassNode", "FunctionNode"], ["Function Call"], 'circle', false,
    "The function calls within the repo. Nodes represent a Python file, function, or class. " +
    "A directed edge from **u** to **v**  represents '**u** is called by **v**.'"],
  'import dependency': [
    ["FileNode", "FolderNode"], ["ImportEdge"], 'concentric', false,
    "The imports of each Python file. Nodes are Python files or folders (as Python packages). " +
    "A directed edge from **u** to **v**  represents '**u** is imported by **v**.'"],
  'broad definitions': [
    ["File", "Class", "Function"], ["Definition"], 'cose', false,
    "The organization of Python class and function definitions. Nodes are files, functions, or classes. " +
    "A directed edge from **u** to **v**  represents '**u** defines **v**.'"],
  'granular definitions': [
    ["File", "Class", "Function", "Variable", "Lambda", "If", "For", "While", "Try"], ["Definition"], 'cose', false,
    "The variables, lambda expressions, if-statements, for loops, while loops, and try-statements defined within Python files." +
    "A directed edge from **u** to **v**  represents '**u** defines **v**.'"],
  'all': [
    ["File", "Folder", "Class", "Function"], ["Inheritance", "Directory", "Function Call", "Import", "Definition"], 'concentric', false,
    "Every type of node and edge displayed at once."],
  'custom': [
    [], [], 'concentric', true, "Choose the Node and Edge types to include. "]
}

/* TESTS */
// const fs = require('fs')
// const path = require('path')

// j_string = fs.readFileSync('./module_data/39dc1c46adcb3b8500b4e232fbe0efc41e65f0e1.json')
// g = JSON.parse(j_string)

// console.log(subgraph(g, ["FileNode"], ["DirectoryEdge"]))

