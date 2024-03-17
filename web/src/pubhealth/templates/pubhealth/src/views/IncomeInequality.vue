<script setup lang="ts">
import transformScale from '@turf/transform-scale'
import interset from '@turf/intersect'
import { ref, onMounted, onUnmounted } from "vue";
import type { Ref } from "vue";
import { logger } from '../utils/logging';
import { io, Socket } from "socket.io-client";

//@ts-ignore
import * as d3 from "d3";

import * as topojson from "topojson"
// import * as turf from "@turf/turf"



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

// function showPlot() {

//     window.d3 = d3
//     scaleG.value = null

//     svg.value = d3.create('svg')
//         .attr("viewBox", [viewBoxMinX, viewBoxMinY, width-200, height-150])
//         .attr("width", width)
//         .attr("height", height)
//         .attr("style", "max-width: 100%; height: auto; border: grey solid 1px")
//         .attr('border', 'black solid 1px')
//         .on("click", reset);

//     gg.value = svg.value.append('g')
//     map_shapes.value = gg.value
//         .append('g')
//         .attr('fill', '#ccc')
//         .attr('cursor', 'pointer')
//         .selectAll('path')
//         .data(pickData())
//         .join('path')
//             .attr('fill', (d) => getColor(d))
//             .on('click', clicked)
//             .attr('d', (g) => {
//                 return path(g)
//         })

//     map_shapes.value.append("title")
//         .text(d => getTitle(d));

//     gg.value.append("path")
//       .attr("fill", "none")
//       .attr("stroke", "#aaa")
//       .attr("stroke-linejoin", "round")
//       .attr("d", path(pickMesh()));

//       gg.value.append("path")
//       .attr("fill", "none")
//       .attr("stroke", "#444")
//       .attr("stroke-linejoin", "round")
//       .attr("stroke-width", 1)
//       .attr("d", path(pickMesh("states")));
      

//     svg.value.call(zoom)
//     if(document.getElementById('plot')?.childNodes.length == 0) {
//         document.getElementById('plot')?.appendChild(svg.value.node())
//     }


    
// }


// function updatePlot() {
//     gg.value.remove()
//     map_shapes.value.remove()

//     gg.value = svg.value.append('g')

//     scaleG.value = null

//     map_shapes.value = gg.value
//         .append('g')
//         .attr('fill', "#ccc")
//         .attr('cursor', 'pointer')
//         .selectAll('path')
//         .data(pickData())
//         .join('path')
//             .attr('fill', (d) => getColor(d))
//             .on('click', clicked)
//             .attr('d', (g) => {
//                 return path(g)
//         })
   
//     map_shapes.value.append("title")
//         .text(d => getTitle(d));
   
    
    

//     gg.value.append("path")
//       .attr("fill", "none")
//       .attr("stroke", "#aaa")
//       .attr("stroke-linejoin", "round")
//       .attr("d", path(pickMesh()));
    
//     gg.value.append("path")
//       .attr("fill", "none")
//       .attr("stroke", "#444")
//       .attr("stroke-linejoin", "round")
//       .attr("d", path(pickMesh("states")));
// }

// let loaded_comparisons = ref(false)
// function countyComparisons() {
//     let STATE_COUNTY_FIPS_left = 0
//     let GINI_left = 1
//     let AVG_AGI_left = 2
//     let STATE_COUNTY_FIPS_right = 3
//     let GINI_right = 4
//     let AVG_AGI_right = 5
    
//     socket.value.on('neighbors_result', (data) => {
//         let {pnp, rnr, pnr, rnp} = data
//         let pnp_map: Map<number, [boolean, any[]]> = new Map(pnp.map((c) => [c[STATE_COUNTY_FIPS_right], [false, c]]))
//         pnp.forEach((c) => {
//             let k = c[STATE_COUNTY_FIPS_left]
//             let v: [boolean, any[]] = [true, c]
//             pnp_map.set(k, v)
//         })
        
//         let rnr_map: Map<number, [boolean, any[]]> = new Map(rnr.map((c) => [c[STATE_COUNTY_FIPS_right], [false, c]]))
//         rnr.forEach((c) => {
//             let k = c[STATE_COUNTY_FIPS_left]
//             let v: [boolean, any[]] = [true, c]
//             rnr_map.set(k, v)
//         })

