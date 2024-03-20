<script setup lang="ts">
import { ref, onMounted, onUnmounted } from "vue";
import { logger } from '../utils/logging';
import type { Ref } from "vue";
import { io, Socket } from "socket.io-client";
//@ts-ignore
import * as d3 from "d3";

interface ClientToServer {
    query: (query: string) => string
    setup: (query: string) => string
}

interface ServerToClient {
    data: (data: {data: any[]}) => any
    setup: (data: {data: any[]}) => any 
}

interface DataElem {
    avg_agi: number,
    avg_tax: number,
    region: string,
    division: string, 
    state_name: string,
    county_name: string,
    measures: Map<string, number>
}

interface State {
    state_name: string
    state_abbrev: string
    fips: number
    region: string
    division: string
}

let socket: Ref<Socket<ServerToClient, ClientToServer> | null> = ref(null)
let model: Ref<Map<string, Map<string, DataElem>>> = ref(new Map())
let hidden_data: Ref<Map<string, Map<string, DataElem>>> = ref(new Map())
let all_measures: Ref<Set<string>> = ref(new Set())
let max_measure: Ref<Map<string, number>> = ref(new Map())
let plot_displayed: Ref<boolean> = ref(false)

let ALL_STATES: Ref<Array<State>> = ref([])
let ALL_REGIONS: Ref<Map<string, State[]>> = ref(new Map())
let ALL_DIVISIONS: Ref<Map<string, State[]>> = ref(new Map())
let CHOOSEN_STATES: Ref< Map<string, [boolean, string]> > = ref(new Map())
let CHOOSEN_REGIONS: Ref< Map<string, [boolean, string]> > = ref(new Map())
let CHOOSEN_DIVISIONS: Ref< Map<string, [boolean, string]> > = ref(new Map())


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
const labels = ref(new Set<string>())

let colorscale: Ref<any | undefined> = ref(undefined)

function labelEnter(enter) {
    enter.append('foreignObject')
    // enter.each( (nodes) => {
        // console.log('entering node')
        // console.log(nodes)
    // } )
    // console.log('entering')
    // console.log(enter)
    // return enter
    
}

function labelUpdate(update) {
    // console.log(`updated: ${JSON.stringify(update)}`)
    update.append('foreignObject')
    // update.remove()
    return update
}

