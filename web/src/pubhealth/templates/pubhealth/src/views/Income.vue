<script setup lang="ts">

    // Vue's ref is used to create a "reference" to data that may change
    // and we want to keep connected to the HTML in the template
    import { ref, onMounted, onUnmounted, computed } from "vue";
    import type { Ref} from "vue";
    import { io, Socket } from "socket.io-client";
    import { logger } from '../utils/logging';
    import * as d3 from "d3";
    import * as topojson from 'topojson-client';
    import { watch } from 'vue';
    import Plotly from 'plotly.js-dist';

    let domain = `localhost`
    let port = 9001

    let us = ref({});
    let incomeData = ref({});
    let lifeData = ref([]);
    const selectedState = ref(null);
    const selectedYear = ref(2000);
    const yearRange = ref({min:2000, max:2023});
    const showIndiviBubbles = ref(true);
    const showFTOTINCBubbles = ref(true);
    const plotContainer = ref(null);

    let stateMap = new Map();

    // watch functions watch for changes in value (for interactivity) and then call functions when
    // value is changed
    watch(showIndiviBubbles,(newValue, oldValue)=> {
        UpdateMap(us.value, incomeData.value);
        UpdateScatter();
        Update3DScatter();
    });
    watch(showFTOTINCBubbles, (newValue, oldValue) => {
        UpdateMap(us.value, incomeData.value);
        UpdateScatter();
        Update3DScatter();
    });

    watch(selectedYear, (newValue) =>{
        UpdateMap(us.value, incomeData.value);
        UpdateScatter();
    })

    // display the bubble map
    function ShowMap(us) {

        
        const width = 975;
        const height = 1000;

        const zoom = d3.zoom()
            .scaleExtent([1, 8])
            .on("zoom", zoomed);

        const svg = d3.select("#map-chart").append("svg")
            .attr("viewBox", [0, 0, width, height])
            .attr("width", width)
            .attr("height", height)
            .attr("style", "max-width: 100%; height: auto;")
            .on("click", reset);

        const projection = d3.geoAlbersUsa();
        const path = d3.geoPath().projection(projection);
        // map statefips to state names
        let features = topojson.feature(us, us.objects.states).features;
        features.forEach(feature => {
            stateMap.set(feature.id, feature.properties.name);
        });

        const g = svg.append("g")
            .attr('id', 'zoom-group'); // create zoom group so that UpdateMap bubbles can also zoom
        // #444 gray
        const states = g.append("g")
            .attr("fill", "#cccccc")
            .attr("cursor", "pointer")
            .selectAll("path")
            .data(topojson.feature(us, us.objects.states).features)
            .join("path")
            .on("click", clicked)
            .attr("d", path);
        
        states.append("title")
            .text(d => d.properties.name);

        g.append("path")
            .attr("fill", "none")
            .attr("stroke", "black")
            .attr("stroke-linejoin", "round")
            .attr("d", path(topojson.mesh(us, us.objects.states, (a, b) => a !== b)));

        svg.call(zoom);

        function reset() {
            states.transition().style("fill", null);
            svg.transition().duration(750).call(
            zoom.transform,
            d3.zoomIdentity,
            d3.zoomTransform(svg.node()).invert([width / 2, height / 2])
            );
        }

        // state selection events
        function clicked(event, d) {
            const [[x0, y0], [x1, y1]] = path.bounds(d);
            // update selected state
            selectedState.value = d.id;
            // update selected state in scatter plot
            Update3DScatter();
            UpdateScatter();
            event.stopPropagation();
            states.transition().style("fill", null);
            d3.select(this).transition().style("fill", "#333333");
            svg.transition().duration(750).call(
            zoom.transform,
            d3.zoomIdentity
                .translate(width / 2, height / 2)
                .scale(Math.min(8, 0.9 / Math.max((x1 - x0) / width, (y1 - y0) / height)))
                .translate(-(x0 + x1) / 2, -(y0 + y1) / 2),
            d3.pointer(event, svg.node())
        );
    }

        function zoomed(event) {
            const {transform} = event;
            g.attr("transform", transform);
            g.attr("stroke-width", 1 / transform.k);
        }

        //element.appendChild(svg.node());
        
    }
    // prep the data for scatter plot
    function combineStateData() {
        let selectedYearData = selectedYear.value;
        
        if (!Object.values(lifeData.value).some(d => d.YEAR === selectedYearData)) {
            selectedYearData = 2019; 
        }

        let filteredIncomeData = incomeData.value.filter(dataEntry => dataEntry.YEAR === selectedYearData);
        let combinedData = filteredIncomeData.map(dataEntry => {
            const key = `${dataEntry.STATEFIP}-${selectedYearData}`;
            const lifeEntry = lifeData.value[key];
            return {
                ...dataEntry,
                LIFE_EXPECTANCY: lifeEntry ? lifeEntry.LIFE_EXPECTANCY : null,
            };
        });
        // console.log("combinedData:", combinedData);
        socket.value?.emit('linear_regression', combinedData.map((datum) => {
            return [datum['avg_INCTOT'], datum['LIFE_EXPECTANCY']]
        }), 'Individual Income vs Life Expectancy')

        socket.value?.emit('linear_regression', combinedData.map((datum) => {
            return [datum['avg_FTOTVAL'], datum['LIFE_EXPECTANCY']]
        }), 'Family Income vs Life Expectancy')
        return combinedData;
    }
    function combineStateData3D() {
        let selectedYearData = selectedYear.value;
        
        if (!Object.values(lifeData.value).some(d => d.YEAR === selectedYearData)) {
            selectedYearData = 2019; 
        }

        let filteredIncomeData = incomeData.value;
        let combinedData = filteredIncomeData.map(dataEntry => {
            const key = `${dataEntry.STATEFIP}-${selectedYearData}`;
            const lifeEntry = lifeData.value[key];
            return {
                ...dataEntry,
                LIFE_EXPECTANCY: lifeEntry ? lifeEntry.LIFE_EXPECTANCY : null,
            };
        });
        // console.log("combinedData:", combinedData);
        return combinedData;
    }

    // scatter plot svg
    function setupScatterPlotSVG() {
        const margin = { top: 20, right: 20, bottom: 50, left: 50 },
                width = 480 - margin.left - margin.right,
                height = 390 - margin.top - margin.bottom;

        d3.select("#line-graph svg").remove();

        const svg = d3.select("#line-graph").append("svg")
            .attr("width", width + margin.left + margin.right)
            .attr("height", height + margin.top + margin.bottom)
            .append("g")
            .attr("transform", `translate(${margin.left},${margin.top})`);

        return { svg, width, height, margin };
    }

    // scatter plot with indiv + family income 
    function UpdateScatter() {
        const { svg, width, height, margin } = setupScatterPlotSVG();
        const data = combineStateData(); 

        const xScale = d3.scaleLinear()
            .domain([10000, d3.max(data, d => Math.max(d.avg_INCTOT, d.avg_FTOTVAL)) * 1.1])
            .range([0, width]);

        // y axis range
        const yScale = d3.scaleLinear()
            .domain([70, 85]) 
            .range([height, 0]);

        // short form x axis ticks to accomodate for family income going into the 100ks
        const xAxis = d3.axisBottom(xScale)
            .ticks(width / 80)  
            .tickFormat(d3.format("~s")); 

        svg.append("g")
            .attr("transform", `translate(0,${height})`)
            .call(xAxis);

        svg.append("g")
            .call(d3.axisLeft(yScale));

        // axis titles
        svg.append("text")             
            .attr("transform", `translate(${width / 2}, ${height + margin.top + 20})`)
            .style("text-anchor", "middle")
            .text("Average Income");
        svg.append("text")
            .attr("transform", "rotate(-90)")
            .attr("y", 0 - margin.left)
            .attr("x", 0 - (height / 2))
            .attr("dy", "1em") 
            .style("text-anchor", "middle")
            .text("Life Expectancy");
        
        // scatter plot dots are also togglable 
        // individual income
        if (showIndiviBubbles.value) {
            svg.selectAll(".dot-income")
                .data(data)
                .enter().append("circle")
                .attr("class", "dot-income")
                .attr("cx", d => xScale(d.avg_INCTOT))
                .attr("cy", d => yScale(d.LIFE_EXPECTANCY))
                .attr("r", 5)
                .style("fill", d => d.STATEFIP === selectedState.value ? "blue" : "#c3e0ea")
                .on("mouseover", tooltipFunction)
                .on("mouseout", tooltipHideFunction);
        } else {
            svg.selectAll(".dot-income").remove(); 
        }

        // family income
        if (showFTOTINCBubbles.value) {
            svg.selectAll(".dot-family")
                .data(data)
                .enter().append("circle")
                .attr("class", "dot-family")
                .attr("cx", d => xScale(d.avg_FTOTVAL))
                .attr("cy", d => yScale(d.LIFE_EXPECTANCY))
                .attr("r", 5)
                .style("fill", d => d.STATEFIP === selectedState.value ? "red" : "#ffc9bb")
                .on("mouseover", tooltipFunction)
                .on("mouseout", tooltipHideFunction);
        } else {
            svg.selectAll(".dot-family").remove(); 
        }

        svg.selectAll(".dot-income")
            .filter(d => d.STATEFIP === selectedState.value)
            .raise() 
            .attr("r", 7);
        svg.selectAll(".dot-family")
            .filter(d => d.STATEFIP === selectedState.value)
            .raise() 
            .attr("r", 7);
    }

    // show scatter tooltips
    function tooltipFunction(event, d) {
        const [x, y] = d3.pointer(event, this);
        const tooltipOffsetX = 60; 
        const tooltipOffsetY = 30; 

        d3.select("#tooltip")
            .style("opacity", 1)
            .html(`State: ${d.STATENAME}<br/>Income: $${d.avg_INCTOT}<br/>Life Expectancy: ${d.LIFE_EXPECTANCY} years`)
            .style("left", `${x + tooltipOffsetX}px`)
            .style("top", `${y + tooltipOffsetY}px`);
    }

    // hide tooltip function
    function tooltipHideFunction() {
        d3.select("#tooltip").style("opacity", 0);
    }
    // 3d scatter plot
    function Update3DScatter() {
        const data1 = combineStateData3D();
        const plotData = computed(() => {
            return data1
                .filter(d => d.YEAR >= 2000 && d.YEAR <= 2019)
                .map(d => {
                    return {
                        x: d.avg_INCTOT,
                        y: d.avg_FTOTVAL,
                        z: d.LIFE_EXPECTANCY,
                        id: d.STATEFIP,
                        year: d.YEAR,
                        name: d.STATENAME,
                        text: `State: ${d.STATENAME}<br>Year: ${d.YEAR}<br>Income: $${d.avg_INCTOT} (Individual), <br>Life Expectancy: ${d.LIFE_EXPECTANCY} years`,
                        text2: `State: ${d.STATENAME}<br>Year: ${d.YEAR}<br>Income: $${d.avg_FTOTVAL} (Family)<br>Life Expectancy: ${d.LIFE_EXPECTANCY} years`,
                    };
                })
                .filter(d => (showIndiviBubbles.value && d.x != null) || (showFTOTINCBubbles.value && d.y != null));
        });
        const data = plotData.value;
        //console.log("Data for plotting:", JSON.stringify(data, null, 2));
        // selected state colors
        let individualIncomeColors = data.map(d => (d.id === selectedState.value ? 'blue' : '#c3e0ea'));
        let familyIncomeColors = data.map(d => (d.id === selectedState.value ? 'red' : '#ffc9bb'));
        const traces = [];
        if (showIndiviBubbles.value) {
            traces.push({
                x: data.map(d => d.x),
                y: data.map(d => d.year), 
                z: data.map(d => d.z),
                mode: 'markers',
                type: 'scatter3d',
                name: 'Individual Income',
                marker: {
                    color: individualIncomeColors,
                    size: 6,
                    opacity: 0.8,
                    
                },
                text: data.map(d => d.text),
                hoverinfo: 'text'
            });
        }

        if (showFTOTINCBubbles.value) {
            traces.push({
                x: data.map(d => d.y),
                y: data.map(d => d.year), 
                z: data.map(d => d.z),
                mode: 'markers',
                type: 'scatter3d',
                name: 'Family Income',
                marker: {
                    color: familyIncomeColors,
                    size: 6,
                    opacity: 0.8,
                    
                },
                text: data.map(d => d.text2),
                hoverinfo: 'text'
            });
        }

        const layout = {
            margin: { l: 0, r: 0, b: 0, t: 0 },
            scene: {
                xaxis: { title: 'Income' },
                yaxis: { title: 'Year' },
                zaxis: { title: 'Life Expectancy' }
            },
            showlegend: false
        };
        
        Plotly.newPlot(plotContainer.value, traces, layout);
    }

    // update function for the bubble map
    function UpdateMap(us, allIncomeData) {
        const svg = d3.select('#map-chart').select('svg');
        let features = topojson.feature(us, us.objects.states).features;
        // filter for year
        const incomeData = allIncomeData.filter(data => data.YEAR === selectedYear.value);
        // calculate centroid and inctot, ftotvals
        const projection = d3.geoAlbersUsa();
        const path = d3.geoPath().projection(projection);
        features.forEach(feature => {
            const centroid = path.centroid(feature);
            feature.centroid = (!isNaN(centroid[0]) && !isNaN(centroid[1])) ? centroid : [0, 0];
            const incomeDatum = incomeData.find(d => d.STATEFIP === feature.id);
            feature.income = incomeDatum ? incomeDatum.avg_INCTOT : 0;
            feature.ftotval = incomeDatum ? incomeDatum.avg_FTOTVAL : 0;
        });

        const g = svg.select('#zoom-group');
        let bubblesGroup = g.select('.bubbles');
        if (bubblesGroup.empty()) {
            bubblesGroup = g.append('g').attr('class', 'bubbles');
        }

        // toggable bubbles
        if (showIndiviBubbles.value) {
            // offset is -5
            updateBubbles(features, bubblesGroup, 'income', 'blue', -5); 
        } else {
            bubblesGroup.selectAll('.bubble.income').remove();
        }

        if (showFTOTINCBubbles.value) {
            // offset is +5
            updateBubbles(features, bubblesGroup, 'ftotval', 'red', 5); 
        } else {
            bubblesGroup.selectAll('.bubble.ftotval').remove();
        }
    }


    function updateBubbles(features, bubblesGroup, dataKey, color, offsetX) {
        // remove 0 from the extent so bubble sizes can be scaled off non 0 values
        const validFeatures = features.filter(d => d[dataKey] > 0);
        const extent = d3.extent(validFeatures, d => d[dataKey]);
        //console.log(`Adjusted extent for ${dataKey}:`, extent);

        const radiusScale = d3.scaleSqrt()
            .domain(extent) 
            .range([2, 30]);

        const svg = d3.select('#map-chart').select('svg');

        const bubbles = bubblesGroup.selectAll(`circle.${dataKey}`)
            .data(validFeatures, d => d.id); 

        const tooltip = d3.select("#tooltip2"); 

        bubbles.enter().append('circle')
            .merge(bubbles)
            .attr('class', `bubble ${dataKey}`)
            .attr('fill', color)
            .attr('stroke', 'black')
            .attr('stroke-width', 1)
            .attr('fill-opacity', 0.5)
            .attr('cx', d => d.centroid[0] + offsetX)
            .attr('cy', d => d.centroid[1])
            .attr('r', d => radiusScale(d[dataKey]))
            .on('mouseenter', (event, d) => {
                const [x, y] = d3.pointer(event, svg.node()); 
                const tooltip = d3.select("#tooltip2");
                // tooltip position doesn't work very well
                // not even near the cursor
                tooltip.style("opacity", 1)
                    .html(`State: ${d.properties.name}<br/>Income: $${d[dataKey]}`)
                    .style("left", `${x - 120}px`)
                    .style("top", `${y - 100}px`);
            })
            .on('mouseleave', () => {
                tooltip.transition()
                    .duration(500)
                    .style("opacity", 0);
            });

    }

    let display_stats = ref(true)

    let display_vars: Ref<Map<string, [string, string]>> = ref(new Map())

    
    function showStats(data, name) {
        let covar = data['covariance']
        let corr_coef = data['correlation_coef']


        let title = name
        let cov = `Covariance: ${String(covar.toFixed(3))}`
        let corr = `Correlation Coefficient: ${String((100*corr_coef).toFixed(3))}`

        display_vars.value.set(title, [cov, corr])

        display_stats.value = true
    }


    interface ClientToServer {
        query: (query: string, name: string) => string
        setup: (query: string) => string
    }

    interface ServerToClient {
        data: (data: {data: any[]}) => any
        setup: (data: {data: any[]}) => any 
    }
    let socket: Ref<Socket<ServerToClient, ClientToServer> | null> = ref(null)
    onMounted(async () => {
        logger.debug('Income Component Mounted')
        socket.value = io(`ws://${domain}:${port}/`, {transports: ['websocket', 'polling']});
        let query = `SELECT
            STATEFIP,
            YEAR,
            ROUND(AVG(INCTOT)) AS avg_INCTOT,
            ROUND(AVG(FTOTVAL)) AS avg_FTOTVAL
        FROM
            cps_00004.cps_00004
        WHERE
            YEAR > 1999
            AND
            INCTOT != 999999999
            AND 
            FTOTVAL != 9999999999
        GROUP BY 
            STATEFIP,
            YEAR
        ORDER BY
            STATEFIP, 
            YEAR`
        
        
        // socket & json can't handle decimal values so convert to float
        let query2 = `SELECT
            STATE_FIPS, 
            toFloat64(LIFE_EXPECTANCY) AS LIFE_EXPECTANCY, YEAR
            FROM cps_00004.life_expectancy
            WHERE STATE_FIPS IS NOT NULL`
       
        // load geojson
        fetch('/states-10m.json')
        .then(response => {
            if (!response.ok) {
            throw new Error('network response was not ok');
            }
            return response.json()
        })
        .then((json) => {
            //console.log(json);
            us.value = json;
            ShowMap(us.value);
             // make sure json is loaded before calling
            socket.value?.emit('query', query, 'avg_inc');
        })
        
        socket.value?.on('data', (data) =>{
            
            if(data['name'] == 'avg_inc'){
                //console.log('income data');
                //console.log(data['data']);
                // format data before passing it in to UpdateMap
                // or else the data is only in an array of arrays
                const formattedData = data['data'].map(row => ({
                    STATEFIP: row[0],
                    YEAR: row[1],
                    avg_INCTOT: row[2],
                    avg_FTOTVAL: row[3]
                }));
                // make sure the statefips still have their leading 0s
                formattedData.forEach(d => {
                    d.STATEFIP = String(d.STATEFIP).padStart(2, '0');
                })
                //console.log(formattedData)
                incomeData.value = formattedData;
                //console.log(us.value)
                // merge with features

                UpdateMap(us.value, formattedData);
                if (data['end'] == true) {
                    //console.log(stateMap);
                    incomeData.value.forEach(dataEntry => {
                        //console.log(dataEntry)
                        if (stateMap.has(String(dataEntry.STATEFIP).trim())) {
                            dataEntry.STATENAME = stateMap.get(dataEntry.STATEFIP);
                            //console.log('merged');
                        } else {
                            dataEntry.STATENAME = 'Unknown';
                        }
                    });
                    //console.log(incomeData.value)
                    socket.value?.emit('query', query2, 'life');
                }
            }
            if (data['name'] == 'life') {
                //console.log('lifeData');
                data['data'].forEach(row => {
                const newStateFips = row[0].toString().padStart(2, '0');  
                const newLifeExpectancy = +parseFloat(row[1]).toFixed(1);
                const year = row[2];

                // key creation
                const key = `${newStateFips}-${year}`;

            
                lifeData.value[key] = {
                    STATE_FIPS: newStateFips,
                    LIFE_EXPECTANCY: newLifeExpectancy,
                    YEAR: year
                };
            
                
                });
                
                if (data['end'] === true) {
                    //console.log(lifeData.value);
                    plotContainer.value = document.getElementById('3d-graph');  // Ensure this ID matches your HTML
                    UpdateScatter();
                    Update3DScatter();
                }
            }
        });

        socket.value.on('linear_regression_result', (data) => {
            showStats(data['data'], data['name'])
        })
        
        
    })


    onUnmounted(() => {
        if (socket.value) {
            socket.value.disconnect(); 
            socket.value = null;
        }
    });