//         let pnr_map: Map<number, [boolean, any[]]> = new Map(pnr.map((c) => [c[STATE_COUNTY_FIPS_right], [false, c]]))
//         pnr.forEach((c) => {
//             let k = c[STATE_COUNTY_FIPS_left]
//             let v: [boolean, any[]] = [true, c]
//             pnr_map.set(k, v)
//         })
//         let rnp_map: Map<number, [boolean, any[]]> = new Map(rnp.map((c) => [c[STATE_COUNTY_FIPS_right], [false, c]]))
//         rnp.forEach((c) => {
//             let k = c[STATE_COUNTY_FIPS_left]
//             let v: [boolean, any[]] = [true, c]
//             rnp_map.set(k, v)
//         })
//         window.pnp = pnp_map

//         let with_group = county_fill.value.map((c) => {
//             let sc_fips = Number(c.id)
//             if(39075 == sc_fips) {
//                 console.log('asdasd')
//             }
//             if(c.properties.focus === undefined) {
//                 c.properties.focus = new Map<string, boolean>()
//             }

//             if(pnp_map.has(sc_fips)) {
//                 let datum = pnp_map.get(sc_fips) as [boolean, any[]]
//                 let is_focus = datum[0]
//                 // c.properties.avg_agi = is_focus === true ? datum[1][AVG_AGI_left] : datum[1][AVG_AGI_right]
                
//                 c.properties.group.add('pnp')
//                 c.properties.focus.set('pnp', is_focus)
//                 c.properties.income_class = 'poor'
//             }
//             if(rnr_map.has(sc_fips)) {
//                 let datum = rnr_map.get(sc_fips) as [boolean, any[]]
//                 let is_focus = datum[0]
//                 // c.properties.avg_agi = is_focus == true ? datum[1][AVG_AGI_left] : datum[1][AVG_AGI_right]
//                 c.properties.group.add('rnr')
//                 c.properties.focus.set('rnr', is_focus)
//                 c.properties.income_class = 'rich'
//             }
//             if(pnr_map.has(sc_fips)) {
//                 let datum = pnr_map.get(sc_fips) as [boolean, any[]]
//                 let is_focus = datum[0]
//                 // c.properties.avg_agi = is_focus == true ? datum[1][AVG_AGI_left] : datum[1][AVG_AGI_right]
//                 c.properties.group.add('pnr')
//                 c.properties.focus.set('pnr', is_focus)
//                 if(is_focus)
//                     c.properties.income_class = 'poor'
//                 else
//                     c.properties.income_class = 'rich'
//             }
//             if(rnp_map.has(sc_fips)) {
//                 let datum = rnp_map.get(sc_fips) as [boolean, any[]]
//                 let is_focus = datum[0]
//                 // c.properties.avg_agi = is_focus == true ? datum[1][AVG_AGI_left] : datum[1][AVG_AGI_right]
//                 c.properties.group.add('rnp')
//                 c.properties.focus.set('rnp', is_focus)
//                 if(is_focus)
//                     c.properties.income_class = 'rich'
//                 else
//                     c.properties.income_class = 'poor'
//             }
//             return c
//         })

//         county_fill.value = with_group
//         loaded_comparisons.value = true
//         updatePlot()        

//     })
//     socket.value.emit('neighbors', 0.1, 0.9)
// }
// interface DataElem {
//     avg_agi: number,
//     avg_tax: number,
//     region: string,
//     division: string, 
//     state_name: string,
//     county_name: string,
//     measures: Map<string, number>
// }

// interface State {
//     state_name: string
//     state_abbrev: string
//     fips: number
//     region: string
//     division: string
// }

// let model: Ref<Map<string, Map<string, DataElem>>> = ref(new Map())
// let hidden_data: Ref<Map<string, Map<string, DataElem>>> = ref(new Map())
// let all_measures: Ref<Set<string>> = ref(new Set())
// let max_measure: Ref<Map<string, number>> = ref(new Map())
// let plot_displayed: Ref<boolean> = ref(false)