function labelExit(exit) {
    // console.log(`exited: ${JSON.stringify(exit)}`)
    exit.remove()
    // return exit
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
    const size = 300//(width - (columns.length + 1) * padding) / columns.length + padding;

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
        .domain(Array.from(model.value.keys()))
        .range(["#1f77b4","#ff7f0e","#2ca02c","#d62728","#9467bd","#8c564b","#e377c2","#7f7f7f","#bcbd22","#17becf", "#8dd3c7","#ffffb3","#bebada","#fb8072","#80b1d3","#fdb462","#b3de69","#fccde5","#d9d9d9","#bc80bd","#ccebc5","#ffed6f", "#8dd3c7","#ffffb3","#bebada","#fb8072","#80b1d3","#fdb462","#b3de69","#fccde5","#d9d9d9","#bc80bd","#ccebc5","#ffed6f"])
        // .range(["#ff4040","#ff423d","#ff453a","#ff4838","#fe4b35","#fe4e33","#fe5130","#fd542e","#fd572b","#fc5a29","#fb5d27","#fa6025","#f96322","#f96620","#f7691e","#f66c1c","#f56f1a","#f47218","#f37517","#f17815","#f07c13","#ee7f11","#ed8210","#eb850e","#e9880d","#e88b0c","#e68e0a","#e49209","#e29508","#e09807","#de9b06","#dc9e05","#d9a104","#d7a403","#d5a703","#d2aa02","#d0ad02","#ceb001","#cbb301","#c9b600","#c6b800","#c3bb00","#c1be00","#bec100","#bbc300","#b8c600","#b6c900","#b3cb01","#b0ce01","#add002","#aad202","#a7d503","#a4d703","#a1d904","#9edc05","#9bde06","#98e007","#95e208","#92e409","#8ee60a","#8be80c","#88e90d","#85eb0e","#82ed10","#7fee11","#7cf013","#78f115","#75f317","#72f418","#6ff51a","#6cf61c","#69f71e","#66f920","#63f922","#60fa25","#5dfb27","#5afc29","#57fd2b","#54fd2e","#51fe30","#4efe33","#4bfe35","#48ff38","#45ff3a","#42ff3d","#40ff40","#3dff42","#3aff45","#38ff48","#35fe4b","#33fe4e","#30fe51","#2efd54","#2bfd57","#29fc5a","#27fb5d","#25fa60","#22f963","#20f966","#1ef769","#1cf66c","#1af56f","#18f472","#17f375","#15f178","#13f07c","#11ee7f","#10ed82","#0eeb85","#0de988","#0ce88b","#0ae68e","#09e492","#08e295","#07e098","#06de9b","#05dc9e","#04d9a1","#03d7a4","#03d5a7","#02d2aa","#02d0ad","#01ceb0","#01cbb3","#00c9b6","#00c6b8","#00c3bb","#00c1be","#00bec1","#00bbc3","#00b8c6","#00b6c9","#01b3cb","#01b0ce","#02add0","#02aad2","#03a7d5","#03a4d7","#04a1d9","#059edc","#069bde","#0798e0","#0895e2","#0992e4","#0a8ee6","#0c8be8","#0d88e9","#0e85eb","#1082ed","#117fee","#137cf0","#1578f1","#1775f3","#1872f4","#1a6ff5","#1c6cf6","#1e69f7","#2066f9","#2263f9","#2560fa","#275dfb","#295afc","#2b57fd","#2e54fd","#3051fe","#334efe","#354bfe","#3848ff","#3a45ff","#3d42ff","#4040ff","#423dff","#453aff","#4838ff","#4b35fe","#4e33fe","#5130fe","#542efd","#572bfd","#5a29fc","#5d27fb","#6025fa","#6322f9","#6620f9","#691ef7","#6c1cf6","#6f1af5","#7218f4","#7517f3","#7815f1","#7c13f0","#7f11ee","#8210ed","#850eeb","#880de9","#8b0ce8","#8e0ae6","#9209e4","#9508e2","#9807e0","#9b06de","#9e05dc","#a104d9","#a403d7","#a703d5","#aa02d2","#ad02d0","#b001ce","#b301cb","#b600c9","#b800c6","#bb00c3","#be00c1","#c100be","#c300bb","#c600b8","#c900b6","#cb01b3","#ce01b0","#d002ad","#d202aa","#d503a7","#d703a4","#d904a1","#dc059e","#de069b","#e00798","#e20895","#e40992","#e60a8e","#e80c8b","#e90d88","#eb0e85","#ed1082","#ee117f","#f0137c","#f11578","#f31775","#f41872","#f51a6f","#f61c6c","#f71e69","#f92066","#f92263","#fa2560","#fb275d","#fc295a","#fd2b57","#fd2e54","#fe3051","#fe334e","#fe354b","#ff3848","#ff3a45","#ff3d42","#ff4040"])
    colorscale.value = color

    const xAxis = d3.axisBottom()
        .ticks(4)
        .tickSize(size * 2)
    
    const axisX = (g: any) => {
        g.selectAll("g").data(x).join("g")
        .attr("transform", (d: any, i: any) => `translate(${i * size},0)`)
        .attr('data_type', 'xaxisinner')
        .each(function(d: any) { 
            return d3.select(this).call(xAxis.scale(d));
        })
        .call(g => g.select(".domain").remove())
        .call(g => g.selectAll(".tick line").attr("stroke", "#ddd"));
    }

    const yAxis = d3.axisLeft()
      .ticks(5)
      .tickSize(-size * 2);

    const axisY = g => g.selectAll("g").data(y).join("g")
      .attr("transform", (d, i) => `translate(0,${i * size})`)
      .attr('data_type', 'yaxisinner')
      .each(function(d) { return d3.select(this).call(yAxis.scale(d)); })
      .call(g => g.select(".domain").remove())
      .call(g => g.selectAll(".tick line").attr("stroke", "#ddd"));
    
    const svg = d3.create('svg')
        .attr('viewBox', [-50,-50,1000,1000])
        .style('height', 1200)
        .style('width', 1200)

    
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
      .attr("fill", (d: DataElem) => {
            if(group_by.value == 'division')
                return color(d.division)
            else if(group_by.value == 'region')
                return color(d.region)
            else
                return color(d.state_name)
        });

    


    // Ignore this line if you don't need the brushing behavior.
    cell.call(brush, circle, svg, {padding, size, x, y, columns});

    
    const reverseEnumeration = d3.scaleOrdinal(enumerate.range(), enumerate.domain())

    svg.append("g")
      .attr('data-type', 'labels')
      .style("font", "bold 10px sans-serif")
      .style("pointer-events", "none")
      .selectAll('text')
    .data(columns, (c) => c)
    .join('foreignObject')
        .attr("transform", (d, i) => {
            let [x, y] = reverseEnumeration(i).split('-')
            return `translate(${x * size},${(y * size)})`
        })
        
        .attr("x", padding)
        .attr("y", padding)
        .attr("dy", ".71em")
        .attr('width', '200')
        .attr('height', '100')
        .attr('id', (d: string) => d)
        .text((d: string) => `${d}`);

    svg.property("value", [])
    document.getElementById('plot')?.append(svg.node())
    plot_displayed.value = true
    root.value = svg
}

