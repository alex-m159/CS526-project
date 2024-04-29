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

let domain = `localhost`
let port = 9001
import { bivaraite_side_length, bivariate_colors, legend } from "@/utils/bivariate";



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

//@ts-ignore
let socket: Ref<Socket<ServerToClient, ClientToServer>> = ref(io(`ws://${domain}:${port}/`, {transports: ['websocket', 'polling']}));

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
let income_metric = ref('gini')
let income_metric_options = ref(['none', 'gini', 'agi'])

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
// This is used to tell us if the cluster scales (i.e. pnpScale, rnrScale, etc.) have been udpated to use
// the same income metric (Gini or AGI) as the unclustered scale. 
// It should match the agi_scale variable and if it doesn't then the
// scaleClusters will be updated the next time getColor is called.
let cluster_income_metric = ref('gini')
//
// A flag to temporarily show color for all the counties
// even when in the clustered view. 
let color_all_with_clusters = ref(false)

// This tells us the currently visualized health metric.
let health_metric = ref("none")
let health_metric_options = ref(new Set(['none']))
window.health_metric = health_metric
// The color scale for health metrics.
// Needs to be updated each time health_metric is changed
// since this is normalized discretization of health metric
// data values 
let healthScale = ref(null)
let healthLegend = ref(null)

// Used to ensure that the choosen health_metric and
// the healthScale are in sync. This follows the health metric
// used to construct the healthScale and if it's different
// than the health_metric then the healthScale should be updated.
let scaleHealthMetric = ref('none')


let bivariate_scale: Ref<any> = ref(null)
let bivariate_legend_income = ref(null)
let bivariate_legend_health = ref(null)

let bivariate_legend_zipped = ref([])

// This comes with the caveat that we can't use it in a v-if statement to determine if
// we should display the legend, but that's not too bad since we can just 
// check the income and health metrics individually
let bivariate_scale_metrics = ref({income_metric: 'none', health_metric: 'none'})


// For population density
let pop_metric = ref('none')
let pop_metric_options = ref(['none', 'rucc'])
let pop_scale = ref(null)
let pop_legend = ref(null)
let pop_scale_metric = ref('none')
let pop_scale_level = ref('states')

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

window.pickData = pickData

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
let cluster_plot_links = ref(null)
let cluster_plot_circles = ref(null)

function zoomed2(event: any) {
    const {transform} = event;
    cluster_plot_circles.value.attr("transform", transform)
    cluster_plot_links.value.attr("transform", transform)
}
let zoom = d3.zoom()
    .scaleExtent([0.1, 100])
    .on('zoom', zoomed)

let zoom2 = d3.zoom()
    .scaleExtent([1, 4])
    .translateExtent([[-Infinity,-300],[900,300]])
    .on('zoom', zoomed2)

function clicked(event, d) {
    const [[x0, y0], [x1, y1]] = path.bounds(d);
    event.stopPropagation();
    // d3.select(map_shapes.value).transition().style("fill", null);
    let fillcolor = d3.select(this).style('fill')
    console.log(fillcolor)
    d3.select(this).transition().style("fill", "yellow").transition().duration(1000).style('fill', `${fillcolor}`);
    // setTimeout(() => {
    //     d3.select(this).transition().duration(1000).style("fill", null);    
    // }, 300)
    svg.value.transition().duration(750).call(
        zoom.transform,
        d3.zoomIdentity
            .translate(width / 2, height / 2)
            .scale(Math.min(8, 0.7 / Math.max((x1 - x0) / width, (y1 - y0) / height)))
            .translate(-(x0 + x1) / 2, -(y0 + y1) / 2),
        d3.pointer(event, svg.value.node())
    );
}

function clickedCluster(event, d) {
    // const [[x0, y0], [x1, y1]] = path.bounds(d);
    console.log(d)
    console.log(event)
    d3.selectAll("circle[data-highlighted=true]").style("fill", "#555")
    let selection = d3.select(this)
    console.log(selection.attr("data-highlighted"))
    if(!selection.attr("data-highlighted") || selection.attr("data-highlighted") === false) {
        console.log("Filtering map values")
        selection.transition().style("fill", "yellow").attr("data-highlighted", true).attr("data-origcolor", selection.style("fill"))
        if(typeof d.data.data.id == "number") {

            let rucc = d.data.data.id
            console.log(rucc)
            map_shapes.value.style("fill", (d) => {
                if(d.properties.rucc !== rucc) {
                    return "#ccc"
                }
            })
        }
    } else {
        // selection.transition().style("fill", "yellow").attr("data-highlighted", true).attr("data-origcolor", selection.style("fill"))
        let orig = selection.attr("data-origcolor")
        selection.transition().style("fill", orig).attr("data-highlighted", undefined)  
        if(typeof d.data.data.id == "number") {

            let rucc = d.data.data.id
            map_shapes.value.style("fill", (d) => {
                if(false) {
                    return "#ccc"
                }
            })
        }
    }
    
    
    
    // event.stopPropagation();
    // map_shapes.value.transition().style("fill", null);
    // d3.select(this).transition().style("fill", "yellow");
    // setTimeout(() => {
    //     d3.select(this).transition().duration(1000).style("fill", null);    
    // }, 300)
    // svg.value.transition().duration(750).call(
    //     zoom.transform,
    //     d3.zoomIdentity
    //         .translate(width / 2, height / 2)
    //         .scale(Math.min(8, 0.7 / Math.max((x1 - x0) / width, (y1 - y0) / height)))
    //         .translate(-(x0 + x1) / 2, -(y0 + y1) / 2),
    //     d3.pointer(event, svg.value.node())
    // );
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
    if(income_metric.value == 'agi') {
        return d.properties.avg_agi
    } else {
        return d.properties.gini
    }
}

