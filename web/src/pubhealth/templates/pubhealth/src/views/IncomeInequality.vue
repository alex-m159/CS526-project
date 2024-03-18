<script setup lang="ts">
// import transformScale from '@turf/transform-scale'
// import interset from '@turf/intersect'
import { ref, onMounted, onUnmounted } from "vue";
import type { Ref } from "vue";
import { logger } from '../utils/logging';
import { io, Socket } from "socket.io-client";
//@ts-ignore
import * as d3 from "d3";

import * as topojson from "topojson"
// import * as turf from "@turf/turf"

import { legend } from "@/utils/bivariate";



interface ClientToServer {
    query: (query: string, name: string) => string
    setup: (query: string) => string
    neighbors: (low_income_perc: number, high_income_perc: number) => any
}

interface ServerToClient {
    data: (data: {data: any[], end: boolean, name: string}) => any
    setup: (data: {data: any[]}) => any 
    neighbors_result: (data: {pnp: any[], rnr: any[], pnr: any[], rnp: any[]}) => any
}

//@ts-ignore
let socket: Ref<Socket<ServerToClient, ClientToServer>> = ref(io(`ws://localhost:9001/`, {transports: ['websocket', 'polling']}));

let geojson = ref({})


const STATE_NAME = 0
const COUNTY_NAME = 1
const STATE_FIPS = 2
const COUNTY_FIPS = 3
const STATE_COUNTY_FIPS = 4
const GEO = 5

let prevScale = ref(1)
let currScale = ref(1)

let county_fill = ref(null)
let state_fill = ref(null)

let level = ref("states")
let cluster = ref("none")


let county_mesh = ref(null)
let state_mesh = ref(null)


let svg = ref(null)
let map_shapes = ref(null)
let gg = ref(null)
// let spikes = ref(null)
let width = document.documentElement.clientWidth*0.7
let height = document.documentElement.clientHeight*0.8
let viewBoxMinX = 0
let viewBoxWidth = 250
let viewBoxMinY = 0
let viewBoxHeight = 170 
let proj = d3.geoMercator()
                .scale(100)
                .center([-50, 60])

let path = d3.geoPath()

// Use to switch between AGI and Gini
let agi_scale = ref(false)

// Use to switch between State relative metrics and national 
// metrics for AGI and Gini
let state_scale = ref(false)

let scaleG = ref(null)
let legendG = ref(null)

let scaleAGI = ref(null)
let legendAGI = ref(null)

let scaleClusters = ref(null)
let legendClusters = ref(null)
let scaleLevel = ref("states")
let cluster_metric_agi = ref(false)


function pickData(choice?: string) {
    if(choice == "counties") {
        return county_fill.value
    } else if(choice == "states") {
        return state_fill.value
    }
    if(level.value === "counties") {
        return county_fill.value
    } else {
        return state_fill.value
    }
}

function pickMesh(choice?: string) {
    if(choice == "counties") {
        return county_mesh.value
    } else if(choice == "states") {
        return state_mesh.value
    }
    if(level.value == "counties") {
        return county_mesh.value
    } else if(level.value == "states"){
        return state_mesh.value
    }
    
}


function zoomed(event: any) {
    const {transform} = event;
    gg.value.attr("transform", transform);
    gg.value.attr("stroke-width", Math.min(1 / transform.k, 1));

    // spikes.value.attr("stroke-width", Math.min(1 / transform.k, 1));
    // spikes.value.attr("transform", transform);
}
let zoom = d3.zoom()
    .scaleExtent([0.1, 100])
    .on('zoom', zoomed)



function clicked(event, d) {
    const [[x0, y0], [x1, y1]] = path.bounds(d);
    event.stopPropagation();
    map_shapes.value.transition().style("fill", null);
    d3.select(this).transition().style("fill", "yellow");
    setTimeout(() => {
        d3.select(this).transition().duration(1000).style("fill", null);    
    }, 300)
    svg.value.transition().duration(750).call(
        zoom.transform,
        d3.zoomIdentity
            .translate(width / 2, height / 2)
            .scale(Math.min(8, 0.7 / Math.max((x1 - x0) / width, (y1 - y0) / height)))
            .translate(-(x0 + x1) / 2, -(y0 + y1) / 2),
        d3.pointer(event, svg.value.node())
    );
}



function reset() {
    map_shapes
    .value
    .transition()
    .style("fill", null);
    svg.value.transition().duration(750).call(
        zoom.transform,
        d3.zoomIdentity,
        d3.zoomTransform(svg.value.node()).invert([width / 2, height / 2])
    );

}

function reverse(a: readonly any[]) {
    let na = []
    for(var i = a.length-1; i >= 0; i--) {
        na.push(a[i])
    }
    return na
}