function updatePlot() {
    const ordered_measures = 
        Array.from(
            all_measures
            .value
            .values()).sort((a, b) => a.localeCompare(b))
    
    const columns = ordered_measures
    const width = 600
    const height = width
    const padding = 20
    const size = 300//(width - (2 + 1) * padding) / 4 + padding;
    let svg = root.value

    
    svg.select("g[data-type=labels]")
      .attr('data-type', 'labels')
      .style("font", "bold 10px sans-serif")
      .style("pointer-events", "none")
      .selectAll('text')
    .data(columns, (c) => c)
    .join('foreignObject')
        
        .attr("transform", (d, i) => {
            let [x, y] = reverseEnumeration(i).split('-')
            return `translate(${x * size},${((y * size)-50)})`
        })
        .attr("x", padding)
        .attr("y", padding)
        .attr("dy", ".71em")
        .attr('width', '200')
        .attr('height', '100')
        .attr('id', (d: string) => {
            d
        })
        .text((d: string) => `${d}`);

    const x = [1, 2, 3].map(m => {
        let [min, max] = d3.extent(getFlatData(), (d: DataElem) => d.avg_agi)
        return d3.scaleLinear()
        .domain([10000, max*1.05])
        .rangeRound([padding / 2, size - padding / 2])
    })

    const y = [1, 2].map(m => {
        return d3.scaleLinear()
        .domain([0.0, 1.1])
        .range([size - padding / 2, padding / 2])
    })
    const xAxis = d3.axisBottom()
        .ticks(4)
        .tickSize(size * 2)
    
    const axisX = (g: any) => {
        g.selectAll("g[data_type=xaxisinner]").data(x).join("g")
        .attr('data_type', 'xaxisinner')
        .attr("transform", (d: any, i: any) => `translate(${i * size},0)`)
        .each(function(d: any) { 
            return d3.select(this).call(xAxis.scale(d));
        })
        .call(g => g.select(".domain").remove())
        .call(g => g.selectAll(".tick line").attr("stroke", "#ddd"));
    }

    const yAxis = d3.axisLeft()
      .ticks(5)
      .tickSize(-size * 3);

    const axisY = g => g.selectAll("g[data_type=yaxisinner]").data(y).join("g")
      .attr("transform", (d, i) => `translate(0,${i * size})`)
      .attr('data_type', 'yaxisinner')
      .each(function(d) { return d3.select(this).call(yAxis.scale(d)); })
      .call(g => g.select(".domain").remove())
      .call(g => g.selectAll(".tick line").attr("stroke", "#ddd"));

    let color_keys = Array.from(model.value.keys())
    const color = d3.scaleOrdinal()
        .domain(color_keys)
        .range(["#1f77b4","#ff7f0e","#2ca02c","#d62728","#9467bd","#8c564b","#e377c2","#7f7f7f","#bcbd22","#17becf", "#8dd3c7","#ffffb3","#bebada","#fb8072","#80b1d3","#fdb462","#b3de69","#fccde5","#d9d9d9","#bc80bd","#ccebc5","#ffed6f", "#8dd3c7","#ffffb3","#bebada","#fb8072","#80b1d3","#fdb462","#b3de69","#fccde5","#d9d9d9","#bc80bd","#ccebc5","#ffed6f"])
    colorscale.value = color
    let cell = svg
    .selectAll('g[data-id=cell]')
    cell.each(function ([i, j]) {
        d3.select(this).selectAll("circle")
        .data(getFlatData().filter((d: DataElem) => d.measures.has( columns[enumerate(tupstr([i, j]))]) ), datakey)
        .join("circle")
        .attr("cx", (d: DataElem) => x[i](d.avg_agi))
        .attr("cy", (d: DataElem) => {
            return y[j](getProportionateData(d, columns[enumerate(tupstr([i, j]))]))
        })
        .attr('data-id', (d: DataElem) => {
            return `${d.county_name}-${d.state_name}`
        })
        .attr("r", 3.5)
        .attr("fill-opacity", 0.7)
        .attr("fill", (d: DataElem) => {
            if(group_by.value == 'division')
                return color(d.division)
            else if(group_by.value == 'region')
                return color(d.region)
            else
                return color(d.state_name)
        });
    })
    const circle = cell.selectAll("circle")
    cell.call(brush, circle, svg, {padding, size, x, y, columns});




  
    

    svg.select("g[data-id=xaxis]")
        .call(axisX);

    svg.select("g[data-id=yaxis]")
        .call(axisY);

    // svg.select("g[data-type=labels]")
    //   .style("font", "bold 10px sans-serif")
    //   .style("pointer-events", "none")
    // .selectAll("text")
    // .data(columns, (c) => c)
    // .join(labelEnter, labelUpdate, labelExit)
    //     .attr("transform", (d, i) => {
    //         let [x, y] = reverseEnumeration(i).split('-')
    //         return `translate(${x * size},${y * size})`
    //     })
    //     .attr("x", padding)
    //     .attr("y", padding)
    //     .attr("dy", ".71em")
    //     .attr('width', '200')
    //     .attr('height', '100')
    //     .attr('id', (d: string) => {
    //         d
    //     })
    //     .text((d: string) => `${d}`);
}