function getHealthMetric(d) {
    if(health_metric.value === 'none') {
        return 0
    } else {
        return d.properties.health_metrics.get(health_metric.value)
    }
}

function getPopMetric(d) {
    if(pop_metric.value === 'none') {
        return 0
    } else {
        return d.properties.rucc
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

    if(scaleClusters.value === null || cluster_income_metric.value !== income_metric.value) {
        let pnp_domain   = pickData("counties").filter(c => c.properties.group.has('pnp')).map(v => getIncomeMetric(v))
        let rnr_domain   = pickData("counties").filter(c => c.properties.group.has('rnr')).map(v => getIncomeMetric(v))
        let pnr_domain   = pickData("counties").filter(c => c.properties.group.has('pnr')).map(v => getIncomeMetric(v))
        let rnp_domain   = pickData("counties").filter(c => c.properties.group.has('rnp')).map(v => getIncomeMetric(v))
        let mixed_domain = pickData("counties").filter(c => c.properties.group.has('rnp') || c.properties.group.has('pnr')).map(v => getIncomeMetric(v))
        let full_domain  = pickData("counties").map(v => getIncomeMetric(v))
        var clusterScales;
        var clusterLegends;
        if(income_metric.value === 'agi') {
            clusterScales = {
                pnpScale: d3.scaleQuantile(pnp_domain, d3.schemeBlues[9]),
                rnrScale: d3.scaleQuantile(rnr_domain, d3.schemeBlues[9]),
                pnrScale: d3.scaleQuantile(pnr_domain, d3.schemeBlues[9]),
                rnpScale: d3.scaleQuantile(rnp_domain, d3.schemeBlues[9]),
                mixedScale: d3.scaleQuantile(mixed_domain, d3.schemeBlues[9]),
                fullScale: d3.scaleQuantile(full_domain, d3.schemeBlues[9]),
            }

            clusterLegends = {
                pnpLegend: getBuckets(pnp_domain.sort((a, b) => a-b), clusterScales.pnpScale),
                rnrLegend: getBuckets(rnr_domain.sort((a, b) => a-b), clusterScales.rnrScale),
                pnrLegend: getBuckets(pnr_domain.sort((a, b) => a-b), clusterScales.pnrScale),
                rnpLegend: getBuckets(rnp_domain.sort((a, b) => a-b), clusterScales.rnpScale),
                fullLegend: getBuckets(full_domain.sort((a, b) => a-b), clusterScales.fullScale),
            }
        } else {
            clusterScales = {
                pnpScale: d3.scaleQuantile(pnp_domain, d3.schemeReds[9]),
                rnrScale: d3.scaleQuantile(rnr_domain, d3.schemeReds[9]),
                pnrScale: d3.scaleQuantile(pnr_domain, d3.schemeReds[9]),
                rnpScale: d3.scaleQuantile(rnp_domain, d3.schemeReds[9]),
                mixedScale: d3.scaleQuantile(mixed_domain, d3.schemeReds[9]),
                fullScale: d3.scaleQuantile(full_domain, d3.schemeReds[9]),
            }
            clusterLegends = {
                pnpLegend: getBuckets(pnp_domain.sort((a, b) => a-b), clusterScales.pnpScale),
                rnrLegend: getBuckets(rnr_domain.sort((a, b) => a-b), clusterScales.rnrScale),
                pnrLegend: getBuckets(pnr_domain.sort((a, b) => a-b), clusterScales.pnrScale),
                rnpLegend: getBuckets(rnp_domain.sort((a, b) => a-b), clusterScales.rnpScale),
                fullLegend: getBuckets(full_domain.sort((a, b) => a-b), clusterScales.fullScale),
            }
        }
        
        scaleClusters.value = clusterScales
        legendClusters.value = clusterLegends
        window.legendClusters = legendClusters
        cluster_income_metric.value = income_metric.value
    }

    
    if(health_metric.value !== 'none' && health_metric.value !== scaleHealthMetric.value && income_metric.value == 'none') {
        
        let healthDomain = pickData().map((c) => c.properties.health_metrics.get(health_metric.value))//.filter(n => n !== undefined)
        window.healthDomain = healthDomain
        healthScale.value = d3.scaleQuantile(healthDomain, d3.schemePurples[9])
        window.healthScale = healthScale
        scaleHealthMetric.value = health_metric.value

        let hd_sorted = healthDomain.sort((a, b) => a-b)
        // scaleAGI.value = d3.scaleQuantile(pickData().map(v => v.properties.health_metrics.get(health_metric)), d3.schemeBlues[9])
        healthLegend.value = getBuckets(hd_sorted, healthScale.value).sort((a, b) => a[0] - b[0])
    }

    if(pop_metric.value !== 'none' && (pop_metric.value !== pop_scale_metric.value || pop_scale_level.value !== level.value)) {
       let pop_domain = pickData().map((c) => c.properties.rucc)
       pop_scale.value = d3.scaleQuantile(pop_domain, reverse(d3.schemeYlGn[9]))

       pop_scale_metric.value = pop_metric.value
       pop_scale_level.value = level.value

       let pd_sorted = pop_domain.sort((a, b) => a-b)
       // this will have a reverse sorted order compared to the other metrics since
       // low RUCC = high population density
       pop_legend.value = getBuckets(pd_sorted, pop_scale.value).sort((a, b) => b[0] - a[0])
    }

    if(income_metric.value !== 'none' && health_metric.value !== 'none' && ( bivariate_scale.value === null || bivariate_scale_metrics.value.income_metric !== income_metric.value || bivariate_scale_metrics.value.health_metric !== health_metric.value )) {
        let income_domain = pickData().map(v => getIncomeMetric(v)).sort((a, b) => a-b)
        let health_domain = pickData().map(v => getHealthMetric(v)).sort((a, b) => a-b)
        let income_scale = d3.scaleQuantile(income_domain, [0, 1, 2])
        let health_scale = d3.scaleQuantile(health_domain, [0, 1, 2])
        // Must accept two values from the domain as input and return a color value as output
        let _bivariate_scale = (income: number, health: number) => {
            let i = income_scale(income)
            let h = health_scale(health)
            return bivariate_colors[ h * bivaraite_side_length + i ]
        }
        bivariate_legend.value = legend(income_metric.value, 'Health Metric', income_scale.quantiles(), health_scale.quantiles())

        bivariate_legend_income.value = getBuckets(income_domain, (i) => _bivariate_scale(i, 0))
        bivariate_legend_health.value = getBuckets(health_domain, (h) => _bivariate_scale(0, h))
        bivariate_legend_zipped.value = d3.zip(bivariate_legend_income.value, bivariate_legend_health.value)
        bivariate_scale.value = _bivariate_scale
        bivariate_scale_metrics.value.income_metric = income_metric.value
        bivariate_scale_metrics.value.health_metric = health_metric.value
        
    }

    if(level.value === "counties") {
        if(cluster.value === "none") {
            if(income_metric.value === 'agi' && health_metric.value === 'none') {
                return scaleAGI.value(d.properties.avg_agi)
            } else if(income_metric.value === 'gini' && health_metric.value === 'none') {
                return scaleG.value(d.properties.gini)
            } else if(income_metric.value === 'none' && health_metric.value !== 'none') {
                return scaleHealthMetric.value(d.properties.health_metrics.get(health_metric.value))
            } else if(income_metric.value !== 'none' && health_metric.value !== 'none') {
                return bivariate_scale.value(getIncomeMetric(d), getHealthMetric(d))
            } else if(income_metric.value === 'none' && health_metric.value === 'none' && pop_metric.value !== 'none') {
                return pop_scale.value(getPopMetric(d))
            }
            
        }
        let focus_color = "yellow"
        let {pnpScale, rnrScale, pnrScale, rnpScale, mixedScale, fullScale} = scaleClusters.value
        // Use single scale coloring
        if(income_metric.value === 'none' || health_metric.value === 'none') {

            if(cluster.value === "pnp" && (d.properties.group.has('pnp') || color_all_with_clusters.value) ) {
                if(d.properties.focus.get('pnp') === true) {
                    return focus_color
                }
                if(color_all_with_clusters.value) {
                    return fullScale(getIncomeMetric(d))
                }
                return pnpScale(getIncomeMetric(d))
            }
            if(cluster.value === "rnr" && (d.properties.group.has("rnr") || color_all_with_clusters.value)) {
                if(d.properties.focus.get('rnr') === true) {
                    return focus_color
                }
                if(color_all_with_clusters.value) {
                    return fullScale(getIncomeMetric(d))
                }
                return rnrScale(getIncomeMetric(d))
            }
            if(cluster.value === "pnr" && (d.properties.group.has("pnr") || color_all_with_clusters.value)) {
                if(d.properties.focus.get('pnr') === true) {
                    return focus_color
                }
                if(color_all_with_clusters.value) {
                    return fullScale(getIncomeMetric(d))
                }
                return pnrScale(getIncomeMetric(d))
            }
            if(cluster.value === "rnp" && (d.properties.group.has("rnp") || color_all_with_clusters.value) ) {
                if(d.properties.focus.get('rnp') === true) {
                    return focus_color
                }
                if(color_all_with_clusters.value) {
                    return fullScale(getIncomeMetric(d))
                }
                return rnpScale(getIncomeMetric(d))
            }
        } else {
            // apply bivariate coloring
            if(d.properties.group.has(cluster.value) || color_all_with_clusters.value) {
                if(d.properties.focus.get(cluster.value) === true) {
                    return focus_color
                }
                return bivariate_scale.value(getIncomeMetric(d), getHealthMetric(d))
            }
            
        }

        return "#ccc"
    } else {
        if(income_metric.value === 'agi' && health_metric.value === 'none') {
            return scaleAGI.value(d.properties.avg_agi)
        } else if(income_metric.value === 'gini' && health_metric.value === 'none') {
            return scaleG.value(d.properties.gini)
        } else if(income_metric.value === 'none' && health_metric.value !== 'none') {
            return healthScale.value(d.properties.health_metrics.get(health_metric.value))
        } else if(income_metric.value !== 'none' && health_metric.value !== 'none') {
            return bivariate_scale.value(getIncomeMetric(d), getHealthMetric(d))
        } else if(income_metric.value === 'none' && health_metric.value === 'none' && pop_metric.value !== 'none') {
            return pop_scale.value(getPopMetric(d))
        }
    }
}

let bivariate_legend = ref(null)

function getTitle(d) {
    if(level.value == 'counties') {
        return `${d.properties.name}, ${d.properties.state} ( AGI: $${Math.floor(d.properties.avg_agi).toLocaleString(undefined, { minimumFractionDigits: 0 })} )`
    } else if(level.value == 'states') {
        return `${d.properties.name} ( AGI: $${Math.floor(d.properties.avg_agi).toLocaleString(undefined, {minimumFractionDigits: 0})})`
    }
    
}




let plotted = ref(false)
function showPlot() {
    if(plotted.value == true) {
        return
    }
    console.log("SHOW PLOT")
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
        .attr('data-tag', 'mapshape')

    map_shapes.value
        .selectAll('path[data-tag="mapshape"]')
        .append("title")
        .attr('data-tag', 'mapshapetitle')
        .text(d => getTitle(d));

    gg.value.append("path")
      .attr("fill", "none")
      .attr("stroke", "#333")
      .attr("stroke-linejoin", "round")
      .attr('data-tag', 'mapoutlinecounties')
      .style('visibility', 'hidden')
      .attr("d", path(pickMesh("counties")));

      gg.value.append("path")
      .attr("fill", "none")
      .attr("stroke", "#444")
      .attr("stroke-linejoin", "round")
      .attr("stroke-width", 1)
      .attr('data-tag', 'mapoutlinestates')
      .attr("d", path(pickMesh("states")));
      

    svg.value.call(zoom)
    if(document.getElementById('plot')?.childNodes.length == 0) {
        document.getElementById('plot')?.appendChild(svg.value.node())
        window.gg = gg
        plotted.value = true
        // let leg_svg = d3.create('svg').append(legend()).attr("transform", "translate(870,450)");
        
        // @ts-ignore
        // document.getElementById('scatter').innerHTML = legend()
    }


    
}

let display_stats = ref(false)
let stats_title = ref("")
let stats_covar = ref("")
let stats_corr = ref("")
function showStats(data: any) {

    let covar = data['covariance']
    let corr = data['correlation_coef']

    stats_title.value = `${income_metric.value} vs ${health_metric.value}`
    stats_covar.value = `Covariance: ${covar}`
    stats_corr.value = `Correlation Coefficient: ${(100*corr).toFixed(3)}`

    display_stats.value = true

}

function hideStats() {
    display_stats.value = false
}

/**
 * TODO: Must find a way to update the plot "in-place" rather than delete it 
 * to improve interactivity. When colors or scales are changed we don't want 
 * the plot to be unzoomed and recentered
 */
function updatePlot(clear?: boolean) {
    console.log("UPDATE PLOT")
    window.county_fill = county_fill
    window.state_fill = state_fill

    scaleG.value = null

    

    if(income_metric.value !== 'none' && income_metric.value !== 'none') {
        if(income_metric.value == 'agi') {
            let pairs: [number, number][] = pickData().map(mun => [mun.properties.avg_agi, mun.properties.health_metrics.get(health_metric.value)] ).filter((pair) => pair[0] !== NaN && pair[1] !== NaN)
            socket.value.emit('linear_regression', pairs)
        } 
        if(income_metric.value == 'gini') {
            let pairs: [number, number][] = pickData().map(mun => [mun.properties.gini, mun.properties.health_metrics.get(health_metric.value)] ).filter((pair) => pair[0] !== NaN && pair[1] !== NaN)
            socket.value.emit('linear_regression', pairs)
        }
        
        
    }
    
    

    map_shapes.value = gg.value
        .selectAll('path[data-tag="mapshape"]')
        .attr('fill', "#ccc")
        .data(pickData())
        .join('path')
            .attr('fill', '#ccc')
            .on('click', clicked)
            .attr('d', (g) => {
                return path(g)
            })
            .attr('data-tag', "mapshape")
            .attr('cursor', 'pointer')
            .transition()
            .ease(d3.easeCubicInOut)
            .delay(300)
            .duration(1000)
            .style('fill', (d) => getColor(d))

    gg.value
        .selectAll('path[data-tag="mapshape"]')
        .selectAll('title')
        .remove()

    gg.value
        .selectAll('path[data-tag="mapshape"]')
        .append("title")
        .text(d => {
            return getTitle(d)
        });
    
   
    if(level.value === `counties`) {
        gg.value.selectAll('path[data-tag="mapoutlinecounties"]')
        .transition()
        .duration(300)
        .delay(300)
        .style('visibility', 'visible')
        
        
        gg.value.selectAll('path[data-tag="mapoutlinestates"]')
        .transition()
        .duration(300)
        .style('visibility', 'hidden')
    } else {
        gg.value.selectAll('path[data-tag="mapoutlinecounties"]')
        .transition()
        .duration(300)
        .delay(300)
        .style('visibility', 'hidden')

        gg.value.selectAll('path[data-tag="mapoutlinestates"]')
        .transition()
        .duration(300)
        .style('visibility', 'visible')
    }
    
    // gg.value.selectAll('path[data-tag="mapoutlinestates"]')
    //   .attr("fill", "none")
    //   .attr("stroke", "#444")
    //   .attr("stroke-linejoin", "round")
    //   .attr("d", path(pickMesh("states")));
    
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

function ruralUrbanCodes() {
    socket.value.on('rural_urban_result', (data) => {
        if(data['name'] == 'state') {

            let kvs = data['data'].map((row) => {
                let state_fips = Number(row[0])
                let rucc = Number(row[1])
                return [state_fips, rucc]
            })
            let rucc_by_state: Map<number, number> = new Map(kvs)
            let with_rucc = state_fill.value.map((state) => {
                let s_fips = Number(state.id)
                if(rucc_by_state.has(s_fips)) {
                    let rucc = rucc_by_state.get(s_fips) as number
                    state.properties.rucc = rucc
                }
                return state
            })
            state_fill.value = with_rucc
        }
        if(data['name'] == 'county') {
            let kvs = data['data'].map((row) => {
                let county_fips = Number(row[1])
                let rucc = Number(row[2])
                return [county_fips, rucc]
            })
            let rucc_by_county: Map<number, number> = new Map(kvs)
            let with_rucc = county_fill.value.map((county) => {
                let c_fips = Number(county.id)
                if(rucc_by_county.has(c_fips)) {
                    let rucc = rucc_by_county.get(c_fips) as number
                    county.properties.rucc = rucc
                }
                return county
            })

            county_fill.value = with_rucc
            showClustering()
            
        }
    })

    socket.value.emit('rural_urban', 'state')
    socket.value.emit('rural_urban', 'county')

}

function showClustering() {
    let ruccToGroupName = (rucc: any) => {
        if(rucc == 1 || rucc == 2 || rucc == 3) {
            return `metro county`
        }
        if(rucc == 4 || rucc == 6 || rucc == 8) {
            return `metro adjacent`
        }
        if(rucc == 5 || rucc == 7 || rucc == 9) {
            return `metro non-adjacent`
        }
    }
    let filterRuccUndef = (cs: any[]) => {
        return cs.filter( (c) => c.properties.rucc !== undefined )
    }
    let no_undefs = () => filterRuccUndef(pickData("counties"))
    
    let base: any[] = [{'id': 'All Counties', 'parentId': undefined}]
    let layer2: any[] = [{'id': 'metro', 'parentId': 'All Counties'}, {'id': 'non-metro', 'parentId': 'All Counties'}]
    let layer3: any[] = [{'id': "metro county",  'parentId': "metro" }, {'id': "metro adjacent",  'parentId': "non-metro" }, {'id': "metro non-adjacent",  'parentId': "non-metro" }]
    let layer4: any[] = [1, 2, 3, 4, 5, 6, 7, 8, 9].map((r) => ({'id': r,  'parentId': ruccToGroupName(r) }))
    // let layer5: any[] = no_undefs().map((c) => ({'id': Number(c.id),  'parentId': c.properties.rucc }))
    let all_layers = base
    .concat(layer2)
    .concat(layer3)
    .concat(layer4)
    // .concat(layer5)

    window.all_layers = all_layers



    let strat1 = d3.stratify()(all_layers)
    
    let root = d3.hierarchy(strat1)

    const dx = 10;
    const dy = width / (root.height + 1);

    // Create a tree layout.
    const tree = d3.cluster().nodeSize([dx, dy]);

    // Sort the tree and apply the layout.
    root.sort((a, b) => d3.ascending(a.data.name, b.data.name));
    tree(root);

    // Compute the extent of the tree. Note that x and y are swapped here
    // because in the tree layout, x is the breadth, but when displayed, the
    // tree extends right rather than down.
    let x0 = Infinity;
    let x1 = -x0;
    root.each(d => {
        if (d.x > x1) x1 = d.x;
        if (d.x < x0) x0 = d.x;
    });

    // Compute the adjusted height of the tree.
    const height = x1 - x0 + dx * 2;

    window.root = root
    // Compute the adjusted height of the tree.
    // const height = x1 - x0 + dx * 2;

    const svg = d3.create("svg")
        .attr("width", width)
        .attr("height", height)
        .attr("viewBox", [-dy / 3, x0 - dx, "800", height])
        .attr("style", "max-width: 100%; height: 200px; font: 10px sans-serif;");

    let link_container = svg.append("g")
    cluster_plot_links.value = link_container

    const link = link_container
        .attr("fill", "none")
        .attr("stroke", "#555")
        .attr("stroke-opacity", 0.4)
        .attr("stroke-width", 1.5)
        .selectAll()
            .data(root.links())
            .join("path")
            .attr("d", d3.linkHorizontal()
                .x(d => d.y*0.4)
                .y(d => d.x*1.9));
    
    const container = svg.append("g")
    
    cluster_plot_circles.value = container
    const node = container
        .attr("stroke-linejoin", "round")
        .attr("stroke-width", 3)
    .selectAll()
    .data(root.descendants())
    .join("g")
        .attr("transform", d => `translate(${d.y*0.4},${d.x*1.9})`);

    node.append("circle")
        .attr("fill", d => d.children ? "#555" : "#555")
        .attr("r", 8.5)
        .on("click", clickedCluster);

    node.append("text")
        .attr("dy", "0.31em")
        .attr("font-size", "16")
        .attr("x", d => d.children ? -6 : 6)
        .attr("text-anchor", d => d.children ? "end" : "start")
        .attr('transform', "rotate(-10)")
        .text(d => d.data.id)
        .attr("stroke", "white")
        .attr("paint-order", "stroke");


    svg.call(zoom2)
    document.getElementById('cluster')?.append(svg.node())


}

onMounted(() => {
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
    SELECT STATE_FIPS, MEASURE, avg_data_value
    FROM (
            SELECT any(STATE_NAME) as STATE_NAME, MEASURE, avg(DATA_VALUE) as avg_data_value 
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

            if(data['end'] == true) {
                showPlot()
            }
                
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
            let reduced = data['data'].reduce(
                (acc: Map<number, Map<string, number>>, row: any[]) => { 
                    let county_fips = Number(row[0])
                    let measure = row[1]
                    let data_value = row[2]
                    if(!acc.has(county_fips)) {
                        acc.set(county_fips, new Map<string, number>())
                    }
                    let county_map = acc.get(county_fips)
                    county_map?.set(measure, data_value)
                    acc.set(county_fips, county_map)
                    return acc  
                }, new Map<number, Map<string, number>>())
            
            let with_health = county_fill.value.map((c) => {
                let sc_fips = Number(c.id)

                
                if(c.properties.health_metrics === undefined) {
                    c.properties.health_metrics = new Map<string, number>()
                }

                if(reduced.has(sc_fips)) {
                    let county_map = reduced.get(sc_fips) as [string, number]
                    c.properties.health_metrics = county_map
                    Array.from(county_map.keys()).forEach((measure) => {
                        health_metric_options.value.add(measure)
                    })
                }
                return c
            })
            county_fill.value = with_health
            // if(level.value === "counties") {
            //     updatePlot()
            // }
            ruralUrbanCodes()
        }

        if(data['name'] === 'health_state') {
            let reduced = data['data'].reduce(
                (acc: Map<number, Map<string, number>>, row: any[]) => { 
                    let state_fips = Number(row[0])
                    let measure = row[1]
                    let data_value = row[2]
                    if(!acc.has(state_fips)) {
                        acc.set(state_fips, new Map<string, number>())
                    }
                    let state_map = acc.get(state_fips)
                    state_map?.set(measure, data_value)
                    acc.set(state_fips, state_map)
                    return acc  
                }, new Map<number, Map<string, number>>())
            let with_health = state_fill.value.map((s) => {
                let s_fips = Number(s.id)


                if(s.properties.health_metrics === undefined) {
                    // this is overwritten for almost all states anyway, but keep this
                    // here for any states that do not show up in the query result.
                    // Helps make the frontend processing consistent later on
                    s.properties.health_metrics = new Map<string, number>()
                }

                if(reduced.has(s_fips)) {
                    let state_map = reduced.get(s_fips) as Map<string, number>
                    s.properties.health_metrics = state_map
                    Array.from(state_map.keys()).forEach((measure) => {
                        health_metric_options.value.add(measure)
                    })
                    
                }
                return s
            })
            state_fill.value = with_health
        }

    })
    socket.value.on('linear_regression_result', (data) => {
        showStats(data['data'])
    })
    fetch(`http://${domain}:${port}/counties-albers-10m.json`)
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
        
        socket.value.emit('query', query_state, "state")    
        socket.value.emit('query', query, "county")
        socket.value.emit('query', county_agi, "county_agi")
        socket.value.emit('query', state_agi, "state_agi")
        socket.value.emit('query', health_county_query, 'health_county')
        socket.value.emit('query', health_state_query, 'health_state')
    })
    
    

})

