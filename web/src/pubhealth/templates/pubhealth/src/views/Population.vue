<script setup lang="ts">
// import type { onMounted } from 'vue';
import {onMounted, ref} from 'vue'
//@ts-ignore
import * as d3 from "d3";
import {Library} from '@observablehq/stdlib'
import { io, Socket } from "socket.io-client";

let domain = `localhost`
let port = 9001

interface ClientToServer {
    query: (query: string, name: string) => string
    setup: (query: string) => string
    neighbors: (low_income_perc: number, high_income_perc: number) => any
    rural_urban_result: (level: string) => any
    linear_regression: (pairs: [number, number][]) => any
}

interface ServerToClient {
    data: (data: {data: any[], end: boolean, name: string}) => any
    setup: (data: {data: any[]}) => any 
    neighbors_result: (data: {pnp: any[], rnr: any[], pnr: any[], rnp: any[]}) => any
    rural_urban_result: (data: {name: string, data: any[]}) => any
    linear_regression_result: (data: {coeff_of_determination: number}) => any
}

class County {
  fips: number
  health_metrics: Map<string, value>
  rucc: number

  constructor(fips: number) {
    this.fips = fips
    this.health_metrics = new Map()
    this.rucc = 0
  }

  setRUCC(rucc: number) {
    this.rucc = rucc
  }

  setHealthMetric(name: string, value: number) {
    this.health_metrics.set(name, value)
  }

}

class CountyData {
  data: Map<number, County>
  clusterScaleNumeric: any
  clusterScaleColor: any
  clusterLegend: [number, number, string][]

  sizeScale: any
  sizeLegend: [number, number, string][]
  sizeMetric: string

  constructor() {
    this.data = new Map()
    this.clusterLegend = []
    this.sizeLegend = []
  }

  addCounty(fips: number) {
    this.data.set(fips, new County(fips))
  }

  addRUCC(fips: number, rucc: number) {
    if(!this.data.has(fips)) {
      throw Error(`No such FIPS: ${fips}`)
    }
    this.data.get(fips)?.setRUCC(rucc)
  }

  addManyRUCC(a: [number, number][]) {
    a.forEach(([fips, rucc]) => {
      this.addRUCC(fips, rucc)
    })
  }

  addHealthMetric(fips: number, name: string, value: number) {
    if(!this.data.has(fips)) {
      this.addCounty(fips)
    }
    let county = this.data.get(fips)
    county?.setHealthMetric(name, value)
  }

  addManyHealthMetric(a: [number, string, number][]) {
    a.forEach(([fips, name, value]) => {
      this.addHealthMetric(fips, name, value)
    })
  }
  
  uniformSample(): County[] {
    let rucc_count = new Map<number, number>()
    var total_counties = 0
    
    // County all counties
    Array.from(this.data.values())
    .map((county: County) => {
      let rucc = county.rucc
      if(!rucc_count.has(rucc)) {
        rucc_count.set(rucc, 0)
      }
      // as number ot satisfy typescript compiler
      let updated = (rucc_count.get(rucc) as number) +1
      rucc_count.set(rucc, updated)
      total_counties++
    })
    
    
    let proportions = new Map(Array.from(rucc_count.entries())
    .map(([rucc, count]) => {
      return [rucc, count/total_counties]
    }))
    return Array.from(this.data.values())
    .filter((county: County) => {
      let r = Math.random()
      
      //@ts-ignore
      if(r <= proportions.get(county.rucc)) {
        return true
      }
    })
  }

  setClusterScale(scale: any, color: any, legend?: any) {
    this.clusterScaleNumeric = scale
    this.clusterScaleColor = color
    if(!legend)
      this.clusterLegend = getBuckets(scale.domain(), scale)
    else
      this.clusterLegend = legend
  }

  setSizeScale(scale: any, metric_name: string, legend?: any) {
    this.sizeScale = scale
    if(legend)
      this.sizeLegend = legend
    else
      this.sizeLegend = getBuckets(scale.domain(), scale)
    this.sizeLegend.unshift([0, 0, `${DEFAULT_SIZE}`])      
    this.sizeMetric = metric_name
  }

}

let county_data = ref(new CountyData())

//@ts-ignore
let socket: Ref<Socket<ServerToClient, ClientToServer>> = ref(io(`ws://${domain}:${port}/`, {transports: ['websocket', 'polling']}));