const AVG_AGI = 0
const AVG_TAX = 1
const STATE_NAME = 2
const COUNTY_NAME = 3
const MEASURE = 4
const DATA_VALUE = 5
const REGION = 6
const DIVISION = 7

onMounted(() => {
    logger.debug("Taxation Component Mounted")
    
    socket.value = io(`ws://45.79.137.151:9001/`, {transports: ['websocket', 'polling']});
    let query = `
    SELECT avg_agi, avg_tax, state_name, county_name, measure, avg_data_value, REGION, DIVISION 
    FROM (
            SELECT (sum(ADJUSTED_GROSS_INCOME) / sum(NUM_RETURNS)) as avg_agi, (sum(TAXES_PAID_AMOUNT) / sum(NUM_RETURNS)) as avg_tax, any(STATE_NAME) as state_name, any(COUNTY_NAME) as county_name, MEASURE as measure, avg(DATA_VALUE) as avg_data_value 
            FROM cps_00004.places_county 
            JOIN cps_00004.income_tax 
            ON cps_00004.places_county.COUNTY_FIPS = cps_00004.income_tax.COUNTYFIP
            WHERE MEASURE LIKE '%heart%' OR MEASURE LIKE '%Cancer%' OR MEASURE LIKE '%teeth%' OR MEASURE LIKE '%dentist%' OR MEASURE LIKE '%Fair or poor self-rated health status among adults%' OR MEASURE LIKE '%Stroke among adults aged%'
            GROUP BY COUNTY_FIPS, MEASURE
            ORDER BY avg_agi DESC
    ) as inside
    JOIN cps_00004.state_regions
    ON inside.state_name = cps_00004.state_regions.STATE_NAME
    `
    

    showPlot()
    socket.value?.on('data', (data) => {
        data['data'].forEach((row) => {
            let state: string = row[STATE_NAME]
            let county: string = row[COUNTY_NAME]
            if(row[DATA_VALUE] === undefined || row[DATA_VALUE] === null) {
                return
            }
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
            
            if(!hidden_data.value.has(state)) {
                hidden_data.value.set(state, new Map())
            }
            if( !hidden_data.value.get(state)?.has(county) ) {
                let d: DataElem = {
                    avg_agi: row[AVG_AGI],
                    avg_tax: row[AVG_TAX],
                    division: row[DIVISION],
                    region: row[REGION],
                    state_name: row[STATE_NAME],
                    county_name: row[COUNTY_NAME],
                    measures: new Map([ [row[MEASURE], row[DATA_VALUE]] ])
                }
                //@ts-ignore
                let updated = hidden_data.value.get(state).set(county, d)
                hidden_data.value.set(state, updated)
            } else {
                let d = hidden_data.value.get(state)?.get(county) as DataElem
                d.measures.set(row[MEASURE], row[DATA_VALUE])
                let counties = hidden_data.value.get(state) as Map<string, DataElem>
                counties?.set(county, d)
                hidden_data.value.set(state, counties)
            }
        })
        
        updatePlot()
        
    })
    
    socket.value?.emit('query', query, "query")

    let setup_query = `SELECT DISTINCT STATE_NAME, STATE_ABBREV, STATE_FIPS, REGION, DIVISION FROM cps_00004.state_regions`
    
    socket.value?.on('setup', (data) => {
        const STATE_NAME = 0
        const STATE_ABBREV = 1
        const STATE_FIPS = 2 
        const REGION = 3 
        const DIVISION = 4
         data['data'].forEach((row) => {
            let s: State = {
                state_name: row[STATE_NAME],
                state_abbrev: row[STATE_ABBREV],
                fips: row[STATE_FIPS],
                region: row[REGION],
                division: row[DIVISION]
            }
            ALL_STATES.value.push(s)
            if(!ALL_REGIONS.value.has(s.region)) {
                ALL_REGIONS.value.set(s.region, [])
            }
            var updated = ALL_REGIONS.value.get(s.region) as State[]
            updated?.push(s)
            ALL_REGIONS.value.set(s.region, updated)

            if(!ALL_DIVISIONS.value.has(s.division)) {
                ALL_DIVISIONS.value.set(s.division, [])
            }
            var updated = ALL_DIVISIONS.value.get(s.division) as State[]
            updated?.push(s)
            ALL_DIVISIONS.value.set(s.division, updated)

            CHOOSEN_STATES.value.set(row[STATE_NAME], [false, ""])
            CHOOSEN_REGIONS.value.set(row[REGION], [false, ""])
            CHOOSEN_DIVISIONS.value.set(row[DIVISION], [false, ""])
         })
    })
    socket.value?.emit('setup', setup_query)
    


})