function doCluster() {
    scaleG.value = null
    scaleClusters.value = null
    countyComparisons()
}

function updateIncomeMetric(e: Event) {
    let im = e.target.value
    income_metric.value = im
    updatePlot()
}

function colorAllMouseDown() {
    console.log("colorAllMouseDown")
    color_all_with_clusters.value = true
    updatePlot()
}

function colorAllMouseUp() {
    console.log('colorAllMouseUp')
    color_all_with_clusters.value = false
    updatePlot()
}

function updatePlotLevel() {
    updatePlot(true)
}
</script>
<template>
    <div class="row">
        <div class="col-md-9" id="plot"></div>
        <!-- <div class="col-md-9" id="cluster"></div> -->
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
                        <div class="row my-2">
                            <p>County Clustering:</p>
                            <select class="form-select " v-if="level == 'counties'" v-model="cluster" @click="doCluster">
                                <option key="none" value="none">No Clusters</option>
                                <option key="pnp" value="pnp">Poor Near Poor</option>
                                <option key="rnr" value="rnr">Rich Near Rich</option>
                                <option key="rnp" value="rnp">Rich Near Poor</option>
                                <option key="pnr" value="pnr">Poor Near Rich</option>
                            </select>
                            <select class="form-select" v-else v-model="cluster" disabled>
                                <option key="none" value="none">No Clusters</option>
                                <option key="pnp" value="pnp">Poor Near Poor</option>
                                <option key="rnr" value="rnr">Rich Near Rich</option>
                                <option key="rnp" value="rnp">Rich Near Poor</option>
                                <option key="pnr" value="pnr">Poor Near Rich</option>
                            </select>
                        </div>
                        <div v-if="cluster !== 'none'" class="row my-2">
                            <button 
                                class="btn btn-outline-primary" 
                                @mousedown="colorAllMouseDown" 
                                @mouseup="colorAllMouseUp"
                                @mouseleave="colorAllMouseUp">Color All</button>
                            
                        </div>
                        <div class="row my-3">
                            
                            <select class="form-select" v-model="income_metric" @click="updateIncomeMetric">
                                <option v-for="metric in income_metric_options" :value="metric" :key="metric">
                                    {{ metric }}
                                </option>
                            </select>
                        </div>
                        
                        <div class="row">
                            <p>Health Metric:</p>
                            <select class="form-select" v-model="health_metric" @click="updatePlot">
                                <option v-for="metric in Array.from(health_metric_options.values())" :value="metric">{{ metric }}</option>
                            </select>
                        </div>
                        <!--
                        <div class="row">
                            <p>Population Density Metric:</p>
                            <select class="form-select" v-model="pop_metric" @click="updatePlot">
                                <option v-for="metric in Array.from(pop_metric_options.values())" :value="metric">{{ metric }}</option>
                            </select>
                        </div>
                        <div id="cluster" style="height: 200px">

                        </div>
                        <div class="row my-3">
                            <button class="btn btn-outline-danger" @click="reset()">Reset</button>
                        </div>
                        -->
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
                            <div v-if="income_metric == 'agi' && cluster == 'none' && health_metric === 'none'">
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
                            <div v-if="income_metric == 'gini' && cluster == 'none' && health_metric === 'none'">
                                <p>Gini Coefficient:</p>
                                <div v-for="elem in legendG">
                                    <span class="d-inline-block">
                                        <div class="d-flex" :style="{backgroundColor: elem[2], height: '1em', width: '1em'}"></div>
                                    </span>
                                    <span class="d-inline mx-3" v-if="income_metric === 'agi'">{{ '$' + (elem[0]/1000).toFixed(0) + 'k' }}</span>
                                    <span class="d-inline mx-2" v-else>{{ elem[0].toFixed(3) }}</span>
                                    <span class="d-inline mx-1"> - </span>
                                    <span class="d-inline mx-2" v-if="income_metric === 'agi'">{{ '$' + (elem[1]/1000).toFixed(0) + 'k' }}</span>
                                    <span class="d-inline mx-2" v-else>{{ elem[1].toFixed(3) }}</span>
                                </div>
                            </div>
                            <div v-if="cluster == 'pnp' && !color_all_with_clusters">
                                <p>Cluster-specific Scale</p>
                                <p v-if="income_metric == 'agi'">Adjusted Gross Income (AGI):</p>
                                <p v-else>Gini Coefficient:</p>
                                <div v-for="elem in legendClusters.pnpLegend">
                                    <span class="d-inline-block">
                                        <div class="d-flex" :style="{backgroundColor: elem[2], height: '1em', width: '1em'}"></div>
                                    </span>
                                    <span class="d-inline mx-3" v-if="income_metric === 'agi'">{{ '$' + (elem[0]/1000).toFixed(0) + 'k' }}</span>
                                    <span class="d-inline mx-2" v-else>{{ elem[0].toFixed(3) }}</span>
                                    <span class="d-inline mx-1"> - </span>
                                    <span class="d-inline mx-2" v-if="income_metric === 'agi'">{{ '$' + (elem[1]/1000).toFixed(0) + 'k' }}</span>
                                    <span class="d-inline mx-2" v-else>{{ elem[1].toFixed(3) }}</span>
                                </div>
                            </div>
                            <div v-if="cluster == 'rnr' && !color_all_with_clusters">
                                <p>Cluster-specific Scale</p>
                                <p v-if="income_metric == 'agi'">Adjusted Gross Income (AGI):</p>
                                <p v-else>Gini Coefficient:</p>
                                <div v-for="elem in legendClusters.rnrLegend">
                                    <span class="d-inline-block">
                                        <div class="d-flex" :style="{backgroundColor: elem[2], height: '1em', width: '1em'}"></div>
                                    </span>
                                    <span class="d-inline mx-3" v-if="income_metric === 'agi'">{{ '$' + (elem[0]/1000).toFixed(0) + 'k' }}</span>
                                    <span class="d-inline mx-2" v-else>{{ elem[0].toFixed(3) }}</span>
                                    <span class="d-inline mx-1"> - </span>
                                    <span class="d-inline mx-2" v-if="income_metric === 'agi'">{{ '$' + (elem[1]/1000).toFixed(0) + 'k' }}</span>
                                    <span class="d-inline mx-2" v-else>{{ elem[1].toFixed(3) }}</span>
                                </div>
                            </div>
                            <div v-if="cluster == 'pnr' && !color_all_with_clusters">
                                <p>Cluster-specific Scale</p>
                                <p v-if="income_metric == 'agi'">Adjusted Gross Income (AGI):</p>
                                <p v-else>Gini Coefficient:</p>
                                <div v-for="elem in legendClusters.pnrLegend">
                                    <span class="d-inline-block">
                                        <div class="d-flex" :style="{backgroundColor: elem[2], height: '1em', width: '1em'}"></div>
                                    </span>
                                    <span class="d-inline mx-3" v-if="income_metric === 'agi'">{{ '$' + (elem[0]/1000).toFixed(0) + 'k' }}</span>
                                    <span class="d-inline mx-2" v-else>{{ elem[0].toFixed(3) }}</span>
                                    <span class="d-inline mx-1"> - </span>
                                    <span class="d-inline mx-2" v-if="income_metric === 'agi'">{{ '$' + (elem[1]/1000).toFixed(0) + 'k' }}</span>
                                    <span class="d-inline mx-2" v-else>{{ elem[1].toFixed(3) }}</span>
                                </div>
                            </div>
                            <div v-if="cluster == 'rnp' && !color_all_with_clusters">
                                <p>Cluster-specific Scale</p>
                                <p v-if="income_metric == 'agi'">Adjusted Gross Income (AGI):</p>
                                <p v-else>Gini Coefficient:</p>
                                <div v-for="elem in legendClusters.rnpLegend">
                                    <span class="d-inline-block">
                                        <div class="d-flex" :style="{backgroundColor: elem[2], height: '1em', width: '1em'}"></div>
                                    </span>
                                    <span class="d-inline mx-3" v-if="income_metric === 'agi'">{{ '$' + (elem[0]/1000).toFixed(0) + 'k' }}</span>
                                    <span class="d-inline mx-2" v-else>{{ elem[0].toFixed(3) }}</span>
                                    <span class="d-inline mx-1"> - </span>
                                    <span class="d-inline mx-2" v-if="income_metric === 'agi'">{{ '$' + (elem[1]/1000).toFixed(0) + 'k' }}</span>
                                    <span class="d-inline mx-2" v-else>{{ elem[1].toFixed(3) }}</span>
                                </div>
                            </div>
                            <div v-if="color_all_with_clusters">
                                <p>Global Scale</p>
                                <p v-if="income_metric == 'agi'">Adjusted Gross Income (AGI):</p>
                                <p v-else>Gini Coefficient:</p>
                                <div v-for="elem in legendClusters.fullLegend">
                                    <span class="d-inline-block">
                                        <div class="d-flex" :style="{backgroundColor: elem[2], height: '1em', width: '1em'}"></div>
                                    </span>
                                    <span class="d-inline mx-3" v-if="income_metric === 'agi'">{{ '$' + (elem[0]/1000).toFixed(0) + 'k' }}</span>
                                    <span class="d-inline mx-2" v-else>{{ elem[0].toFixed(3) }}</span>
                                    <span class="d-inline mx-1"> - </span>
                                    <span class="d-inline mx-2" v-if="income_metric === 'agi'">{{ '$' + (elem[1]/1000).toFixed(0) + 'k' }}</span>
                                    <span class="d-inline mx-2" v-else>{{ elem[1].toFixed(3) }}</span>
                                </div>
                            </div>
                            <div v-if="income_metric === 'none' && health_metric !== 'none'">
                                <p>Health Metric:</p>
                                <p>{{ health_metric }}</p>
                                <div v-for="elem in healthLegend">
                                    <span class="d-inline-block">
                                        <div class="d-flex" :style="{backgroundColor: elem[2], height: '1em', width: '1em'}"></div>
                                    </span>
                                    <span class="d-inline mx-2">{{ elem[0].toFixed(1) }}%</span>
                                    <span class="d-inline mx-1"> - </span>
                                    <span class="d-inline mx-2">{{ elem[1].toFixed(1) }}%</span>
                                </div>
                            </div>
                            <div v-if="pop_metric !== 'none'">
                                <p v-if="level == 'counties'">Population Density (RUCC):</p>
                                <p v-else>Population Density (Weighted RUCC Avg.):</p>
                                <div v-for="elem in pop_legend">
                                    <span class="d-inline-block">
                                        <div class="d-flex" :style="{backgroundColor: elem[2], height: '1em', width: '1em'}"></div>
                                    </span>
                                    <span v-if="level == 'states'">
                                        <span class="d-inline mx-2">{{ elem[0].toFixed(2) }}</span>
                                        <span class="d-inline mx-1"> - </span>
                                        <span class="d-inline mx-2">{{ elem[1].toFixed(2) }}</span>
                                    </span>
                                    <span v-if="level == 'counties'">
                                        <span class="d-inline mx-2">{{ elem[0] }}</span>
                                    </span>
                                </div>
                            </div>

                            <div v-if="income_metric !== 'none' && health_metric !== 'none'">
                                <div class="row">
                                    <span class="col-md-6">{{ income_metric }}</span>
                                    <span class="col-md-6">Health</span>
                                </div>
                                <div class="row" v-for="elem in bivariate_legend_zipped">
                                    <!-- INCOME/X AXIS COLORS -->
                                    <div class="col-md-6">
                                        <span class="d-inline-block">
                                            <div class="d-flex" :style="{backgroundColor: elem[0][2], height: '1em', width: '1em'}"></div>
                                        </span>
                                        <span class="d-inline mx-3" v-if="income_metric === 'agi'">{{ '$' + (elem[0][0]/1000).toFixed(0) + 'k' }}</span>
                                        <span class="d-inline mx-2" v-else>{{ elem[0][0].toFixed(3) }}</span>
                                        <span class="d-inline mx-1"> - </span>
                                        <span class="d-inline mx-2" v-if="income_metric === 'agi'">{{ '$' + (elem[0][1]/1000).toFixed(0) + 'k' }}</span>
                                        <span class="d-inline mx-2" v-else>{{ elem[0][1].toFixed(3) }}</span>
                                    </div>
                                    <!-- HEALTH/Y AXIS COLORS -->
                                    <div class="col-md-6">
                                        <span class="d-inline-block">
                                            <div class="d-flex" :style="{backgroundColor: elem[1][2], height: '1em', width: '1em'}"></div>
                                        </span>
                                        <span class="d-inline mx-2">{{ elem[1][0].toFixed(1) }}%</span>
                                        <span class="d-inline mx-1"> - </span>
                                        <span class="d-inline mx-2">{{ elem[1][1].toFixed(1) }}%</span>
                                    </div>
                                </div>
                            </div>
                            <!-- Bivariate Legend -->
                            <div v-if="income_metric !== 'none' && health_metric !== 'none'" v-html="bivariate_legend">
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
                        <div v-if="display_stats">
                            <div id="stats-title">
                                {{ stats_title }}
                            </div>
                            <div id="covariance">
                                {{ stats_covar }}
                            </div>
                            <div id="correlation_coef">
                                {{ stats_corr }}
                            </div>
                        </div>
                    </div>
                    </div>
                </div>
            </div>
           
            
        </div>
    </div>
</template>
