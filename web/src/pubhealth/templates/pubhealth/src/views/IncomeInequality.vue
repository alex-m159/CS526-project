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
import * as turf from "@turf/turf"



interface ClientToServer {
    query: (query: string, name: string) => string
    setup: (query: string) => string
}

interface ServerToClient {
    data: (data: {data: any[], end: boolean}) => any
    setup: (data: {data: any[]}) => any 
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

// function showPlot() {
//     const width = 1000;
//   const height = 610;

//   const zoom = d3.zoom()
//       .scaleExtent([1, 8])
//       .on("zoom", zoomed);

//   const svg = d3.create("svg")
//       .attr("viewBox", [0, 0, width, height])
//        .attr("width", width)
//       .attr("height", height)
//       .attr("style", "max-width: 100%; height: auto;")
//       .on("click", reset);

//   const path = d3.geoPath();

//   const g = svg.append("g");

//   const states = g.append("g")
//       .attr("fill", "#444")
//       .attr("cursor", "pointer")
//     .selectAll("path")
//     .data(topojson.feature(geojson.value, geojson.value.objects.counties).features)
//     .join("path")
//       .on("click", clicked)
//       .attr("d", path);
  
//   states.append("title")
//       .text(d => d.properties.name);

//   g.append("path")
//       .attr("fill", "none")
//       .attr("stroke", "white")
//       .attr("stroke-linejoin", "round")
//       .attr("d", path(topojson.mesh(geojson.value, geojson.value.objects.counties, (a, b) => a !== b)));

//   svg.call(zoom);

//   function reset() {
//     states.transition().style("fill", null);
//     svg.transition().duration(750).call(
//       zoom.transform,
//       d3.zoomIdentity,
//       d3.zoomTransform(svg.node()).invert([width / 2, height / 2])
//     );
//   }

//   function clicked(event, d) {
//     const [[x0, y0], [x1, y1]] = path.bounds(d);
//     event.stopPropagation();
//     states.transition().style("fill", null);
//     d3.select(this).transition().style("fill", "red");
//     svg.transition().duration(750).call(
//       zoom.transform,
//       d3.zoomIdentity
//         .translate(width / 2, height / 2)
//         .scale(Math.min(8, 0.9 / Math.max((x1 - x0) / width, (y1 - y0) / height)))
//         .translate(-(x0 + x1) / 2, -(y0 + y1) / 2),
//       d3.pointer(event, svg.node())
//     );
//   }

//   function zoomed(event) {
//     const {transform} = event;
//     g.attr("transform", transform);
//     g.attr("stroke-width", 1 / transform.k);
//   }

//     if(document.getElementById('plot')?.childNodes.length == 0) {
//         document.getElementById('plot')?.appendChild(svg.node())
//     }
// }
let county_fill = ref(null)
let state_fill = ref(null)

let level = ref("counties")
function pickData() {
    if(level.value === "counties") {
        return county_fill.value
    } else {
        return state_fill.value
    }
}

let county_mesh = ref(null)
let state_mesh = ref(null)



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
function zoomed(event: any) {
    const {transform} = event;
    gg.value.attr("transform", transform);
    gg.value.attr("stroke-width", Math.min(1 / transform.k, 1));
}
let zoom = d3.zoom()
    .scaleExtent([0.1, 100])
    .on('zoom', zoomed)

let path = d3.geoPath()



function clicked(event, d) {
    const [[x0, y0], [x1, y1]] = path.bounds(d);
    event.stopPropagation();
    map_shapes.value.transition().style("fill", null);
    d3.select(this).transition().style("fill", "red");
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

function showPlot() {
    console.log('Running showPlot')
    // setting to null returns SVG render
    

    window.d3 = d3
    let scale = d3.scaleQuantile(pickData().map(v => v.properties.gini), d3.schemeReds[9])

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
            .attr('fill', (d) => scale(d.properties.gini))
            .on('click', clicked)
            .attr('d', (g) => {
                return path(g)
        })

    map_shapes.value.append("title")
        .text(d => level.value == "counties" ? `${d.properties.name}, ${d.properties.state}` : `${d.properties.name}`);

    gg.value.append("path")
      .attr("fill", "none")
      .attr("stroke", "white")
      .attr("stroke-linejoin", "round")
      .attr("d", path(pickMesh()));

      gg.value.append("path")
      .attr("fill", "none")
      .attr("stroke", "black")
      .attr("stroke-linejoin", "round")
      .attr("stroke-width", 1)
      .attr("d", path(pickMesh("states")));
      

    svg.value.call(zoom)
    if(document.getElementById('plot')?.childNodes.length == 0) {
        document.getElementById('plot')?.appendChild(svg.value.node())
    }


    
}
function updatePlot() {
    gg.value.remove()
    map_shapes.value.remove()

    gg.value = svg.value.append('g')
    let scale = d3.scaleQuantile(pickData().map(v => v.properties.gini), d3.schemeReds[9])

    map_shapes.value = gg.value
        .append('g')
        .attr('fill', "#ccc")
        .attr('cursor', 'pointer')
        .selectAll('path')
        .data(pickData())
        .join('path')
            .attr('fill', (d) => scale(d.properties.gini))
            .on('click', clicked)
            .attr('d', (g) => {
                return path(g)
        })
   
    map_shapes.value.append("title")
      .text(d => level.value == "counties" ? `${d.properties.name}, ${d.properties.state}` : `${d.properties.name}`);
   
    
    

    gg.value.append("path")
      .attr("fill", "none")
      .attr("stroke", "white")
      .attr("stroke-linejoin", "round")
      .attr("d", path(pickMesh()));
    
    gg.value.append("path")
      .attr("fill", "none")
      .attr("stroke", "black")
      .attr("stroke-linejoin", "round")
      .attr("stroke-width", 1)
      .attr("d", path(pickMesh("states")));
}


onMounted(() => {
    logger.debug("Taxation Component Mounted")
    
    // socket.value = io(`wss://hub.publichealthhq.xyz:9000/`, {transports: ['websocket', 'polling']});
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
    
    fetch(`http://localhost:9001/counties-albers-10m.json`)
    .then((res) => {
        
        return res.json()
    })
    .then((json) => {
        console.log(json)
        geojson.value = json
        
        socket.value.emit('query', query, "county")
        county_mesh.value   = topojson.mesh(geojson.value, geojson.value.objects.counties, (a, b) => a !== b)
        window.county_mesh = county_mesh
        state_mesh.value    = topojson.mesh(geojson.value, geojson.value.objects.states, (a, b) => a !== b)   
        window.state_mesh = state_mesh
        county_fill.value   = topojson.feature(geojson.value, geojson.value.objects.counties).features
        window.county_fill = county_fill
        state_fill.value    = topojson.feature(geojson.value, geojson.value.objects.states).features
        window.state_fill = state_fill

        console.log("asldjasd")

        
    })
    
    
    
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
            console.log(with_gini)
            county_fill.value = with_gini

            console.log("asdad")
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
            // console.log(with_gini)
            state_fill.value = with_gini

            console.log("asdad")
            if(data['end'] == true) 
                showPlot()
        }
        
    })


    

})

function buf() {
    // console.log(geojson.value)
    let tg = topojson.feature(geojson.value, geojson.value.objects.states)

    let buffed = 
        tg.features.map((s) => {
            try {
                if(s.properties.state == "New Jersey" || s.properties.state == "New York" || s.properties.state == "Pennsylvania") {
                    let b = turf.transformScale(s, 1.2, {units: 'miles'})
                    return b
                }
                let b = turf.transformScale(s, 200.0, {units: 'miles'})
                b.id = s.id
                return s
                // return s
            } catch (err) {
                console.log(err)
                return s
            }
        })
    
    // console.log(buffed)
    state_fill.value = buffed
    // state_fill.value = topojson.feature(geojson.value, geojson.value.objects.states).features
    updatePlot()
    // console.log(geojson.value)
}


</script>
<template>
    <div class="row">
        <div class="col-md-9" id="plot"></div>
        <div class="col-md-3">
            <div class="row">
                <label>Group By:</label>
                <select class="form-select" v-model="level" @change="updatePlot">
                    <option key="counties" value="counties">counties</option>
                    <option key="states" value="states">states</option>
                </select>
            </div>
            <div class="row">
                <button class="btn btn-primary" @click="reset()">Reset</button>
            </div>
        </div>
    </div>
</template>