let group_by: Ref<string> = ref('none')

function updateColors() {
    let keys = Array.from(model.value.keys())
    var CHOOSEN = undefined as unknown as Ref<Map<string, [boolean, string]>>
    if(group_by.value === 'none') {
        CHOOSEN = CHOOSEN_STATES
    } else if(group_by.value === 'region') {
        CHOOSEN = CHOOSEN_REGIONS
    } else if(group_by.value === 'division') {
        CHOOSEN = CHOOSEN_DIVISIONS
    }

    keys.forEach((k) => {
        let updated = CHOOSEN.value.get(k) as [boolean, string]
        updated[1] = colorscale.value(k)
        CHOOSEN.value.set(k, updated)
    })
}

function stateCheckbox(event) {
    console.log(event)
    if(group_by.value === 'none') {
        
        let state = event.target.name
        let checked = event.target.checked
        console.log(state)
        CHOOSEN_STATES.value.set(state, [checked, colorscale.value(state)])
        if(checked) {
            let data = hidden_data.value.get(state) as Map<string, DataElem>
            model.value.set(state, data)
        } else {
            model.value.delete(state)
        }
    } else if(group_by.value === 'region') {
        let region = event.target.name
        let checked = event.target.checked
        
        console.log(region)
        CHOOSEN_REGIONS.value.set(region, [checked, colorscale.value(region)])
        if(checked) {
            let states_in_region = ALL_REGIONS.value.get(region)?.map((s) => s.state_name) as string[]
            let show: [string, Map<string, DataElem>][] = 
                Array.from(hidden_data.value.entries()).filter(([state_name, counties]) => states_in_region.includes(state_name))

            let [_, merged] = show.reduce((prev: [string, Map<string, DataElem>], curr: [string, Map<string, DataElem>]) => {
                let region = prev[0]
                let counties_aggregated = prev[1]

                let state = curr[0]
                let counties: Map<string, DataElem> = curr[1]
                counties.forEach((data, county_name) => {
                    counties_aggregated.set(`${county_name}, ${state}`, data)
                })
                
                return [region, counties_aggregated]
            },  [region, new Map<string, DataElem>()] )

            model.value.set(region, merged)
        } else {
            model.value.delete(region)
            
        }
    }  else if(group_by.value === 'division') {
        let division = event.target.name
        let checked = event.target.checked
        
        console.log(division)
        CHOOSEN_DIVISIONS.value.set(division, [checked, colorscale.value(division)])
        if(checked) {
            let states_in_division = ALL_DIVISIONS.value.get(division)?.map((s) => s.state_name) as string[]
            let show: [string, Map<string, DataElem>][] = 
                Array.from(hidden_data.value.entries()).filter(([state_name, counties]) => states_in_division.includes(state_name))

            let [_, merged] = show.reduce((prev: [string, Map<string, DataElem>], curr: [string, Map<string, DataElem>]) => {
                let division = prev[0]
                let counties_aggregated = prev[1]

                let state = curr[0]
                let counties: Map<string, DataElem> = curr[1]
                counties.forEach((data, county_name) => {
                    counties_aggregated.set(`${county_name}, ${state}`, data)
                })
                
                return [division, counties_aggregated]
            },  [division, new Map<string, DataElem>()] )

            model.value.set(division, merged)
        } else {
            model.value.delete(division)
            
        }
        
    }
    updatePlot()
    updateColors()
}

