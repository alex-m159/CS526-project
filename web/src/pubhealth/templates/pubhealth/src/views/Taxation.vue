<script setup lang="ts">
import { ref, onMounted, onUnmounted } from "vue";
import { logger } from '../utils/logging';
import type { Ref } from "vue";
import { io, Socket } from "socket.io-client";
//@ts-ignore
import * as d3 from "d3";

interface ClientToServer {
    query: (query: string) => string
}

interface ServerToClient {
    data: (data: {data: any[]}) => any
}

interface DataElem {
    avg_agi: number,
    avg_tax: number,
    state_name: string,
    county_name: string,
    measures: Map<string, number>
}

let socket: Ref<Socket<ServerToClient, ClientToServer> | null> = ref(null)
let model: Ref<Map<string, Map<string, DataElem>>> = ref(new Map())
let all_measures: Ref<Set<string>> = ref(new Set())
let max_measure: Ref<Map<string, number>> = ref(new Map())
let plot_displayed: Ref<boolean> = ref(false)

function getFlatData() {
    return Array.from(model.value.values()).flatMap((map) => Array.from(map.values()))
}
function getProportionateData(d: DataElem, measure: string) {
    return ((d.measures.get(measure) as number) / (max_measure.value.get(measure) as number))
}

const root: Ref<any> = ref(null)
const tupstr = (tup: [number, number]) => {return `${tup[0]}-${tup[1]}`}
const datakey = (d: DataElem) => {return `${d.state_name}-${d.county_name}`}
const enumerate = d3.scaleOrdinal()
    .domain(d3.cross(d3.range(3), d3.range(2)).map(tupstr))
    .range([0, 1, 2, 3, 4, 5])


const reverseEnumeration = d3.scaleOrdinal(enumerate.range(), enumerate.domain())

function brush(cell: any, circle: any, svg: any, {padding, size, x, y, columns}: any) {
    const brush = d3.brush()
        .extent([[padding / 2, padding / 2], [size - padding / 2, size - padding / 2]])
        .on("start", brushstarted)
        .on("brush", brushed)
        .on("end", brushended);

    cell.call(brush);

    let brushCell: any;

    // Clear the previously-active brush, if any.
    function brushstarted() {
        //@ts-ignore
        if (brushCell !== this) {
        d3.select(brushCell).call(brush.move, null);
        //@ts-ignore
        brushCell = this;
        }
    }

    // Highlight the selected circles.
    function brushed({selection}: any, [i, j]: any) {
        let selected: any[] = [];
        if (selection) {
        const [[x0, y0], [x1, y1]] = selection; 
        circle.classed("hidden",
            (d: DataElem) => x0 > x[i](d.avg_agi)
            || x1 < x[i](d.avg_agi)
            || y0 > y[j]( getProportionateData(d, columns[enumerate(tupstr([i, j]))]))
            || y1 < y[j]( getProportionateData(d, columns[enumerate(tupstr([i, j]))])  ));
        selected = getFlatData().filter(
            (d: DataElem) => x0 < x[i](d.avg_agi)
            && x1 > x[i](d.avg_agi)
            && y0 < y[j](getProportionateData(d, columns[enumerate(tupstr([i, j]))]))
            && y1 > y[j](getProportionateData(d, columns[enumerate(tupstr([i, j]))])));
        }
        svg.property("value", selected).dispatch("input");
    }

    // If the brush is empty, select all circles.
    function brushended({selection}: any) {
        if (selection) return;
        svg.property("value", []).dispatch("input");
        circle.classed("hidden", false);
    }
}