</script>

<template>
    <div class="container mt-4">
        <h1 class="text-center mb-4">Income and Life Expectancy</h1>
        <div class="row">
            <div class="col-12 mb-3">
                <div id="controls" class="p-3 border rounded">
                    <div class="mb-3">
                        <label for="range-slider" class="form-label">Selected Year: {{ selectedYear }}</label>
                        <input type="range" class="form-range" id="range-slider" v-model.number="selectedYear" :min="2000" :max="2023">
                    </div>
                    <div class="form-check mb-2">
                        <input class="form-check-input" type="checkbox" id="flexCheckChecked" v-model="showIndiviBubbles">
                        <label class="form-check-label" for="flexCheckChecked">
                            <span class="label-individual">Average Individual Income</span>
                        </label>
                    </div>
                    <div class="form-check">
                        <input class="form-check-input" type="checkbox" id="ftotincCheck" v-model="showFTOTINCBubbles">
                        <label class="form-check-label" for="ftotincCheck">
                            <span class="label-family">Average Family Income</span>
                        </label>
                    </div>
                    <div class="row">
                        <div class='col' v-for="elem in Array.from(display_vars.entries())">
                            <div class="fw-bold">
                                {{ elem[0] }}
                            </div>
                            <div>
                                {{  elem[1][0] }}
                            </div>
                            <div>
                                {{  elem[1][1] }}
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            <div class="col-12">
                <div id="visualization" class="d-flex justify-content-between align-items-start">
                    <div id="map-chart" class="border border-secondary p-2" style="width: 60%;">
                        <div id="tooltip2" style="position: absolute; text-align: left; width: auto; height: auto; padding: 10px; background: #f9f9f9; border: 1px solid #d4d4d4; border-radius: 8px; pointer-events: none; opacity: 0;">
                        </div>
                    </div>
                    <div style="width: 38%; display: flex; flex-direction: column;">
                        <div id="line-graph" class="border border-secondary" style="height: 400px;">
                            <div id="tooltip" style="position: absolute; text-align: left; width: auto; height: auto; padding: 10px; background: #f9f9f9; border: 1px solid #d4d4d4; border-radius: 8px; pointer-events: none; opacity: 0;">
                            </div>
                        </div>
                        <div id="3d-graph" class="border border-secondary" style="height: 400px;">

                        </div>
                    </div>
                
                </div>
            </div>
        </div>
    </div>
</template>

<style scoped>
    #controls {
        background: #fff;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    }
    #visualization {
        display: flex;
        flex-wrap: wrap;
        gap: 20px;
    }
    #map-chart {
        position: relative; 
        height: 800px; 
    }
    #line-graph {
        position: relative;
        height: 400px;
    }
    #3d-graph {
        position: relative;
        height: 400px; 
        background-color: #f0f0f0; 
        border: 1px solid black; 
    }
    .label-individual {
        background-color: #007BFF; 
        color: white;
        padding: 5px 10px;
        border-radius: 20px; 
        display: inline-block;
    }

    .label-family {
        background-color: #DC3545; 
        color: white;
        padding: 5px 10px;
        border-radius: 20px; 
        display: inline-block;
    }
</style>
 