function groupChange(e) {
    if(group_by.value === 'none') {
        model.value.clear()
        CHOOSEN_STATES.value.forEach(([selected, color], state) => {
            if(selected) {
                let data = hidden_data.value.get(state) as Map<string, DataElem>
                model.value.set(state, data)
            }
        })
        
    } else if(group_by.value === 'region') {
        model.value.clear()
        CHOOSEN_REGIONS.value.forEach(([selected, color], region) => {
            if(selected) {
                let states_in_region = ALL_REGIONS.value.get(region)?.map((s) => s.state_name) as string[]
                let show: [string, Map<string, DataElem>][] = 
                    Array
                    .from(hidden_data.value.entries())
                    .filter(([state_name, counties]) => states_in_region.includes(state_name))
                
                let [_, merged] = show.reduce((prev: [string, Map<string, DataElem>], curr: [string, Map<string, DataElem>]) => {
                    let region = prev[0]
                    let counties_aggregated = prev[1]

                    let state = curr[0]
                    let counties: Map<string, DataElem> = curr[1]
                    counties.forEach((data, county_name) => {
                        counties_aggregated.set(`${county_name}, ${state}`, data)
                    })
                    
                    return [region, counties_aggregated]
                },  [region, new Map<string, DataElem>()] )
                model.value.set(region, merged)
            }
        })
    } else if(group_by.value === 'division') {
        model.value.clear()
        CHOOSEN_DIVISIONS.value.forEach(([selected, color], division) => {
            if(selected) {
                let states_in_division = ALL_DIVISIONS.value.get(division)?.map((s) => s.state_name) as string[]
                let show: [string, Map<string, DataElem>][] = 
                    Array
                    .from(hidden_data.value.entries())
                    .filter(([state_name, counties]) => states_in_division.includes(state_name))
                
                let [_, merged] = show.reduce((prev: [string, Map<string, DataElem>], curr: [string, Map<string, DataElem>]) => {
                    let division = prev[0]
                    let counties_aggregated = prev[1]

                    let state = curr[0]
                    let counties: Map<string, DataElem> = curr[1]
                    counties.forEach((data, county_name) => {
                        counties_aggregated.set(`${county_name}, ${state}`, data)
                    })
                    
                    return [division, counties_aggregated]
                },  [division, new Map<string, DataElem>()] )
                model.value.set(division, merged)
            }
        })
    }
    updatePlot()
}



function clearDivision() {
    model.value.clear()
    Array.from(CHOOSEN_DIVISIONS.value.keys())
    .map(k => {
        CHOOSEN_DIVISIONS.value.set(k, [false, ""])
    })
    updatePlot()
}

function clearRegion() {
    model.value.clear()
    Array.from(CHOOSEN_REGIONS.value.keys())
    .map(k => {
        CHOOSEN_REGIONS.value.set(k, [false, ""])
    })
    updatePlot()
}

function clearStates() {
    model.value.clear()
    Array.from(CHOOSEN_STATES.value.keys())
    .map(k => {
        CHOOSEN_STATES.value.set(k, [false, ""])
    })
    updatePlot()
}

</script>