// let ALL_STATES: Ref<Array<State>> = ref([])
// let ALL_REGIONS: Ref<Map<string, State[]>> = ref(new Map())
// let ALL_DIVISIONS: Ref<Map<string, State[]>> = ref(new Map())
// let CHOOSEN_STATES: Ref< Map<string, [boolean, string]> > = ref(new Map())
// let CHOOSEN_REGIONS: Ref< Map<string, [boolean, string]> > = ref(new Map())
// let CHOOSEN_DIVISIONS: Ref< Map<string, [boolean, string]> > = ref(new Map())


// function getFlatData() {
//     return Array.from(model.value.values()).flatMap((map) => Array.from(map.values()))
// }
// function getProportionateData(d: DataElem, measure: string) {
//     return ((d.measures.get(measure) as number) / (max_measure.value.get(measure) as number))
// }

// const root: Ref<any> = ref(null)
// const tupstr = (tup: [number, number]) => {return `${tup[0]}-${tup[1]}`}
// const datakey = (d: DataElem) => {return `${d.state_name}-${d.county_name}`}
// const enumerate = d3.scaleOrdinal()
//     .domain(d3.cross(d3.range(3), d3.range(2)).map(tupstr))
//     .range([0, 1, 2, 3, 4, 5])


// const reverseEnumeration = d3.scaleOrdinal(enumerate.range(), enumerate.domain())

// function brush(cell: any, circle: any, svg: any, {padding, size, x, y, columns}: any) {
//     const brush = d3.brush()
//         .extent([[padding / 2, padding / 2], [size - padding / 2, size - padding / 2]])
//         .on("start", brushstarted)
//         .on("brush", brushed)
//         .on("end", brushended);

//     cell.call(brush);

//     let brushCell: any;

//     // Clear the previously-active brush, if any.
//     function brushstarted() {
//         //@ts-ignore
//         if (brushCell !== this) {
//         d3.select(brushCell).call(brush.move, null);
//         //@ts-ignore
//         brushCell = this;
//         }
//     }

//     // Highlight the selected circles.
//     function brushed({selection}: any, [i, j]: any) {
//         let selected: any[] = [];
//         if (selection) {
//         const [[x0, y0], [x1, y1]] = selection; 
//         circle.classed("hidden",
//             (d: DataElem) => x0 > x[i](d.avg_agi)
//             || x1 < x[i](d.avg_agi)
//             || y0 > y[j]( getProportionateData(d, columns[enumerate(tupstr([i, j]))]))
//             || y1 < y[j]( getProportionateData(d, columns[enumerate(tupstr([i, j]))])  ));
//         selected = getFlatData().filter(
//             (d: DataElem) => x0 < x[i](d.avg_agi)
//             && x1 > x[i](d.avg_agi)
//             && y0 < y[j](getProportionateData(d, columns[enumerate(tupstr([i, j]))]))
//             && y1 > y[j](getProportionateData(d, columns[enumerate(tupstr([i, j]))])));
//         }
//         svg.property("value", selected).dispatch("input");
//     }

//     // If the brush is empty, select all circles.
//     function brushended({selection}: any) {
//         if (selection) return;
//         svg.property("value", []).dispatch("input");
//         circle.classed("hidden", false);
//     }
// }
// const labels = ref(new Set<string>())

// let colorscale: Ref<any | undefined> = ref(undefined)

// function labelEnter(enter) {
//     enter.append('foreignObject')
//     // enter.each( (nodes) => {
//         // console.log('entering node')
//         // console.log(nodes)
//     // } )
//     // console.log('entering')
//     // console.log(enter)
//     // return enter
    
// }

// function labelUpdate(update) {
//     // console.log(`updated: ${JSON.stringify(update)}`)
//     update.append('foreignObject')
//     // update.remove()
//     return update
// }

// function labelExit(exit) {
//     // console.log(`exited: ${JSON.stringify(exit)}`)
//     exit.remove()
//     // return exit
// }
// function showPlot() {
//     if(plot_displayed.value) {
//         return;
//     }
//     const ordered_measures = 
//         Array.from(
//             all_measures
//             .value
//             .values()).sort((a, b) => a.localeCompare(b))
//     const columns = ordered_measures
//     const width = 600
//     const height = width
//     const padding = 20
//     const size = 300//(width - (columns.length + 1) * padding) / columns.length + padding;

