<script setup lang="ts">
// import type { onMounted } from 'vue';
import {onMounted} from 'vue'
//@ts-ignore
import * as d3 from "d3";
import {Library} from '@observablehq/stdlib'

const library = new Library()
const DOM = library.DOM

let maxRadius = 10
let numClusters = 10
let clusterPadding = 20
let padding = 5
let height = 500
let width = 750
let radius = d3.scaleLinear().domain([0, 10]).range([3, maxRadius])
let color = d3.scaleOrdinal(d3.schemeCategory10)

let nodesFn = () => {
  const noClusterNodes = d3.range(50).map((idx) => {
    return {
      id: idx,
      cluster: 0,
      radius: 3,
      x: Math.random() * width,
      y: Math.random() * height
    };
  });
  const clusterNodes = d3.range(150).map((idx) => {
    const i = Math.floor(Math.random() * numClusters);
    const r = Math.sqrt((i + 1) / numClusters * -Math.log(Math.random())) * maxRadius;
    return {
      id: idx + 50,
      cluster: i,
      radius: radius(r),
      x: Math.random() * width,
      y: Math.random() * height
      // x: Math.cos(i / numClusters * 2 * Math.PI) * 200 + width / 2 + Math.random(),
      // y: Math.sin(i / numClusters * 2 * Math.PI) * 200 + height / 2 + Math.random()
    };
  });
  return noClusterNodes.concat(clusterNodes);
}

let nodes = nodesFn()

let clustersFn = () => {
  const clusterMap: any = {};
  nodes.forEach(n => {
    if (!clusterMap[n.cluster] || (n.radius > clusterMap[n.cluster].radius)) 
        clusterMap[n.cluster] = n;

  });
  return clusterMap;
}

let clusters = clustersFn()

let hullPoints = (data: any) => {
  let pointArr: any[] = [];
  const padding = 2.5;
  data.each(d => {
    const pad = d.radius + padding;
    pointArr = pointArr.concat([
      [d.x - pad, d.y - pad],
      [d.x - pad, d.y + pad],
      [d.x + pad, d.y - pad],
      [d.x + pad, d.y + pad]
    ]);
  });
  return pointArr;
}

let cluster = (alpha) => {
  // https://bl.ocks.org/mbostock/7881887
  return function (d) {
    const cluster = clusters[d.cluster];
    if (cluster === d || d.cluster == 0) return;
    let x = d.x - cluster.x,
        y = d.y - cluster.y,
        l = Math.sqrt(x * x + y * y),
        r = d.radius + cluster.radius + 3;
    if (l != r) {
      l = (l - r) / l * alpha;
      d.x -= x *= l;
      d.y -= y *= l;
      cluster.x += x;
      cluster.y += y;
    }
  };
}

let collide = (alpha) => {
  // https://bl.ocks.org/mbostock/7882658
  const quadtree = d3.quadtree()
    .x(function (d) { return d.x; })
    .y(function (d) { return d.y; })
    .extent([[0, 0], [width, height]])
    .addAll(nodes);
  return function (d) {
    let r = d.radius + (maxRadius * 8) + Math.max(padding, clusterPadding),
        nx1 = d.x - r,
        nx2 = d.x + r,
        ny1 = d.y - r,
        ny2 = d.y + r;
    quadtree.visit(function (quad, x1, y1, x2, y2) {
      let data = quad.data;
      if (data && data !== d) {
        let x = d.x - data.x,
            y = d.y - data.y,
            l = Math.sqrt(x * x + y * y),
            r = d.radius + data.radius + (d.cluster == data.cluster ? padding : clusterPadding);
        if (l < r) {
          l = (l - r) / l * alpha;
          d.x -= x *= l;
          d.y -= y *= l;
          data.x += x;
          data.y += y;
        }
      }
      return x1 > nx2 || x2 < nx1 || y1 > ny2 || y2 < ny1;
    });
  };
}
onMounted(() => {
    let chart = () => {
        const svg = d3.select(DOM.svg(width, height)).attr("id", "chart");
        const line = d3.line().curve(d3.curveBasisClosed);
        const simulation = d3
            .forceSimulation()
            .alpha(0.3)
            .force(
            "center",
            d3
                .forceCenter()
                .x(width / 2)
                .y(height / 2)
            )
            .force(
            "collide",
            d3.forceCollide((d) => d.radius + padding)
            )
            .nodes(nodes, (d) => d.id)
            .on("tick", ticked)
            .restart();

        let showCells = true;
        const hullG = svg.append("g").attr("class", "hulls");

        const node = svg
            .append("g")
            .attr("class", "nodes")
            .selectAll("circle")
            .data(nodes, (d) => d.id)
            .enter()
            .append("circle")
            .attr("class", (d) => `cluster${d.cluster}`)
            .attr("r", (d) => d.radius)
            .attr("fill", (d) => color(+d.cluster))
            .call(
            d3
            .drag()
            .on("start", dragstarted)
            .on("drag", dragged)
            .on("end", dragended)
            );

        const hulls = hullG
            .selectAll("path")
            .data(
            Object.keys(clusters)
                .map((c) => {
                return {
                    cluster: c,
                    nodes: node.filter((d) => d.cluster == c)
                };
                })
                .filter((d) => d.cluster != 0),
            (d) => d.cluster
            )
            .enter()
            .append("path")
            .attr("d", (d) => line(d3.polygonHull(hullPoints(d.nodes))))
            .attr("fill", (d) => color(+d.cluster))
            .attr("opacity", 0.4);

        function ticked() {
            node
            .each(cluster(0.2))
            .each(collide(0.2))
            .attr(
                "cx",
                (d) => (d.x = Math.max(d.radius, Math.min(width - d.radius, d.x)))
            )
            .attr(
                "cy",
                (d) => (d.y = Math.max(d.radius, Math.min(height - d.radius, d.y)))
            );

            hulls.attr("d", (d) => line(d3.polygonHull(hullPoints(d.nodes))));
        }

        d3.select("#updateButton").on("click", () => {
            showCells = !showCells;
            const useNodes = showCells
            ? nodes
            : nodes.map((d) => ({ ...d, radius: 3, cluster: 0 }));

            simulation
            .force(
                "collide",
                d3.forceCollide((d) => d.radius + padding)
            )
            .nodes(useNodes);
            simulation.alpha(0.1).restart();

            node
            .data(useNodes, (d) => d.id)
            .transition()
            .duration(1000)
            .attr("class", (d) => `cluster${d.cluster}`)
            .attr("r", (d) => d.radius)
            .attr("fill", (d) => color(d.cluster));

            hulls
            .transition()
            .duration(1000)
            .attr("opacity", showCells ? 0.4 : 0);
        });

        function dragstarted(event, d) {
            if (!event.active) simulation.alphaTarget(0.1).restart();
            d.fx = d.x;
            d.fy = d.y;
        }

        function dragged(event, d) {
            d.fx = event.x;
            d.fy = event.y;
        }

        function dragended(event, d) {
            if (!event.active) simulation.alphaTarget(0);
            d.fx = null;
            d.fy = null;
        }

        return svg.node();
    }
    document.getElementById("plot")?.append(chart())

})
</script>
<template>
    <div id="plot"></div>
</template>