<template>
    <div class="row">
        <div id="plot" class="col-md-10"></div>
        <div class="col-md-2">
            <div class="row">
                <label>Group By:</label>
                <select class="form-select" v-model="group_by" @change="groupChange">
                    <option key="none" value="none">Individual State</option>
                    <option key="region" value="region">Region</option>
                    <option key="division" value="division">Division</option>
                </select>
            </div>
            <div class="row my-2 ">


                <div v-if="group_by == 'none'">
                    <button class="btn btn-primary my-3" @click="clearStates()">Clear All</button>
                    <br/>
                    <label for="states">Selected States:</label>
                    <br/>
                    <div style="overflow: scroll; height: 30vh; text-overflow: unset;">
                        <div v-for="state in Array.from(CHOOSEN_STATES.entries()).filter(([k, v]) => v[0] === true).sort((a, b) => a[0].localeCompare(b[0]))">
                        <input 
                            checked 
                            class="form-check-input mx-2" 
                            type="checkbox"
                            :name="state[0]"
                            :key="state[0]"
                            @change="stateCheckbox">
                            <label :style="'font-weight: bold; color:' + state[1][1]" class="mx-3 form-check-label" :for="state[0]">{{state[0]}}</label>
                        </div>
                    </div>
                    <br/>
                    <label>Available States:</label>
                    <br/>                    

                    <div style="overflow: scroll; height: 30vh;">
                        <div v-for="state in Array.from(CHOOSEN_STATES.entries()).filter(([k, v]) => v[0] === false).sort((a, b) => a[0].localeCompare(b[0]))">
                            <input 
                                class="form-check-input mx-2" 
                                type="checkbox" 
                                :name="state[0]"
                                :key="state[0]"
                                @change="stateCheckbox">
                            <label class="mx-3 form-check-label" :for="state[0]">{{state[0]}}</label>    
                        </div>
                    </div>
                </div>




                <div v-if="group_by == 'region'">
                    <button class="btn btn-primary" @click="clearRegion()">Clear All</button>
                    <br/>
                    <label for="regions">Selected Region:</label>
                    <br/>
                    <div v-for="region in Array.from(CHOOSEN_REGIONS.entries()).filter(([k, v]) => v[0] === true).sort((a, b) => a[0].localeCompare(b[0]))">
                        <input 
                            checked 
                            class="form-check-input mx-2" 
                            type="checkbox"
                            :name="region[0]"
                            :key="region[0]"
                            
                            @change="stateCheckbox">
                            <label :style="'color:' + region[1][1]" class="mx-3 form-check-label" :for="region[0]">{{region[0]}}</label>
                    </div>
                    <br/>
                    <label>Available Regions:</label>
                    <br/>                    

                    <div v-for="region in Array.from(CHOOSEN_REGIONS.entries()).filter(([k, v]) => v[0] === false).sort((a, b) => a[0].localeCompare(b[0]))">
                        <input 
                            class="form-check-input mx-2" 
                            type="checkbox" 
                            :name="region[0]"
                            :key="region[0]"
                            @change="stateCheckbox">
                        <label class="mx-3 form-check-label" :for="region[0]">{{region[0]}}</label>    
                    </div>
                </div>



                <div v-if="group_by == 'division'">
                    <button class="btn btn-primary" @click="clearDivision()">Clear All</button>
                    <br/>
                    <label for="divisions">Selected Division:</label>
                    <br/>
                    <div v-for="division in Array.from(CHOOSEN_DIVISIONS.entries()).filter(([k, v]) => v[0] === true).sort((a, b) => a[0].localeCompare(b[0]))">
                        <input 
                            checked 
                            class="form-check-input mx-2" 
                            type="checkbox"
                            :name="division[0]"
                            :key="division[0]"
                            @change="stateCheckbox">
                            <label :style="'color:' + division[1][1]" class="mx-3 form-check-label" :for="division[0]">{{division[0]}}</label>
                    </div>
                    <br/>
                    <label>Available Divisions:</label>
                    <br/>                    

                    <div v-for="division in Array.from(CHOOSEN_DIVISIONS.entries()).filter(([k, v]) => v[0] === false).sort((a, b) => a[0].localeCompare(b[0]))">
                        <input 
                            class="form-check-input mx-2" 
                            type="checkbox" 
                            :name="division[0]"
                            :key="division[0]"
                            @change="stateCheckbox">
                        <label class="mx-3 form-check-label" :for="division[0]">{{division[0]}}</label>    
                    </div>
                </div>


            </div>

            
        </div>
    </div>
</template>