//     const measures = Array.from(all_measures.value.values())
//     const x = measures.map(m => {
//         return d3.scaleLinear()
//         .domain(d3.extent(Array.from(model.value.values()).flatMap((map) => Array.from(map.values())), (d: DataElem) => d.avg_agi))
//         .rangeRound([padding / 2, size - padding / 2])
//     })

//     const y = measures.map(m => {
//         return d3.scaleLinear()
//         .domain([0.0, 1.0])
//         .range([size - padding / 2, padding / 2])
//     })

    
    
//     String.prototype.hashCode = function() {
//         var hash = 0,
//             i, chr;
//         if (this.length === 0) return hash;
//         for (i = 0; i < this.length; i++) {
//             chr = this.charCodeAt(i);
//             hash = ((hash << 5) - hash) + chr;
//             hash |= 0; // Convert to 32bit integer
//         }
//         return hash;
//     }

//     const color = d3.scaleOrdinal()
//         .domain(Array.from(model.value.keys()))
//         .range(["#1f77b4","#ff7f0e","#2ca02c","#d62728","#9467bd","#8c564b","#e377c2","#7f7f7f","#bcbd22","#17becf", "#8dd3c7","#ffffb3","#bebada","#fb8072","#80b1d3","#fdb462","#b3de69","#fccde5","#d9d9d9","#bc80bd","#ccebc5","#ffed6f", "#8dd3c7","#ffffb3","#bebada","#fb8072","#80b1d3","#fdb462","#b3de69","#fccde5","#d9d9d9","#bc80bd","#ccebc5","#ffed6f"])
//         // .range(["#ff4040","#ff423d","#ff453a","#ff4838","#fe4b35","#fe4e33","#fe5130","#fd542e","#fd572b","#fc5a29","#fb5d27","#fa6025","#f96322","#f96620","#f7691e","#f66c1c","#f56f1a","#f47218","#f37517","#f17815","#f07c13","#ee7f11","#ed8210","#eb850e","#e9880d","#e88b0c","#e68e0a","#e49209","#e29508","#e09807","#de9b06","#dc9e05","#d9a104","#d7a403","#d5a703","#d2aa02","#d0ad02","#ceb001","#cbb301","#c9b600","#c6b800","#c3bb00","#c1be00","#bec100","#bbc300","#b8c600","#b6c900","#b3cb01","#b0ce01","#add002","#aad202","#a7d503","#a4d703","#a1d904","#9edc05","#9bde06","#98e007","#95e208","#92e409","#8ee60a","#8be80c","#88e90d","#85eb0e","#82ed10","#7fee11","#7cf013","#78f115","#75f317","#72f418","#6ff51a","#6cf61c","#69f71e","#66f920","#63f922","#60fa25","#5dfb27","#5afc29","#57fd2b","#54fd2e","#51fe30","#4efe33","#4bfe35","#48ff38","#45ff3a","#42ff3d","#40ff40","#3dff42","#3aff45","#38ff48","#35fe4b","#33fe4e","#30fe51","#2efd54","#2bfd57","#29fc5a","#27fb5d","#25fa60","#22f963","#20f966","#1ef769","#1cf66c","#1af56f","#18f472","#17f375","#15f178","#13f07c","#11ee7f","#10ed82","#0eeb85","#0de988","#0ce88b","#0ae68e","#09e492","#08e295","#07e098","#06de9b","#05dc9e","#04d9a1","#03d7a4","#03d5a7","#02d2aa","#02d0ad","#01ceb0","#01cbb3","#00c9b6","#00c6b8","#00c3bb","#00c1be","#00bec1","#00bbc3","#00b8c6","#00b6c9","#01b3cb","#01b0ce","#02add0","#02aad2","#03a7d5","#03a4d7","#04a1d9","#059edc","#069bde","#0798e0","#0895e2","#0992e4","#0a8ee6","#0c8be8","#0d88e9","#0e85eb","#1082ed","#117fee","#137cf0","#1578f1","#1775f3","#1872f4","#1a6ff5","#1c6cf6","#1e69f7","#2066f9","#2263f9","#2560fa","#275dfb","#295afc","#2b57fd","#2e54fd","#3051fe","#334efe","#354bfe","#3848ff","#3a45ff","#3d42ff","#4040ff","#423dff","#453aff","#4838ff","#4b35fe","#4e33fe","#5130fe","#542efd","#572bfd","#5a29fc","#5d27fb","#6025fa","#6322f9","#6620f9","#691ef7","#6c1cf6","#6f1af5","#7218f4","#7517f3","#7815f1","#7c13f0","#7f11ee","#8210ed","#850eeb","#880de9","#8b0ce8","#8e0ae6","#9209e4","#9508e2","#9807e0","#9b06de","#9e05dc","#a104d9","#a403d7","#a703d5","#aa02d2","#ad02d0","#b001ce","#b301cb","#b600c9","#b800c6","#bb00c3","#be00c1","#c100be","#c300bb","#c600b8","#c900b6","#cb01b3","#ce01b0","#d002ad","#d202aa","#d503a7","#d703a4","#d904a1","#dc059e","#de069b","#e00798","#e20895","#e40992","#e60a8e","#e80c8b","#e90d88","#eb0e85","#ed1082","#ee117f","#f0137c","#f11578","#f31775","#f41872","#f51a6f","#f61c6c","#f71e69","#f92066","#f92263","#fa2560","#fb275d","#fc295a","#fd2b57","#fd2e54","#fe3051","#fe334e","#fe354b","#ff3848","#ff3a45","#ff3d42","#ff4040"])
//     colorscale.value = color