function getIncomeMetric(d) {
    if(agi_scale.value == true) {
        return d.properties.avg_agi
    } else {
        return d.properties.gini
    }
}

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
function getColor(d) {
    
    if(scaleG.value === null || scaleLevel.value !== level.value) {
        let gini_domain = pickData().map(v => v.properties.gini).sort((a, b) => a-b)

        scaleG.value = d3.scaleQuantile(pickData().map(v => v.properties.gini), (d3.schemeReds[9]))
        legendG.value = getBuckets(gini_domain, scaleG.value).sort((a, b) => a[0] - b[0])

        let agi_domain = pickData().map(v => v.properties.avg_agi).sort((a, b) => a-b)
        scaleAGI.value = d3.scaleQuantile(pickData().map(v => v.properties.avg_agi), d3.schemeBlues[9])
        legendAGI.value = getBuckets(agi_domain, scaleAGI.value).sort((a, b) => a[0] - b[0])
        window.legendAGI = legendAGI
        scaleLevel.value = level.value
        
    }
    if(scaleClusters.value === null || cluster_metric_agi.value !== agi_scale.value) {
        

        
        let pnp_domain   = pickData("counties").filter(c => c.properties.group.has('pnp')).map(v => getIncomeMetric(v))
        
        
        let rnr_domain   = pickData("counties").filter(c => c.properties.group.has('rnr')).map(v => getIncomeMetric(v))
        let pnr_domain   = pickData("counties").filter(c => c.properties.group.has('pnr')).map(v => getIncomeMetric(v))
        let rnp_domain   = pickData("counties").filter(c => c.properties.group.has('rnp')).map(v => getIncomeMetric(v))
        let mixed_domain = pickData("counties").filter(c => c.properties.group.has('rnp') || c.properties.group.has('pnr')).map(v => getIncomeMetric(v))
        var clusterScales;
        var clusterLegends;
        if(agi_scale.value === true) {
            clusterScales = {
                pnpScale: d3.scaleQuantile(pnp_domain, d3.schemeBlues[9]),
                rnrScale: d3.scaleQuantile(rnr_domain, d3.schemeBlues[9]),
                pnrScale: d3.scaleQuantile(pnr_domain, d3.schemeBlues[9]),
                rnpScale: d3.scaleQuantile(rnp_domain, d3.schemeBlues[9]),
                mixedScale: d3.scaleQuantile(mixed_domain, d3.schemeBlues[9]),
            }

            clusterLegends = {
                pnpLegend: getBuckets(pnp_domain.sort((a, b) => a-b), clusterScales.pnpScale),
                rnrLegend: getBuckets(rnr_domain.sort((a, b) => a-b), clusterScales.rnrScale),
                pnrLegend: getBuckets(pnr_domain.sort((a, b) => a-b), clusterScales.pnrScale),
                rnpLegend: getBuckets(rnp_domain.sort((a, b) => a-b), clusterScales.rnpScale),
            }
        } else {
            clusterScales = {
                pnpScale: d3.scaleQuantile(pnp_domain, d3.schemeReds[9]),
                rnrScale: d3.scaleQuantile(rnr_domain, d3.schemeReds[9]),
                pnrScale: d3.scaleQuantile(pnr_domain, d3.schemeReds[9]),
                rnpScale: d3.scaleQuantile(rnp_domain, d3.schemeReds[9]),
                mixedScale: d3.scaleQuantile(mixed_domain, d3.schemeReds[9]),
            }
            clusterLegends = {
                pnpLegend: getBuckets(pnp_domain.sort((a, b) => a-b), clusterScales.pnpScale),
                rnrLegend: getBuckets(rnr_domain.sort((a, b) => a-b), clusterScales.rnrScale),
                pnrLegend: getBuckets(pnr_domain.sort((a, b) => a-b), clusterScales.pnrScale),
                rnpLegend: getBuckets(rnp_domain.sort((a, b) => a-b), clusterScales.rnpScale),
            }
        }
        
        scaleClusters.value = clusterScales
        legendClusters.value = clusterLegends
        window.scales = scaleClusters
        cluster_metric_agi.value = agi_scale.value
    }

    if(level.value === "counties") {
        if(cluster.value === "none") {
            if(agi_scale.value === true) {
                return scaleAGI.value(d.properties.avg_agi)
            } else {
                return scaleG.value(d.properties.gini)
            }
            
        } 
        let focus_color = "yellow"
        let {pnpScale, rnrScale, pnrScale, rnpScale, mixedScale} = scaleClusters.value
        if(cluster.value === "pnp" && d.properties.group.has('pnp') ) {
            if(d.properties.focus.get('pnp') === true) {
                return focus_color
            }
            return pnpScale(getIncomeMetric(d))
        }
        if(cluster.value === "rnr" && d.properties.group.has("rnr") ) {
            if(d.properties.focus.get('rnr') === true) {
                return focus_color
            }
            return rnrScale(getIncomeMetric(d))
        }
        if(cluster.value === "pnr" && d.properties.group.has("pnr") ) {
            if(d.properties.focus.get('pnr') === true) {
                return focus_color
            }
            return pnrScale(getIncomeMetric(d))
        }
        if(cluster.value === "rnp" && d.properties.group.has("rnp") ) {
            if(d.properties.focus.get('rnp') === true) {
                return focus_color
            }
            return rnpScale(getIncomeMetric(d))
        }
        return "#ccc"
    } else {
        if(agi_scale.value === true)
            return scaleAGI.value(d.properties.avg_agi)
        else 
            return scaleG.value(d.properties.gini)
    }

    
        
    
}


function getTitle(d) {
    if(level.value == 'counties') {
        return `${d.properties.name}, ${d.properties.state} ( AGI: $${Math.floor(d.properties.avg_agi).toLocaleString(undefined, { minimumFractionDigits: 0 })} )`
    } else if(level.value == 'states') {
        return `${d.properties.name} ( AGI: $${Math.floor(d.properties.avg_agi).toLocaleString(undefined, {minimumFractionDigits: 0})})`
    }
    
}



