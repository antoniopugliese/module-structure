const svg = d3.select("#graph-display")
width = +svg.attr("width"),
  height = +svg.attr("height");

const g = svg.append("g")
  .attr("cursor", "grab");

const color = d3.scaleOrdinal(d3.schemeCategory20);

const simulation = d3.forceSimulation()
  .force("link", d3.forceLink().id((d) => { return d.id; }))
  .force("charge", d3.forceManyBody())
  .force("center", d3.forceCenter(width / 2, height / 2));

d3.json("module_data/39dc1c46adcb3b8500b4e232fbe0efc41e65f0e1.json", (error, graph) => {
  if (error) throw error;

  let link = svg.append("g")
    .attr("class", "links")
    .selectAll("line")
    .data(graph.links)
    .enter().append("line")
    .attr("stroke-width", (d) => { return Math.sqrt(d.value); });

  let node = svg.append("g")
    .attr("class", "nodes")
    .selectAll("circle")
    .data(graph.nodes)
    .enter().append("circle")
    .attr("r", 5)
    .attr("fill", (d) => { return color(d.group); })
    .attr("cursor", "grab")
    .call(d3.drag()
      .on("start", dragstarted)
      .on("drag", dragged)
      .on("end", dragended))
    .call(d3.zoom().on("zoom", () => {
      svg.attr("transform", d3.event.transform)
    }))
    ;


  node.append("title")
    .text((d) => { return d.id; });

  simulation
    .nodes(graph.nodes)
    .on("tick", ticked);

  simulation.force("link")
    .links(graph.links);

  function ticked() {
    link
      .attr("x1", (d) => { return d.source.x; })
      .attr("y1", (d) => { return d.source.y; })
      .attr("x2", (d) => { return d.target.x; })
      .attr("y2", (d) => { return d.target.y; });

    node
      .attr("cx", (d) => { return d.x; })
      .attr("cy", (d) => { return d.y; });
  }
});

function dragstarted(d) {
  if (!d3.event.active) simulation.alphaTarget(0.3).restart();
  d.fx = d.x;
  d.fy = d.y;
}

function dragged(d) {
  d.fx = d3.event.x;
  d.fy = d3.event.y;
}

function dragended(d) {
  if (!d3.event.active) simulation.alphaTarget(0);
  d.fx = null;
  d.fy = null;
}