//     const xAxis = d3.axisBottom()
//         .ticks(4)
//         .tickSize(size * 2)
    
//     const axisX = (g: any) => {
//         g.selectAll("g").data(x).join("g")
//         .attr("transform", (d: any, i: any) => `translate(${i * size},0)`)
//         .attr('data_type', 'xaxisinner')
//         .each(function(d: any) { 
//             return d3.select(this).call(xAxis.scale(d));
//         })
//         .call(g => g.select(".domain").remove())
//         .call(g => g.selectAll(".tick line").attr("stroke", "#ddd"));
//     }

//     const yAxis = d3.axisLeft()
//       .ticks(5)
//       .tickSize(-size * 2);

//     const axisY = g => g.selectAll("g").data(y).join("g")
//       .attr("transform", (d, i) => `translate(0,${i * size})`)
//       .attr('data_type', 'yaxisinner')
//       .each(function(d) { return d3.select(this).call(yAxis.scale(d)); })
//       .call(g => g.select(".domain").remove())
//       .call(g => g.selectAll(".tick line").attr("stroke", "#ddd"));
    
//     const svg = d3.create('svg')
//         .attr('viewBox', [-50,-50,1000,1000])
//         .style('height', 1200)
//         .style('width', 1200)

    
//     svg.append("style")
//       .text(`circle.hidden { fill: #000; fill-opacity: 1; r: 1px; }`);

//     svg.append("g")
//         .attr('data-id', 'xaxis')
//         .call(axisX);

//     svg.append("g")
//         .attr('data-id', 'yaxis')
//         .call(axisY);

        
    
//     const cell = svg.append("g")
//         .selectAll("g")
//         .data(d3.cross(d3.range(3), d3.range(2)))
//         .join("g")
//         .attr("transform", ([i, j]) => `translate(${i * size},${j * size})`)
//         .attr('data-id', ([i, j]) => `cell`)
//         // .attr('data-x', ([i, j]) => `${i * size}`)
//         // .attr('data-y', ([i, j]) => `${j * size}`)
//         // .attr('data-id', ([i, j]) => `${m([i, j])}`);


//     cell.append("rect")
//       .attr("fill", "none")
//       .attr("stroke", "#aaa")
//       .attr("x", padding / 2 + 0.5)
//       .attr("y", padding / 2 + 0.5)
//       .attr("width", size - padding)
//       .attr("height", size - padding);

    