function trivariateLegend() {
    trivariatePlot()
    let ticks = 5
    let scale = 15
    let strokesize = 0.2
    let translate_x = 10
    let translate_y = translate_x * (Math.sqrt(3)/2)
    let base = 10
    let height = base * (Math.sqrt(3)/2)
    let points = [[0, 0], [base, 0], [base/2, height]]
    let equilateral = `${0},${0} ${base},${0} ${base/2},${height}`
    



    let g = d3.create('svg:g')
    let triangles = ticks - 1
    for(var i = 1; i <= triangles; i++) {
        let polygon = g.append('polygon')
        
        polygon
            .attr('points', equilateral)
            .style('fill', 'cyan')
            .style('stroke', 'black')
            .style('stroke-width', strokesize)
            .attr('transform', `translate(${translate_x*i}, 0) rotate(180)`)
    }
    triangles -= 1
    for(var i = 1; i <= triangles; i++) {
        g
        .append('polygon')
            .attr('points', equilateral)
            .style('fill', 'cyan')
            .style('stroke', 'black')
            .style('stroke-width', strokesize)
            .attr('transform', `translate(${translate_x*i - translate_x/2}, ${-(translate_y)}) rotate(0)`)
    }
    for(var i = 1; i <= triangles; i++) {
        g
        .append('polygon')
            .attr('points', equilateral)
            .style('fill', 'cyan')
            .style('stroke', 'black')
            .style('stroke-width', strokesize)
            .attr('transform', `translate(${translate_x*i + translate_x/2}, ${-(translate_y)}) rotate(180)`)
    }
    triangles -= 1
    for(var i = 1; i <= triangles; i++) {
        g
        .append('polygon')
            .attr('points', equilateral)
            .style('fill', 'cyan')
            .style('stroke', 'black')
            .style('stroke-width', strokesize)
            .attr('transform', `translate(${translate_x*i}, ${-(translate_y*2)}) rotate(0)`)
    }
    for(var i = 1; i <= triangles; i++) {
        g
        .append('polygon')
            .attr('points', equilateral)
            .style('fill', 'cyan')
            .style('stroke', 'black')
            .style('stroke-width', strokesize)
            .attr('transform', `translate(${translate_x*i + translate_x}, ${-(translate_y*2)}) rotate(180)`)
    }
    
    triangles -= 1
    g
    .append('polygon')
        .attr('points', equilateral)
        .style('fill', 'cyan')
        .style('stroke', 'black')
        .style('stroke-width', strokesize)
        .attr('transform', `translate(${1.5*translate_x}, ${-(translate_y*3)}) rotate(0)`)
    g
    .append('polygon')
        .attr('points', equilateral)
        .style('fill', 'cyan')
        .style('stroke', 'black')
        .style('stroke-width', strokesize)
        .attr('transform', `translate(${2.5*translate_x}, ${-(translate_y*3)}) rotate(180)`)
    
    return g
}


function showPlot() {

    window.d3 = d3
    scaleG.value = null

    svg.value = d3.create('svg')
        .attr("viewBox", [viewBoxMinX, viewBoxMinY, width-200, height-150])
        .attr("width", width)
        .attr("height", height)
        .attr("style", "max-width: 100%; height: auto; border: grey solid 1px")
        .attr('border', 'black solid 1px')
        .on("click", reset);

    gg.value = svg.value.append('g')
    map_shapes.value = gg.value
        .append('g')
        .attr('fill', '#ccc')
        .attr('cursor', 'pointer')
        .selectAll('path')
        .data(pickData())
        .join('path')
            .attr('fill', (d) => getColor(d))
            .on('click', clicked)
            .attr('d', (g) => {
                return path(g)
        })

    map_shapes.value.append("title")
        .text(d => getTitle(d));

    gg.value.append("path")
      .attr("fill", "none")
      .attr("stroke", "#aaa")
      .attr("stroke-linejoin", "round")
      .attr("d", path(pickMesh()));

      gg.value.append("path")
      .attr("fill", "none")
      .attr("stroke", "#444")
      .attr("stroke-linejoin", "round")
      .attr("stroke-width", 1)
      .attr("d", path(pickMesh("states")));
      

    svg.value.call(zoom)
    if(document.getElementById('plot')?.childNodes.length == 0) {
        document.getElementById('plot')?.appendChild(svg.value.node())
        // showScatter()
        // showSpike()
        window.gg = gg
        gg.value.append(() => trivariateLegend().node())
        // document.getElementById('scatter')?.append(chart(pickData()))
    }


    
}


function updatePlot() {
    gg.value.remove()
    map_shapes.value.remove()

    gg.value = svg.value.append('g')

    scaleG.value = null

    map_shapes.value = gg.value
        .append('g')
        .attr('fill', "#ccc")
        .attr('cursor', 'pointer')
        .selectAll('path')
        .data(pickData())
        .join('path')
            .attr('fill', (d) => getColor(d))
            .on('click', clicked)
            .attr('d', (g) => {
                return path(g)
        })
   
    map_shapes.value.append("title")
        .text(d => getTitle(d));
   
    
    

    gg.value.append("path")
      .attr("fill", "none")
      .attr("stroke", "#aaa")
      .attr("stroke-linejoin", "round")
      .attr("d", path(pickMesh()));
    
    gg.value.append("path")
      .attr("fill", "none")
      .attr("stroke", "#444")
      .attr("stroke-linejoin", "round")
      .attr("d", path(pickMesh("states")));
    // showScatter()
    // showSpike()
}