function showPlot() {
    if(plot_displayed.value) {
        return;
    }
    const ordered_measures = 
        Array.from(
            all_measures
            .value
            .values()).sort((a, b) => a.localeCompare(b))
    const columns = ordered_measures
    const width = 600
    const height = width
    const padding = 20
    const size = 300//(width - (3 + 1) * padding) / 2 + padding

    const measures = Array.from(all_measures.value.values())
    const x = measures.map(m => {
        return d3.scaleLinear()
        .domain(d3.extent(Array.from(model.value.values()).flatMap((map) => Array.from(map.values())), (d: DataElem) => d.avg_agi))
        .rangeRound([padding / 2, size - padding / 2])
    })

    const y = measures.map(m => {
        return d3.scaleLinear()
        .domain([0.0, 1.0])
        .range([size - padding / 2, padding / 2])
    })

    
    
    String.prototype.hashCode = function() {
        var hash = 0,
            i, chr;
        if (this.length === 0) return hash;
        for (i = 0; i < this.length; i++) {
            chr = this.charCodeAt(i);
            hash = ((hash << 5) - hash) + chr;
            hash |= 0; // Convert to 32bit integer
        }
        return hash;
    }

    const color = d3.scaleOrdinal()
        .domain(getFlatData().sort((a, b) => a.state_name.localeCompare(b.state_name)).map((d: DataElem, i) => d.state_name))
        .range(["#1f77b4","#ff7f0e","#2ca02c","#d62728","#9467bd","#8c564b","#e377c2","#7f7f7f","#bcbd22","#17becf", "#8dd3c7","#ffffb3","#bebada","#fb8072","#80b1d3","#fdb462","#b3de69","#fccde5","#d9d9d9","#bc80bd","#ccebc5","#ffed6f", "#8dd3c7","#ffffb3","#bebada","#fb8072","#80b1d3","#fdb462","#b3de69","#fccde5","#d9d9d9","#bc80bd","#ccebc5","#ffed6f"])
        // .range(["#ff4040","#ff423d","#ff453a","#ff4838","#fe4b35","#fe4e33","#fe5130","#fd542e","#fd572b","#fc5a29","#fb5d27","#fa6025","#f96322","#f96620","#f7691e","#f66c1c","#f56f1a","#f47218","#f37517","#f17815","#f07c13","#ee7f11","#ed8210","#eb850e","#e9880d","#e88b0c","#e68e0a","#e49209","#e29508","#e09807","#de9b06","#dc9e05","#d9a104","#d7a403","#d5a703","#d2aa02","#d0ad02","#ceb001","#cbb301","#c9b600","#c6b800","#c3bb00","#c1be00","#bec100","#bbc300","#b8c600","#b6c900","#b3cb01","#b0ce01","#add002","#aad202","#a7d503","#a4d703","#a1d904","#9edc05","#9bde06","#98e007","#95e208","#92e409","#8ee60a","#8be80c","#88e90d","#85eb0e","#82ed10","#7fee11","#7cf013","#78f115","#75f317","#72f418","#6ff51a","#6cf61c","#69f71e","#66f920","#63f922","#60fa25","#5dfb27","#5afc29","#57fd2b","#54fd2e","#51fe30","#4efe33","#4bfe35","#48ff38","#45ff3a","#42ff3d","#40ff40","#3dff42","#3aff45","#38ff48","#35fe4b","#33fe4e","#30fe51","#2efd54","#2bfd57","#29fc5a","#27fb5d","#25fa60","#22f963","#20f966","#1ef769","#1cf66c","#1af56f","#18f472","#17f375","#15f178","#13f07c","#11ee7f","#10ed82","#0eeb85","#0de988","#0ce88b","#0ae68e","#09e492","#08e295","#07e098","#06de9b","#05dc9e","#04d9a1","#03d7a4","#03d5a7","#02d2aa","#02d0ad","#01ceb0","#01cbb3","#00c9b6","#00c6b8","#00c3bb","#00c1be","#00bec1","#00bbc3","#00b8c6","#00b6c9","#01b3cb","#01b0ce","#02add0","#02aad2","#03a7d5","#03a4d7","#04a1d9","#059edc","#069bde","#0798e0","#0895e2","#0992e4","#0a8ee6","#0c8be8","#0d88e9","#0e85eb","#1082ed","#117fee","#137cf0","#1578f1","#1775f3","#1872f4","#1a6ff5","#1c6cf6","#1e69f7","#2066f9","#2263f9","#2560fa","#275dfb","#295afc","#2b57fd","#2e54fd","#3051fe","#334efe","#354bfe","#3848ff","#3a45ff","#3d42ff","#4040ff","#423dff","#453aff","#4838ff","#4b35fe","#4e33fe","#5130fe","#542efd","#572bfd","#5a29fc","#5d27fb","#6025fa","#6322f9","#6620f9","#691ef7","#6c1cf6","#6f1af5","#7218f4","#7517f3","#7815f1","#7c13f0","#7f11ee","#8210ed","#850eeb","#880de9","#8b0ce8","#8e0ae6","#9209e4","#9508e2","#9807e0","#9b06de","#9e05dc","#a104d9","#a403d7","#a703d5","#aa02d2","#ad02d0","#b001ce","#b301cb","#b600c9","#b800c6","#bb00c3","#be00c1","#c100be","#c300bb","#c600b8","#c900b6","#cb01b3","#ce01b0","#d002ad","#d202aa","#d503a7","#d703a4","#d904a1","#dc059e","#de069b","#e00798","#e20895","#e40992","#e60a8e","#e80c8b","#e90d88","#eb0e85","#ed1082","#ee117f","#f0137c","#f11578","#f31775","#f41872","#f51a6f","#f61c6c","#f71e69","#f92066","#f92263","#fa2560","#fb275d","#fc295a","#fd2b57","#fd2e54","#fe3051","#fe334e","#fe354b","#ff3848","#ff3a45","#ff3d42","#ff4040"])


    const xAxis = d3.axisBottom()
        .ticks(4)
        .tickSize(size * columns.length)
    
    const axisX = (g: any) => {
        g.selectAll("g").data(x).join("g")
        .attr("transform", (d: any, i: any) => `translate(${i * size},0)`)
        .each(function(d: any) { 
            return d3.select(this).call(xAxis.scale(d));
        })
        .call(g => g.select(".domain").remove())
        .call(g => g.selectAll(".tick line").attr("stroke", "#ddd"));
    }

    const yAxis = d3.axisLeft()
      .ticks(10)
      .tickSize(-size * columns.length);

    const axisY = g => g.selectAll("g").data(y).join("g")
      .attr("transform", (d, i) => `translate(0,${i * size})`)
      .each(function(d) { return d3.select(this).call(yAxis.scale(d)); })
      .call(g => g.select(".domain").remove())
      .call(g => g.selectAll(".tick line").attr("stroke", "#ddd"));
    
    const svg = d3.create('svg')
        .attr('viewBox', [-50,-50,1200,1200])
        .style('height', height)
        .style('width', width)

    
    svg.append("style")
      .text(`circle.hidden { fill: #000; fill-opacity: 1; r: 1px; }`);

    svg.append("g")
        .attr('data-id', 'xaxis')
        .call(axisX);

    svg.append("g")
        .attr('data-id', 'yaxis')
        .call(axisY);

        
    
    const cell = svg.append("g")
        .selectAll("g")
        .data(d3.cross(d3.range(3), d3.range(2)))
        .join("g")
        .attr("transform", ([i, j]) => `translate(${i * size},${j * size})`)
        .attr('data-id', ([i, j]) => `cell`)
        // .attr('data-x', ([i, j]) => `${i * size}`)
        // .attr('data-y', ([i, j]) => `${j * size}`)
        // .attr('data-id', ([i, j]) => `${m([i, j])}`);


    cell.append("rect")
      .attr("fill", "none")
      .attr("stroke", "#aaa")
      .attr("x", padding / 2 + 0.5)
      .attr("y", padding / 2 + 0.5)
      .attr("width", size - padding)
      .attr("height", size - padding);

    

    cell.each(function([i, j]) {
        d3.select(this).selectAll("circle")
        .data(getFlatData(), datakey)
        .join("circle")
        .attr("cx", (d: DataElem) => x[i](d.avg_agi))
        .attr("cy", (d: DataElem) => {
            return y[j](getProportionateData(d, columns[enumerate(tupstr([i, j]))]))
        })
        .attr('data-id', (d: DataElem) => {
            return `${d.county_name}-${d.state_name}`
        })
        // .on('mouseenter', (event: Event) => {
        //     let targetX = d3.select(event.target)
        //     .attr('cx')

        //     let targetY = d3.select(event.target)
        //     .attr('cy')
            
        //     svg
        //     .append('text')
        //         .attr('x', targetX)
        //         .attr('y', targetY)
        //         .attr('dx', 0)
        //         .attr('dy', 0)
        //         .attr('class', 'small')
        //         .attr('textLength', 50)
        //         .text('Testing text')
        // });
    })
    const circle = cell.selectAll("circle")
      .attr("r", 3.5)
      .attr("fill-opacity", 0.7)
      .attr("fill", (d: DataElem) => color(d.state_name));

    


    // Ignore this line if you don't need the brushing behavior.
    cell.call(brush, circle, svg, {padding, size, x, y, columns});

    
    const reverseEnumeration = d3.scaleOrdinal(enumerate.range(), enumerate.domain())

    svg.append("g")
      .attr('data-type', 'labels')
      .style("font", "bold 10px sans-serif")
      .style("pointer-events", "none")
    .selectAll("text")
    .data(columns)
    .join('foreignObject')
        .attr("transform", (d, i) => {
            let [x, y] = reverseEnumeration(i).split('-')
            return `translate(${x * size},${y * size})`
        })
        .attr("x", padding)
        .attr("y", padding)
        .attr("dy", ".71em")
        .attr('width', '200')
        .attr('height', '100')
        .text((d: string) => `${d}`);

    svg.property("value", [])
    document.getElementById('plot')?.append(svg.node())
    plot_displayed.value = true
    root.value = svg
}