//     cell.each(function([i, j]) {
//         d3.select(this).selectAll("circle")
//         .data(getFlatData(), datakey)
//         .join("circle")
//         .attr("cx", (d: DataElem) => x[i](d.avg_agi))
//         .attr("cy", (d: DataElem) => {
//             return y[j](getProportionateData(d, columns[enumerate(tupstr([i, j]))]))
//         })
//         .attr('data-id', (d: DataElem) => {
//             return `${d.county_name}-${d.state_name}`
//         })
//         // .on('mouseenter', (event: Event) => {
//         //     let targetX = d3.select(event.target)
//         //     .attr('cx')

//         //     let targetY = d3.select(event.target)
//         //     .attr('cy')
            
//         //     svg
//         //     .append('text')
//         //         .attr('x', targetX)
//         //         .attr('y', targetY)
//         //         .attr('dx', 0)
//         //         .attr('dy', 0)
//         //         .attr('class', 'small')
//         //         .attr('textLength', 50)
//         //         .text('Testing text')
//         // });
//     })
//     const circle = cell.selectAll("circle")
//       .attr("r", 3.5)
//       .attr("fill-opacity", 0.7)
//       .attr("fill", (d: DataElem) => {
//             if(group_by.value == 'division')
//                 return color(d.division)
//             else if(group_by.value == 'region')
//                 return color(d.region)
//             else
//                 return color(d.state_name)
//         });

    


//     // Ignore this line if you don't need the brushing behavior.
//     cell.call(brush, circle, svg, {padding, size, x, y, columns});

    
//     const reverseEnumeration = d3.scaleOrdinal(enumerate.range(), enumerate.domain())

//     svg.append("g")
//       .attr('data-type', 'labels')
//       .style("font", "bold 10px sans-serif")
//       .style("pointer-events", "none")
//       .selectAll('text')
//     .data(columns, (c) => c)
//     .join('foreignObject')
//         .attr("transform", (d, i) => {
//             let [x, y] = reverseEnumeration(i).split('-')
//             return `translate(${x * size},${(y * size)})`
//         })
        
//         .attr("x", padding)
//         .attr("y", padding)
//         .attr("dy", ".71em")
//         .attr('width', '200')
//         .attr('height', '100')
//         .attr('id', (d: string) => d)
//         .text((d: string) => `${d}`);

//     svg.property("value", [])
//     document.getElementById('plot')?.append(svg.node())
//     plot_displayed.value = true
//     root.value = svg
// }

// function updatePlot() {
//     const ordered_measures = 
//         Array.from(
//             all_measures
//             .value
//             .values()).sort((a, b) => a.localeCompare(b))
    
//     const columns = ordered_measures
//     const width = 600
//     const height = width
//     const padding = 20
//     const size = 300//(width - (2 + 1) * padding) / 4 + padding;
//     let svg = root.value

    
//     svg.select("g[data-type=labels]")
//       .attr('data-type', 'labels')
//       .style("font", "bold 10px sans-serif")
//       .style("pointer-events", "none")
//       .selectAll('text')
//     .data(columns, (c) => c)
//     .join('foreignObject')
        
//         .attr("transform", (d, i) => {
//             let [x, y] = reverseEnumeration(i).split('-')
//             return `translate(${x * size},${((y * size)-50)})`
//         })
//         .attr("x", padding)
//         .attr("y", padding)
//         .attr("dy", ".71em")
//         .attr('width', '200')
//         .attr('height', '100')
//         .attr('id', (d: string) => {
//             d
//         })
//         .text((d: string) => `${d}`);

//     const x = [1, 2, 3].map(m => {
//         let [min, max] = d3.extent(getFlatData(), (d: DataElem) => d.avg_agi)
//         return d3.scaleLinear()
//         .domain([10000, max*1.05])
//         .rangeRound([padding / 2, size - padding / 2])
//     })

//     const y = [1, 2].map(m => {
//         return d3.scaleLinear()
//         .domain([0.0, 1.1])
//         .range([size - padding / 2, padding / 2])
//     })
//     const xAxis = d3.axisBottom()
//         .ticks(4)
//         .tickSize(size * 2)
    