let loaded_comparisons = ref(false)
function countyComparisons() {
    let STATE_COUNTY_FIPS_left = 0
    let GINI_left = 1
    let AVG_AGI_left = 2
    let STATE_COUNTY_FIPS_right = 3
    let GINI_right = 4
    let AVG_AGI_right = 5
    
    socket.value.on('neighbors_result', (data) => {
        let {pnp, rnr, pnr, rnp} = data
        let pnp_map: Map<number, [boolean, any[]]> = new Map(pnp.map((c) => [c[STATE_COUNTY_FIPS_right], [false, c]]))
        pnp.forEach((c) => {
            let k = c[STATE_COUNTY_FIPS_left]
            let v: [boolean, any[]] = [true, c]
            pnp_map.set(k, v)
        })
        
        let rnr_map: Map<number, [boolean, any[]]> = new Map(rnr.map((c) => [c[STATE_COUNTY_FIPS_right], [false, c]]))
        rnr.forEach((c) => {
            let k = c[STATE_COUNTY_FIPS_left]
            let v: [boolean, any[]] = [true, c]
            rnr_map.set(k, v)
        })

        let pnr_map: Map<number, [boolean, any[]]> = new Map(pnr.map((c) => [c[STATE_COUNTY_FIPS_right], [false, c]]))
        pnr.forEach((c) => {
            let k = c[STATE_COUNTY_FIPS_left]
            let v: [boolean, any[]] = [true, c]
            pnr_map.set(k, v)
        })
        let rnp_map: Map<number, [boolean, any[]]> = new Map(rnp.map((c) => [c[STATE_COUNTY_FIPS_right], [false, c]]))
        rnp.forEach((c) => {
            let k = c[STATE_COUNTY_FIPS_left]
            let v: [boolean, any[]] = [true, c]
            rnp_map.set(k, v)
        })
        window.pnp = pnp_map

        let with_group = county_fill.value.map((c) => {
            let sc_fips = Number(c.id)
            if(39075 == sc_fips) {
                console.log('asdasd')
            }
            if(c.properties.focus === undefined) {
                c.properties.focus = new Map<string, boolean>()
            }

            if(pnp_map.has(sc_fips)) {
                let datum = pnp_map.get(sc_fips) as [boolean, any[]]
                let is_focus = datum[0]
                // c.properties.avg_agi = is_focus === true ? datum[1][AVG_AGI_left] : datum[1][AVG_AGI_right]
                
                c.properties.group.add('pnp')
                c.properties.focus.set('pnp', is_focus)
                c.properties.income_class = 'poor'
            }
            if(rnr_map.has(sc_fips)) {
                let datum = rnr_map.get(sc_fips) as [boolean, any[]]
                let is_focus = datum[0]
                // c.properties.avg_agi = is_focus == true ? datum[1][AVG_AGI_left] : datum[1][AVG_AGI_right]
                c.properties.group.add('rnr')
                c.properties.focus.set('rnr', is_focus)
                c.properties.income_class = 'rich'
            }
            if(pnr_map.has(sc_fips)) {
                let datum = pnr_map.get(sc_fips) as [boolean, any[]]
                let is_focus = datum[0]
                // c.properties.avg_agi = is_focus == true ? datum[1][AVG_AGI_left] : datum[1][AVG_AGI_right]
                c.properties.group.add('pnr')
                c.properties.focus.set('pnr', is_focus)
                if(is_focus)
                    c.properties.income_class = 'poor'
                else
                    c.properties.income_class = 'rich'
            }
            if(rnp_map.has(sc_fips)) {
                let datum = rnp_map.get(sc_fips) as [boolean, any[]]
                let is_focus = datum[0]
                // c.properties.avg_agi = is_focus == true ? datum[1][AVG_AGI_left] : datum[1][AVG_AGI_right]
                c.properties.group.add('rnp')
                c.properties.focus.set('rnp', is_focus)
                if(is_focus)
                    c.properties.income_class = 'rich'
                else
                    c.properties.income_class = 'poor'
            }
            return c
        })

        county_fill.value = with_group
        loaded_comparisons.value = true
        updatePlot()        
        
    })
    socket.value.emit('neighbors', 0.1, 0.9)
}

/**
 * 
 * Spike Map - decided not to use this since it was very cluttered and difficult to 
 * see with the colored map in the background, especially in the county view.
 * 
 * Not removing it yet just to keep it for reference.
 * 
 */
// Copyright 2022 Observable, Inc.
// Released under the ISC license.
// https://observablehq.com/@d3/spike-map
//  function SpikeMap(data, {
//     position = d => d, // given d in data, returns the [longitude, latitude]
//     value = () => undefined, // given d in data, returns the quantitative value
//     title, // given a datum d, returns the hover text
//     scale = (domain, range) => d3.scaleQuantize(domain, range), // type of length scale
//     domain, // [0, max] values; input of length scale; must start at zero
//     maxLength = 200, // maximum length of spikes
//     width = 640, // outer width, in pixels
//     height, // outer height, in pixels
//     projection, // a D3 projection; null for pre-projected geometry
//     features, // a GeoJSON feature collection for the background
//     borders, // a GeoJSON object for stroking borders
//     spike = (length, width = 7) => `M${-width / 2},0L0,${-length}L${width / 2},0`,
//     outline = projection && projection.rotate ? {type: "Sphere"} : null, // a GeoJSON object for the background
//     backgroundFill = "#e0e0e0", // fill color for background
//     backgroundStroke = "white", // stroke color for borders
//     backgroundStrokeWidth, // stroke width for borders
//     backgroundStrokeOpacity, // stroke width for borders
//     backgroundStrokeLinecap = "round", // stroke line cap for borders
//     backgroundStrokeLinejoin = "round", // stroke line join for borders
//     fill = "pink", // fill color for spikes
//     fillOpacity = 0.3, // fill opacity for spikes
//     stroke = "black", // stroke color for spikes
//     strokeWidth, // stroke width for spikes
//     strokeOpacity, // stroke opacity for spikes
//     legendX = width - 20,
//     legendY = height - 20,
//   } = {}) {
//     // Compute values.
//     const I = d3.map(data, (_, i) => i);
//     const V = d3.map(data, value)
//     const P = d3.map(data, position);
//     const T = title == null ? null : d3.map(data, title);
  
//     // Compute default domains.
//     if (domain === undefined) domain = [0, d3.max(V)];
  
//     // Construct scales.
//     const length = scale(V.sort((a, b) => a-b), [1, 5, 20, 40, 60, 80, 100]);
  
//     // Compute the default height. If an outline object is specified, scale the projection to fit
//     // the width, and then compute the corresponding height.
//     if (height === undefined) {
//       if (outline === undefined) {
//         height = 400;
//       } else {
//         const [[x0, y0], [x1, y1]] = d3.geoPath(projection.fitWidth(width, outline)).bounds(outline);
//         const dy = Math.ceil(y1 - y0), l = Math.min(Math.ceil(x1 - x0), dy);
//         projection.scale(projection.scale() * (l - 1) / l).precision(0.2);
//         height = dy;
//       }
//     }
  