function getBuckets(incomes: number[], colorScheme: CallableFunction): [number, number, string][] {
    let buckets = []

    let start = incomes[0]
    
    for(var i = 1; i < incomes.length; i++) {
        if(colorScheme(incomes[i]) !== colorScheme(incomes[i-1])) {
            buckets.push([start, incomes[i-1], colorScheme(incomes[i-1])])
            start = incomes[i]
        }
    }
    if(incomes[i-1] !== undefined)
        buckets.push([start, incomes[i-1], colorScheme(incomes[i-1])])
    return buckets
}

const library = new Library()
const DOM = library.DOM

let maxRadius = 10
let numClusters = 10
let clusterPadding = 20
let padding = 5
let height = 500
let width = 750
let radius = d3.scaleLinear().domain([0, 10]).range([3, maxRadius])
// let color = d3.scaleOrdinal(d3.schemeCategory10)

let datapoints = ref([])
let nodes = ref([])
let clusters = ref({})

const DEFAULT_SIZE = 3

let nodesFn = () => {
  const noClusterNodes = datapoints.value.map((c: County) => {
    let health_value: number = c.health_metrics.get('All teeth lost among adults aged >=65 years')
    
    return {
      id: c.rucc,
      cluster: county_data.value.clusterScaleNumeric(c.rucc),
      radius: county_data.value.sizeScale(health_value) || DEFAULT_SIZE,
      x: Math.random() * width,
      y: Math.random() * height
    };
    
  });

  return noClusterNodes;
}



let clustersFn = () => {
  const clusterMap: any = {};
  nodes.value.forEach(n => {
    if (!clusterMap[n.cluster] || (n.radius > clusterMap[n.cluster].radius)) 
        clusterMap[n.cluster] = n;

  });
  return clusterMap;
}



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

let cluster = (alpha: any) => {
  // https://bl.ocks.org/mbostock/7881887
  return function (d) {
    const cluster = clusters.value[d.cluster];
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
      clusters.value[d.cluster] = cluster
    }
  };
}