//     const axisX = (g: any) => {
//         g.selectAll("g[data_type=xaxisinner]").data(x).join("g")
//         .attr('data_type', 'xaxisinner')
//         .attr("transform", (d: any, i: any) => `translate(${i * size},0)`)
//         .each(function(d: any) { 
//             return d3.select(this).call(xAxis.scale(d));
//         })
//         .call(g => g.select(".domain").remove())
//         .call(g => g.selectAll(".tick line").attr("stroke", "#ddd"));
//     }

//     const yAxis = d3.axisLeft()
//       .ticks(5)
//       .tickSize(-size * 3);

//     const axisY = g => g.selectAll("g[data_type=yaxisinner]").data(y).join("g")
//       .attr("transform", (d, i) => `translate(0,${i * size})`)
//       .attr('data_type', 'yaxisinner')
//       .each(function(d) { return d3.select(this).call(yAxis.scale(d)); })
//       .call(g => g.select(".domain").remove())
//       .call(g => g.selectAll(".tick line").attr("stroke", "#ddd"));

//     let color_keys = Array.from(model.value.keys())
//     const color = d3.scaleOrdinal()
//         .domain(color_keys)
//         .range(["#1f77b4","#ff7f0e","#2ca02c","#d62728","#9467bd","#8c564b","#e377c2","#7f7f7f","#bcbd22","#17becf", "#8dd3c7","#ffffb3","#bebada","#fb8072","#80b1d3","#fdb462","#b3de69","#fccde5","#d9d9d9","#bc80bd","#ccebc5","#ffed6f", "#8dd3c7","#ffffb3","#bebada","#fb8072","#80b1d3","#fdb462","#b3de69","#fccde5","#d9d9d9","#bc80bd","#ccebc5","#ffed6f"])
//     colorscale.value = color
//     let cell = svg
//     .selectAll('g[data-id=cell]')
//     cell.each(function ([i, j]) {
//         d3.select(this).selectAll("circle")
//         .data(getFlatData().filter((d: DataElem) => d.measures.has( columns[enumerate(tupstr([i, j]))]) ), datakey)
//         .join("circle")
//         .attr("cx", (d: DataElem) => x[i](d.avg_agi))
//         .attr("cy", (d: DataElem) => {
//             return y[j](getProportionateData(d, columns[enumerate(tupstr([i, j]))]))
//         })
//         .attr('data-id', (d: DataElem) => {
//             return `${d.county_name}-${d.state_name}`
//         })
//         .attr("r", 3.5)
//         .attr("fill-opacity", 0.7)
//         .attr("fill", (d: DataElem) => {
//             if(group_by.value == 'division')
//                 return color(d.division)
//             else if(group_by.value == 'region')
//                 return color(d.region)
//             else
//                 return color(d.state_name)
//         });
//     })
//     const circle = cell.selectAll("circle")
//     cell.call(brush, circle, svg, {padding, size, x, y, columns});




  
    

//     svg.select("g[data-id=xaxis]")
//         .call(axisX);

//     svg.select("g[data-id=yaxis]")
//         .call(axisY);

//     // svg.select("g[data-type=labels]")
//     //   .style("font", "bold 10px sans-serif")
//     //   .style("pointer-events", "none")
//     // .selectAll("text")
//     // .data(columns, (c) => c)
//     // .join(labelEnter, labelUpdate, labelExit)
//     //     .attr("transform", (d, i) => {
//     //         let [x, y] = reverseEnumeration(i).split('-')
//     //         return `translate(${x * size},${y * size})`
//     //     })
//     //     .attr("x", padding)
//     //     .attr("y", padding)
//     //     .attr("dy", ".71em")
//     //     .attr('width', '200')
//     //     .attr('height', '100')
//     //     .attr('id', (d: string) => {
//     //         d
//     //     })
//     //     .text((d: string) => `${d}`);
// }

onMounted(() => {
    
    let query = `
    SELECT STATE_COUNTY_FIPS, GINI, STATE_NAME
    FROM cps_00004.county_gini
    JOIN cps_00004.county_fips
    ON county_gini.STATE_COUNTY_FIPS = county_fips.STATE_COUNTY_FIPS
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
        // socket.value.emit('query', state_fips_query, "state_fips")

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