//     // Construct a path generator.
//     const path = d3.geoPath(projection);
  
//     const svg = d3.select("svg")
 
  
//     const legend = svg.append("g")
//         .attr("fill", "#777")
//         .attr("text-anchor", "middle")
//         .attr("font-family", "sans-serif")
//         .attr("font-size", 10)
//       .selectAll("g")
//         .data(length.ticks(4).slice(1).reverse())
//       .join("g")
//         .attr("transform", (d, i) => `translate(${legendX - i * 18},${legendY})`);
  
//     legend.append("path")
//         .attr("fill", "red")
//         .attr("fill-opacity", 0.3)
//         .attr("stroke", "red")
//         .attr("d", d => spike(length(d)));
  
//     legend.append("text")
//         .attr("dy", "1.3em")
//         .text(length.tickFormat(4, "s"));
  
//     let spikes = gg.value.append('g')
    
//     spikes.attr("fill", fill)
//         .attr("fill-opacity", fillOpacity)
//         .attr("stroke", stroke)
//         .attr("stroke-width", strokeWidth)
//         .attr("stroke-opacity", strokeOpacity)
//       .selectAll("path")
//       .data(d3.range(data.length)
//           .filter(i => P[i])
//           .sort((i, j) => d3.ascending(P[i][1], P[j][1]) || d3.ascending(P[i][0], P[j][0])))
//       .join("path")
//         .attr("transform", projection == null
//             ? i => `translate(${P[i]})`
//             : i => `translate(${projection(P[i])})`)
//         .attr("d", i => spike(length(V[i])))
//         .call(T ? path => path.append("title").text(i => T[i]) : () => {});
//     return spikes;
//   }
// function centroid(feature: any) { 
//   return path.centroid(feature);
// }
// let chart = (income_metric, statemap, countymap) => SpikeMap(income_metric, {
//   value: (d) => {
//     let {income_metric, statefips, countyfips} = d
//     return income_metric
//   },
//   position(d) {
//     let {income_metric, statefips, countyfips} = d
//     if(level.value == 'counties') {
//         const county = countymap.get(countyfips);
//         return centroid(county);
//     } else {
//         let state = statemap.get(statefips)
//         return centroid(state)
//     }
    
//   },
//   title: (d) => {
//     let {income_metric, statefips, countyfips} = d
//     const state = statemap.get(statefips)
//     const county = countymap.get(countyfips)
//     return `${county?.properties.name}, ${state?.properties.name}\n${(Number(income_metric)).toLocaleString("en")}`;
//   },
//   features: county_fill.value,
//   borders: county_mesh.value,
//   width: 975,
//   height: 610
// })


// function showSpike() {

//     let countymap = new Map(county_fill.value.map(d => [d.id, d]))
//     let statemap = new Map(state_fill.value.map(d => [d.id, d]))

//     let data = pickData().map((d: any) => ({
//         'income_metric': getIncomeMetric(d),
//         'statefips': d.id[0] + d.id[1],
//         'countyfips': d.id
//     }))
//     chart(data, statemap, countymap)
// }


// function showScatter() {
//     // Specify the chart?s dimensions.
//   const width = 928;
//   const height = 600;
//   const marginTop = 20;
//   const marginRight = 30;
//   const marginBottom = 30;
//   const marginLeft = 40;

//   d3.select("svg[data-scatter=true]").remove()

//   // Create the horizontal (x) scale, positioning N/A values on the left margin.
//   const x = d3.scaleLinear()
//       .domain([0, d3.max(pickData(), d => getIncomeMetric(d))]).nice()
//       .range([marginLeft, width - marginRight])
//       .unknown(marginLeft);

//   // Create the vertical (y) scale, positioning N/A values on the bottom margin.
//   const y = d3.scaleLinear()
//       .domain([0, d3.max(pickData(), d => getIncomeMetric(d))]).nice()
//       .range([height - marginBottom, marginTop])
//       .unknown(height - marginBottom);

//   // Create the SVG container.
//   const svg = d3.create("svg")
//       .attr("viewBox", [0, 0, width, height])
//       .attr("data-scatter", true)
//       .property("value", []);

//   // Append the axes.
//   svg.append("g")
//       .attr("transform", `translate(0,${height - marginBottom})`)
//       .call(d3.axisBottom(x))
//       .call(g => g.select(".domain").remove())
//       .call(g => g.append("text")
//           .attr("x", width - marginRight)
//           .attr("y", -4)
//           .attr("fill", "#000")
//           .attr("font-weight", "bold")
//           .attr("text-anchor", "end")
//           .text("Health vs. Income"));

//   svg.append("g")
//       .attr("transform", `translate(${marginLeft},0)`)
//       .call(d3.axisLeft(y))
//       .call(g => g.select(".domain").remove())
//       .call(g => g.select(".tick:last-of-type text").clone()
//           .attr("x", 4)
//           .attr("text-anchor", "start")
//           .attr("font-weight", "bold")
//           .text("Health Outcome (normalized to maximum observation)"));

//   // Append the dots.
//   const dot = svg.append("g")
//       .attr("fill", "none")
//       .attr("stroke", "steelblue")
//       .attr("stroke-width", 1.5)
//     .selectAll("circle")
//     .data(pickData())
//     .join("circle")
//       .attr("transform", d => `translate(${x(getIncomeMetric(d))},${y(getIncomeMetric(d))})`)
//       .attr("r", 3);

//   // Create the brush behavior.
//   svg.call(d3.brush().on("start brush end", ({selection}) => {
//     let value = [];
//     if (selection) {
//       const [[x0, y0], [x1, y1]] = selection;
//       value = dot
//         .style("stroke", "gray")
//         .filter(d => x0 <= x(getIncomeMetric(d)) && x(getIncomeMetric(d)) < x1
//                 && y0 <= y(getIncomeMetric(d)) && y(getIncomeMetric(d)) < y1)
//         .style("stroke", "steelblue")
//         .data();
//     } else {
//       dot.style("stroke", "steelblue");
//     }