let collide = (alpha: any) => {
  // https://bl.ocks.org/mbostock/7882658
  const quadtree = d3.quadtree()
    .x(function (d) { return d.x; })
    .y(function (d) { return d.y; })
    .extent([[0, 0], [width, height]])
    .addAll(nodes.value);
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

let size_metric = ref('All teeth lost among adults aged >=65 years')

function createPlot() {
  

  
  
  // this only has one since I only requested 1 metric from the DB
  // we'll update this later to accept a user-selected metric

  // scaleQuantize will accept all the values from the health metrics we have and bucket them into 3 buckets, since 
  // we gave it a 3 element array.
  // Later when we pass in a health metric value (like 35.656), then this scale will give us back 6, 12, or 20.
  // An alternative syntax that makes it look more like a function from math...

  // So now we have the domain and range for this "function"/scale
  // console.log(
  //   Array.from(county_data.value.data.values())
  //   .filter((c: County) => c.health_metrics.get('All teeth lost among adults aged >=65 years'))
  //   .map((c: County) => c.health_metrics.get('All teeth lost among adults aged >=65 years') )
  //   .sort((a, b) => a-b)
  // )
  let total_data = Array.from(county_data.value.data.values())
  .filter((c: County) => c.health_metrics.get(size_metric.value))
  .map((c: County) => c.health_metrics.get(size_metric.value) )
  .sort((a, b) => a-b)

  let sizeScale = d3.scaleQuantize()
  .domain([total_data.at(0), total_data.at(-1)])
  .range([8, 13, 24])

  let sizeLegend = getBuckets(total_data, sizeScale)
  

  let color = (i) => {
    let choices = ["red", "orange", "yellow", "limegreen", "green", "cyan", "blue", "darkblue", "purple"]
    if((i-1) < 0)
      return choices[0]
    if( (i-1) > 8)
      return choices[8]
    return choices[(i-1)]
  }
  let scale = Math.floor
  let legend = getBuckets(datapoints.value.map((c: County) => c.rucc).sort((a, b) => a-b), color)
  
  county_data.value.setClusterScale(scale, color, legend)
  county_data.value.setSizeScale(sizeScale, size_metric, sizeLegend)

  window.county_data = county_data

  nodes.value = nodesFn()
  clusters.value = clustersFn()
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
            .nodes(nodes.value, (d) => d.id)
            .on("tick", ticked)
            .restart();

        let showCells = true;
        const hullG = svg.append("g").attr("class", "hulls");

        const node = svg
            .append("g")
            .attr("class", "nodes")
            .selectAll("circle")
            .data(nodes.value, (d) => d.id)
            .enter()
            .append("circle")
            .attr("class", (d) => `cluster${d.cluster}`)
            .attr("r", (d) => d.radius)
            .attr("fill", (d) => county_data.value.clusterScaleColor(+d.cluster))
            .attr("stroke", "black")
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
            Object.keys(clusters.value)
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
            .attr("fill", (d) => county_data.value.clusterScaleColor(+d.cluster))
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
            ? nodes.value
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
            .attr("fill", (d) => county_data.value.clusterScaleColor(d.cluster));

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
    if(document.getElementById("plot")?.childElementCount === 0) {
      document.getElementById("plot")?.append(chart())
    }
    
}


onMounted(() => {
    let rows = 0
    socket.value.on('data', (data) => {
      if(data['name'] == 'weighted_rucc') {
        data['data'].forEach((row) => {
          datapoints.value.push(row)
        })
        // createPlot()
      }
      if(data['name'] == 'county_rucc') {
        
        data['data'].forEach((row) => {
          let [fips, rucc] = row
          county_data.value.addCounty(fips)
          county_data.value.addRUCC(fips, rucc)
        })
        datapoints.value = county_data.value.uniformSample()
        // createPlot()
        
      } 
      if(data['name'] == 'county_health') {
        data['data'].forEach((row) => {
          let [fips, measure, data_value] = row
          county_data.value.addHealthMetric(fips, measure, data_value)
        })

        // create the plot once we process the last batch of data for this query
        rows += data['data'].length
        if(rows === 228770) {
          datapoints.value = county_data.value.uniformSample()
          createPlot()
        }
        
      }
    })

    // let state_rucc_query = "SELECT STATE_FIPS, WEIGHTED_RUCC FROM cps_00004.pop_weighted_rucc"
    let county_rucc_query = "SELECT FIPS, RUCC FROM cps_00004.rural_urban_codes"
    let county_disease_prevalance = `
    SELECT COUNTY_FIPS, MEASURE, DATA_VALUE 
    FROM cps_00004.places_county
    `
    // socket.value.emit('query', state_rucc_query, 'weighted_rucc')
    socket.value.emit('query', county_rucc_query, 'county_rucc')
    socket.value.emit('query', county_disease_prevalance, 'county_health')

    
    

})
</script>
<template>
    <div class="row">
      <div id="plot" class="col-md-6"></div>
      <div id="" class="col-md-3">
        <div v-for="elem in county_data.clusterLegend">
          <div>
            <span class="d-inline-block">
                <div class="d-flex" :style="{backgroundColor: elem[2], height: '1em', width: '1em'}"></div>
            </span>
            
            <span class="d-inline mx-3">{{ elem[0] }}</span>
            <span v-if="elem[0] === 1">(Most densely populated)</span>
            <span v-if="elem[0] === 9">(Least densely populated)</span>
          </div>
        </div>
        <div id="secondary" class="my-3 row">
          <div>
            {{ county_data.sizeMetric }}
          </div>
          <div v-for="elem in county_data.sizeLegend" class="align-middle align-text-middle my-2">
            
            <span class="d-inline-flex align-middle align-text-middle col-md-2 justify-content-center">
                <div class="d-flex" :style="{backgroundColor: `white`, height: `${elem[2]*2}px`, width: `${elem[2]*2}px`, borderStyle: `solid`, borderWidth: `thin`, borderRadius: `1000px`}"></div>
            </span>
            <span v-if="elem[0] === 0">
              <span class="col-md-1 d-inline mx-3 align-middle align-text-middle">N/A</span>
            </span>
            <span v-else class="col-md-1">
              <span class="d-inline mx-3 align-middle align-text-middle">{{ elem[0] }}</span>
              <span class="d-inline align-middle align-text-middle"> - </span>
              <span class="d-inline mx-3 align-middle align-text-middle">{{ elem[1] }}</span>
            </span>
          </div>
        </div>
      </div>
      
    </div>
</template>