function updatePlot() {
    const width = 600
    const height = width
    const padding = 20
    const size = 300//(width - (3 + 1) * padding) / 2 + padding
    let svg = root.value
    const ordered_measures = 
        Array.from(
            all_measures
            .value
            .values()).sort((a, b) => a.localeCompare(b))
    const columns = ordered_measures
    const x = ordered_measures.map(m => {
        return d3.scaleLinear()
        .domain(d3.extent(getFlatData(), (d: DataElem) => d.avg_agi))
        .rangeRound([padding / 2, size - padding / 2])
    })

    const y = ordered_measures.map(m => {
        return d3.scaleLinear()
        .domain([0.0, 1.0])
        .range([size - padding / 2, padding / 2])
    })
    const color = d3.scaleOrdinal()
        .domain(getFlatData().sort((a, b) => a.state_name.localeCompare(b.state_name)).map((d: DataElem, i) => d.state_name))
        .range(["#1f77b4","#ff7f0e","#2ca02c","#d62728","#9467bd","#8c564b","#e377c2","#7f7f7f","#bcbd22","#17becf", "#8dd3c7","#ffffb3","#bebada","#fb8072","#80b1d3","#fdb462","#b3de69","#fccde5","#d9d9d9","#bc80bd","#ccebc5","#ffed6f", "#8dd3c7","#ffffb3","#bebada","#fb8072","#80b1d3","#fdb462","#b3de69","#fccde5","#d9d9d9","#bc80bd","#ccebc5","#ffed6f"])
    let cell = svg
    .selectAll('g[data-id=cell]')
    cell.each(function ([i, j]) {
        d3.select(this).selectAll("circle")
        .data(getFlatData(), datakey)
        .join("circle")
        .attr("cx", (d: DataElem) => x[i](d.avg_agi))
        .attr("cy", (d: DataElem) => {
            console.log(getProportionateData(d, columns[enumerate(tupstr([i, j]))]))
            return y[j](getProportionateData(d, columns[enumerate(tupstr([i, j]))]))
        })
        .attr('data-id', (d: DataElem) => {
            return `${d.county_name}-${d.state_name}`
        })
        .attr("r", 3.5)
        .attr("fill-opacity", 0.7)
        .attr("fill", (d: DataElem) => color(d.state_name));
    })
    const circle = cell.selectAll("circle")
    cell.call(brush, circle, svg, {padding, size, x, y, columns});




    const xAxis = d3.axisBottom()
        .ticks(4)
        .tickSize(size * columns.length)
    
    const axisX = (g: any) => {
        g.selectAll("g").data(x).join("g")
        .attr("transform", (d: any, i: any) => `translate(${i * size},0)`)
        .each(function(d: any) { 
            return d3.select(this).call(xAxis.scale(d));
        })
        .call(g => g.select(".domain").remove())
        .call(g => g.selectAll(".tick line").attr("stroke", "#ddd"));
    }

    const yAxis = d3.axisLeft()
      .ticks(10)
      .tickSize(-size * columns.length);

    const axisY = g => g.selectAll("g").data(y).join("g")
      .attr("transform", (d, i) => `translate(0,${i * size})`)
      .each(function(d) { return d3.select(this).call(yAxis.scale(d)); })
      .call(g => g.select(".domain").remove())
      .call(g => g.selectAll(".tick line").attr("stroke", "#ddd"));

    

    svg.select("g[data-id=xaxis]")
        .call(axisX);

    svg.select("g[data-id=yaxis]")
        .call(axisY);

    svg.select("g[data-type=labels]")
      .style("font", "bold 10px sans-serif")
      .style("pointer-events", "none")
    .selectAll("text")
    .data(columns)
    .join('foreignObject')
        .attr("transform", (d, i) => {
            let [x, y] = reverseEnumeration(i).split('-')
            return `translate(${x * size},${y * size})`
        })
        .attr("x", padding)
        .attr("y", padding)
        .attr("dy", ".71em")
        .attr('width', '200')
        .attr('height', '100')
        .text((d: string) => `${d}`);
}