//     // Inform downstream cells that the selection has changed.
//     svg.property("value", value).dispatch("input");
//   }));

//   document.getElementById('scatter')?.append(svg.node())
// }

onMounted(() => {
    trivariatePlot()
    let query = `
    SELECT STATE_COUNTY_FIPS, GINI, STATE_NAME
    FROM cps_00004.county_gini
    JOIN cps_00004.county_fips
    ON county_gini.STATE_COUNTY_FIPS = county_fips.STATE_COUNTY_FIPS
    WHERE 0 < GINI AND GINI < 100
    `

    let query_state = `
    SELECT STATE_FIPS, avg(GINI), any(STATE_NAME)
    FROM cps_00004.county_gini
    JOIN cps_00004.county_fips
    ON county_gini.STATE_COUNTY_FIPS = county_fips.STATE_COUNTY_FIPS GROUP BY STATE_FIPS
    `

    let county_agi = `
    SELECT COUNTYFIP, (sum(ADJUSTED_GROSS_INCOME) / sum(NUM_RETURNS)) as avg_agi, (sum(TAXES_PAID_AMOUNT) / sum(NUM_RETURNS)) as avg_tax
    FROM cps_00004.income_tax 
    GROUP BY cps_00004.income_tax.COUNTYFIP
    `

    let state_agi = `
    SELECT STATEFIPS, (sum(ADJUSTED_GROSS_INCOME) / sum(NUM_RETURNS)) as avg_agi, (sum(TAXES_PAID_AMOUNT) / sum(NUM_RETURNS)) as avg_tax
    FROM cps_00004.income_tax 
    GROUP BY cps_00004.income_tax.STATEFIPS
    `

    let health_county_query = `
    SELECT COUNTY_FIPS, MEASURE as measure, avg(DATA_VALUE) as avg_data_value 
    FROM cps_00004.places_county 
    WHERE MEASURE LIKE '%heart%' OR MEASURE LIKE '%Cancer%' OR MEASURE LIKE '%teeth%' OR MEASURE LIKE '%dentist%' OR MEASURE LIKE '%Fair or poor self-rated health status among adults%' OR MEASURE LIKE '%Stroke among adults aged%'
    GROUP BY COUNTY_FIPS, MEASURE
    `

    let health_state_query = `
    SELECT STATE_FIPS, MEASURE as measure, avg(DATA_VALUE) as avg_data_value
    FROM (
            SELECT STATE_NAME, MEASURE as measure, avg(DATA_VALUE) as avg_data_value 
            FROM cps_00004.places_county 
            WHERE MEASURE LIKE '%heart%' OR MEASURE LIKE '%Cancer%' OR MEASURE LIKE '%teeth%' OR MEASURE LIKE '%dentist%' OR MEASURE LIKE '%Fair or poor self-rated health status among adults%' OR MEASURE LIKE '%Stroke among adults aged%'
            GROUP BY COUNTY_FIPS, MEASURE
        ) 
        as inside
    JOIN cps_00004.state_fips
    ON cps_00004.state_fips.STATE_NAME = inside.STATE_NAME
    `

    socket.value.on('data', (data) => {
        if(data['name'] == 'county') {
            let cg = new Map<number, [number, string]>(data['data'].map((row) => { return [row[0], [row[1], row[2]] ]}))
            let with_gini = county_fill.value.map((c) => {
                // state-county combined FIPS
                let sc_fips = Number(c.id)

                if(cg.has(sc_fips))  {
                    c.properties.gini = cg.get(sc_fips)[0]
                    c.properties.state = cg.get(sc_fips)[1]
                }
                return c
            })
            county_fill.value = with_gini

            if(data['end'] == true) 
                socket.value.emit('query', query_state, 'state')
                // showPlot()
        }

        if(data['name'] == 'state') {
            let sg = new Map<number, [number, string]>(data['data'].map((row) => { return [row[0], [row[1], row[2]] ]}))
            let with_gini = state_fill.value.map((s) => {
                // state-county combined FIPS
                let s_fips = Number(s.id)

                if(sg.has(s_fips))  {
                    s.properties.gini = sg.get(s_fips)[0]
                    s.properties.state = sg.get(s_fips)[1]
                }
                return s
            })
            state_fill.value = with_gini

            if(data['end'] == true) 
                showPlot()
        }

        if(data['name'] == 'county_agi') {
            // row: COUNTYFIPS, AGI, TAX
            let ca = new Map<number, [number, number]>(data['data'].map((row) => { return [row[0], [row[1], row[2]] ]}))
            let with_agi = county_fill.value.map((c) => {
                let sc_fips = Number(c.id)

                if(ca.has(sc_fips)) {
                    let agi = ca.get(sc_fips)[0]
                    let tax = ca.get(sc_fips)[1]
                    c.properties.avg_agi = agi
                    c.properties.avg_tax = tax
                }
                return c
            })
            county_fill.value = with_agi
            if(level.value === "counties") {
                updatePlot()
            }
        }

        if(data['name'] == 'state_agi') {
            // row: STATE_FIPS, AGI, TAX
            let sa = new Map<number, [number, number]>(data['data'].map((row) => { return [row[0], [row[1], row[2]] ]}))
            let with_agi = state_fill.value.map((s) => {
                let s_fips = Number(s.id)

                if(sa.has(s_fips)) {
                    let agi = sa.get(s_fips)[0]
                    let tax = sa.get(s_fips)[1]
                    s.properties.avg_agi = agi
                    s.properties.avg_tax = tax
                }
                return s
            })

            state_fill.value = with_agi
            if(level.value === "states") {
                // updatePlot()
            }
        }

        if(data['name'] === 'health_county') {
            let ca = new Map<number, [string, number]>(data['data'].map((row) => { return [row[0], [row[1], row[2]]  ]}))
            let with_health = county_fill.value.map((c) => {
                let sc_fips = Number(c.id)

                if(c.properties.health_metrics === undefined) {
                    c.properties.health_metrics = new Map<string, number>()
                }

                if(ca.has(sc_fips)) {
                    let [measure, datavalue] = ca.get(sc_fips) as [string, number]
                    c.properties.health_metrics.set(measure, datavalue)
                }
                return c
            })
            county_fill.value = with_health
            // if(level.value === "counties") {
            //     updatePlot()
            // }
        }

        if(data['name'] === 'health_county') {
            let sa = new Map<number, [string, number]>(data['data'].map((row) => { return [row[0], [row[1], row[2]]  ]}))
            let with_health = state_fill.value.map((s) => {
                let s_fips = Number(s.id)

                if(s.properties.health_metrics === undefined) {
                    s.properties.health_metrics = new Map<string, number>()
                }

                if(sa.has(s_fips)) {
                    let [measure, datavalue] = sa.get(s_fips) as [string, number]
                    s.properties.health_metrics.set(measure, datavalue)
                }
                return s
            })
            state_fill.value = with_health
        }

    })
    window.agi_scale = agi_scale
    fetch(`http://localhost:9001/counties-albers-10m.json`)
    .then((res) => {
        
        return res.json()
    })
    .then((json) => {
        geojson.value = json
        
        

        county_mesh.value   = topojson.mesh(geojson.value, geojson.value.objects.counties, (a, b) => a !== b)
        window.county_mesh = county_mesh
        state_mesh.value    = topojson.mesh(geojson.value, geojson.value.objects.states, (a, b) => a !== b)   
        window.state_mesh = state_mesh
        county_fill.value   = topojson.feature(geojson.value, geojson.value.objects.counties).features
        window.county_fill = county_fill
        county_fill.value.map((c) => {
            if(!c.properties.group) {
                c.properties.group = new Set()
            }
            
        })
        state_fill.value    = topojson.feature(geojson.value, geojson.value.objects.states).features
        window.state_fill = state_fill

        socket.value.emit('query', query, "county")
        socket.value.emit('query', county_agi, "county_agi")
        socket.value.emit('query', state_agi, "state_agi")
        socket.value.emit('query', health_county_query, 'health_county')
        socket.value.emit('query', health_state_query, 'health_state')
    })
    
    
    
    document.querySelector("#scaleToggle").bootstrapToggle({
        on: 'AGI',
        off: 'Gini'
    });

    document.querySelector("#stateScaleToggle").bootstrapToggle({
        off: 'National',
        on: 'State'
    });


    

})

function doCluster() {
    scaleG.value = null
    scaleClusters.value = null
    countyComparisons()
}

</script>
<template>
    <div class="row">
        <div class="col-md-9" id="plot"></div>
        <div class="col-md-3">
            <div class="accordion" id="menus">
                <div class="accordion-item">
                    <h2 class="accordion-header" id="plots-controls">
                    <button class="accordion-button" type="button" data-bs-toggle="collapse" data-bs-target="#collapseOne" aria-expanded="true" aria-controls="collapseOne">
                        Plot Controls
                    </button>
                    </h2>
                    <div id="collapseOne" class="accordion-collapse collapse show" aria-labelledby="plots-controls" >
                    <div class="accordion-body">
                        <div class="row">
                            <label>Group By:</label>
                            <select class="form-select my-3" v-model="level" @change="updatePlot">
                                <option key="states" value="states">states</option>
                                <option key="counties" value="counties">counties</option>
                            </select>
                        </div>
                        <div class="row my-3">
                            <p>Color Coding Metric:</p>
                            <input 
                                id="scaleToggle" 
                                type="checkbox" 
                                v-model="agi_scale"
                                @change="updatePlot"
                                data-toggle="toggle"  
                                data-onstyle="outline-primary" 
                                data-offstyle="outline-danger" ></input>
                        </div>
                        <div class="row my-3">
                            <p>Color Coding Scale Domain (non-functional):</p>
                            <input 
                                id="stateScaleToggle" 
                                type="checkbox" 
                                v-model="state_scale"
                                @change="updatePlot"
                                data-toggle="toggle"  
                                data-onstyle="outline-dark" 
                                data-offstyle="outline-success" ></input>
                        </div>
                        
                        <div class="row">
                            <select class="form-select my-3" v-if="level == 'counties'" v-model="cluster" @click="doCluster">
                                <option key="none" value="none">No Clusters</option>
                                <option key="pnp" value="pnp">Poor Near Poor</option>
                                <option key="rnr" value="rnr">Rich Near Rich</option>
                                <option key="rnp" value="rnp">Rich Near Poor</option>
                                <option key="pnr" value="pnr">Poor Near Rich</option>
                            </select>
                            <select class="form-select my-3" v-else v-model="cluster" disabled>
                                <option key="none" value="none">No Clusters</option>
                                <option key="pnp" value="pnp">Poor Near Poor</option>
                                <option key="rnr" value="rnr">Rich Near Rich</option>
                                <option key="rnp" value="rnp">Rich Near Poor</option>
                                <option key="pnr" value="pnr">Poor Near Rich</option>
                            </select>
                        </div>
                        <div class="row">
                            <button class="btn btn-primary" @click="reset()">Reset</button>
                        </div>
                    </div>
                    </div>
                </div>
                <div class="accordion-item">
                    <h2 class="accordion-header" id="color-legend">
                    <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#collapseTwo" aria-expanded="false" aria-controls="collapseTwo">
                        Plot Legend
                    </button>
                    </h2>
                    <div id="collapseTwo" class="accordion-collapse collapse" aria-labelledby="color-legend" >
                    <div class="accordion-body">
                        <div class="row">
                            <div v-if="agi_scale && cluster == 'none'">
                                <p>Adjusted Gross Income (AGI):</p>
                                <div v-for="elem in legendAGI">
                                    <span class="d-inline-block">
                                        <div class="d-flex" :style="{backgroundColor: elem[2], height: '1em', width: '1em'}"></div>
                                    </span>
                                    <span class="d-inline mx-2">{{'$' + (elem[0] / 1000).toFixed(0) + 'k' }}</span>
                                    <span class="d-inline mx-1"> - </span>
                                    <span class="d-inline mx-2">{{'$' + (elem[1] / 1000).toFixed(0) + 'k'}}</span>
                                </div>
                            </div>
                            <div v-if="!agi_scale && cluster == 'none'">
                                <p>Gini Coefficient:</p>
                                <div v-for="elem in legendG">
                                    <span class="d-inline-block">
                                        <div class="d-flex" :style="{backgroundColor: elem[2], height: '1em', width: '1em'}"></div>
                                    </span>
                                    <span class="d-inline mx-3" v-if="agi_scale">{{ '$' + (elem[0]/1000).toFixed(0) + 'k' }}</span>
                                    <span class="d-inline mx-2" v-else>{{ elem[0].toFixed(3) }}</span>
                                    <span class="d-inline mx-1"> - </span>
                                    <span class="d-inline mx-2" v-if="agi_scale">{{ '$' + (elem[1]/1000).toFixed(0) + 'k' }}</span>
                                    <span class="d-inline mx-2" v-else>{{ elem[1].toFixed(3) }}</span>
                                </div>
                            </div>
                            <div v-if="cluster == 'pnp'">
                                <p v-if="agi_scale">Adjusted Gross Income (AGI):</p>
                                <p v-else>Gini Coefficient:</p>
                                <div v-for="elem in legendClusters.pnpLegend">
                                    <span class="d-inline-block">
                                        <div class="d-flex" :style="{backgroundColor: elem[2], height: '1em', width: '1em'}"></div>
                                    </span>
                                    <span class="d-inline mx-3" v-if="agi_scale">{{ '$' + (elem[0]/1000).toFixed(0) + 'k' }}</span>
                                    <span class="d-inline mx-2" v-else>{{ elem[0].toFixed(3) }}</span>
                                    <span class="d-inline mx-1"> - </span>
                                    <span class="d-inline mx-2" v-if="agi_scale">{{ '$' + (elem[1]/1000).toFixed(0) + 'k' }}</span>
                                    <span class="d-inline mx-2" v-else>{{ elem[1].toFixed(3) }}</span>
                                </div>
                            </div>
                            <div v-if="cluster == 'rnr'">
                                <p v-if="agi_scale">Adjusted Gross Income (AGI):</p>
                                <p v-else>Gini Coefficient:</p>
                                <div v-for="elem in legendClusters.rnrLegend">
                                    <span class="d-inline-block">
                                        <div class="d-flex" :style="{backgroundColor: elem[2], height: '1em', width: '1em'}"></div>
                                    </span>
                                    <span class="d-inline mx-3" v-if="agi_scale">{{ '$' + (elem[0]/1000).toFixed(0) + 'k' }}</span>
                                    <span class="d-inline mx-2" v-else>{{ elem[0].toFixed(3) }}</span>
                                    <span class="d-inline mx-1"> - </span>
                                    <span class="d-inline mx-2" v-if="agi_scale">{{ '$' + (elem[1]/1000).toFixed(0) + 'k' }}</span>
                                    <span class="d-inline mx-2" v-else>{{ elem[1].toFixed(3) }}</span>
                                </div>
                            </div>
                            <div v-if="cluster == 'pnr'">
                                <p v-if="agi_scale">Adjusted Gross Income (AGI):</p>
                                <p v-else>Gini Coefficient:</p>
                                <div v-for="elem in legendClusters.pnrLegend">
                                    <span class="d-inline-block">
                                        <div class="d-flex" :style="{backgroundColor: elem[2], height: '1em', width: '1em'}"></div>
                                    </span>
                                    <span class="d-inline mx-3" v-if="agi_scale">{{ '$' + (elem[0]/1000).toFixed(0) + 'k' }}</span>
                                    <span class="d-inline mx-2" v-else>{{ elem[0].toFixed(3) }}</span>
                                    <span class="d-inline mx-1"> - </span>
                                    <span class="d-inline mx-2" v-if="agi_scale">{{ '$' + (elem[1]/1000).toFixed(0) + 'k' }}</span>
                                    <span class="d-inline mx-2" v-else>{{ elem[1].toFixed(3) }}</span>
                                </div>
                            </div>
                            <div v-if="cluster == 'rnp'">
                                <p v-if="agi_scale">Adjusted Gross Income (AGI):</p>
                                <p v-else>Gini Coefficient:</p>
                                <div v-for="elem in legendClusters.rnpLegend">
                                    <span class="d-inline-block">
                                        <div class="d-flex" :style="{backgroundColor: elem[2], height: '1em', width: '1em'}"></div>
                                    </span>
                                    <span class="d-inline mx-2">{{ elem[0].toFixed(3) }}</span>
                                    <span class="d-inline mx-1"> - </span>
                                    <span class="d-inline mx-2">{{ elem[1].toFixed(3) }}</span>
                                </div>
                            </div>
                        </div>
                    </div>
                    </div>
                </div>
                <div class="accordion-item">
                    <h2 class="accordion-header" id="health-metrics">
                    <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#collapseThree" aria-expanded="false" aria-controls="collapseThree">
                        Health Metrics
                    </button>
                    </h2>
                    <div id="collapseThree" class="accordion-collapse collapse" aria-labelledby="health-metrics" >
                    <div class="accordion-body">
                        <div id="scatter"></div>
                    </div>
                    </div>
                </div>
            </div>
           
            
        </div>
    </div>
</template>