const AVG_AGI = 0
const AVG_TAX = 1
const STATE_NAME = 2
const COUNTY_NAME = 3
const MEASURE = 4
const DATA_VALUE = 5

onMounted(() => {
    logger.debug("Taxation Component Mounted")
    
    socket.value = io("ws://localhost:8000/", {transports: ['websocket', 'polling']});
    let query = `
    SELECT (sum(ADJUSTED_GROSS_INCOME) / sum(NUM_RETURNS)) as avg_agi, (sum(TAXES_PAID_AMOUNT) / sum(NUM_RETURNS)) as avg_tax, any(STATE_NAME) as state_name, any(COUNTY_NAME) as county_name, MEASURE as measure, avg(DATA_VALUE) as avg_data_value 
    FROM cps_00004.places_county 
    JOIN cps_00004.income_tax 
    ON cps_00004.places_county.COUNTY_FIPS = cps_00004.income_tax.COUNTYFIP  
    WHERE MEASURE LIKE '%heart%' OR MEASURE LIKE '%Cancer%' OR MEASURE LIKE '%teeth%' OR MEASURE LIKE '%dentist%' OR MEASURE LIKE '%Fair or poor self-rated health status among adults%' OR MEASURE LIKE '%Stroke among adults aged%'
    GROUP BY COUNTY_FIPS, MEASURE
    HAVING state_name = 'Texas' OR state_name = 'California'
    ORDER BY avg_agi DESC`
    socket.value?.emit('query', query)
    /**
     * [] Can D3 make use of Map/hashmap data structures?
     * [] Can we display and incrementally update data as it arrives from the web socket?
     * [] Can the Python server be adjusted to send data more frequently rather than allowing it to build up
     * 
     */
    showPlot()
    socket.value?.on('data', (data) => {
        logger.debug(`Data received: ${getFlatData().length}`)
        data['data'].forEach((row) => {
            let state: string = row[STATE_NAME]
            let county: string = row[COUNTY_NAME]
            all_measures.value.add(row[MEASURE])
                

            if(max_measure.value.has(row[MEASURE])) {
                // update if it exists
                let max_val = max_measure.value.get(row[MEASURE]) as number
                if(row[DATA_VALUE] > max_val ) {
                    max_measure.value.set(row[MEASURE], row[DATA_VALUE])    
                }
            } else {
                // create if it does not exist
                max_measure.value.set(row[MEASURE], row[DATA_VALUE])
            }
            
            if(!model.value.has(state)) {
                model.value.set(state, new Map())
            }
            if( !model.value.get(state)?.has(county) ) {
                let d: DataElem = {
                    avg_agi: row[AVG_AGI],
                    avg_tax: row[AVG_TAX],
                    state_name: row[STATE_NAME],
                    county_name: row[COUNTY_NAME],
                    measures: new Map([ [row[MEASURE], row[DATA_VALUE]] ])
                }
                //@ts-ignore
                let updated = model.value.get(state).set(county, d)
                model.value.set(state, updated)
            } else {
                let d = model.value.get(state)?.get(county) as DataElem
                d.measures.set(row[MEASURE], row[DATA_VALUE])
                let counties = model.value.get(state) as Map<string, DataElem>
                counties?.set(county, d)
                model.value.set(state, counties)
            }
        })
        
        updatePlot()
        
    })
   


})


</script>

<template>
    <div id="plot"></div>
</template>