<script setup lang="ts">

    // Vue's ref is used to create a "reference" to data that may change
    // and we want to keep connected to the HTML in the template
    import { ref, onMounted, onUnmounted } from "vue";
    import type { Ref, computed } from "vue";
    import { io, Socket } from "socket.io-client";
    import { logger } from '../utils/logging';
    import * as d3 from "d3";
    import * as topojson from 'topojson-client';
    import { watch } from 'vue';

    let host = `localhost`

    let us = ref({});
    let incomeData = ref({});
    let lifeData = ref([]);
    const selectedState = ref(null);
    const selectedYear = ref(2000);
    const yearRange = ref({min:2000, max:2023});
    const showIndiviBubbles = ref(true);
    let stateMap = new Map();

    // watch functions watch for changes in value (for interactivity) and then call functions when
    // value is changed
    watch(showIndiviBubbles,(newValue, oldValue)=> {
        UpdateMap(us.value, incomeData.value);
    });
    watch(selectedYear, (newValue) =>{
        UpdateMap(us.value, incomeData.value);
        UpdateScatter();
    })
    function ShowMap(us) {

        
        const width = 975;
        const height = 610;

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
            .attr("fill", "#77dd77")
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

        function clicked(event, d) {
            const [[x0, y0], [x1, y1]] = path.bounds(d);
            selectedState.value = d.id;
            // call line graph
            UpdateScatter(selectedState.value);
            event.stopPropagation();
            states.transition().style("fill", null);
            d3.select(this).transition().style("fill", "#ccffcc");
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
    function combineStateData() {
        let filteredIncomeData = incomeData.value.filter(dataEntry => dataEntry.YEAR === selectedYear.value);
        let combinedData = filteredIncomeData.map(dataEntry => {
            const lifeEntry = lifeData.value.find(le => le.STATENAME === dataEntry.STATENAME);
            return {
            ...dataEntry,
            LIFE_EXPECTANCY: lifeEntry ? lifeEntry.LIFE_EXPECTANCY : null,
            };
        });
        return combinedData;
    }
    function setupScatterPlotSVG() {
        const margin = { top: 20, right: 20, bottom: 50, left: 50 },
                width = 600 - margin.left - margin.right,
                height = 400 - margin.top - margin.bottom;

        d3.select("#line-graph svg").remove();

        const svg = d3.select("#line-graph").append("svg")
            .attr("width", width + margin.left + margin.right)
            .attr("height", height + margin.top + margin.bottom)
            .append("g")
            .attr("transform", `translate(${margin.left},${margin.top})`);

        return { svg, width, height, margin };
    }

    function UpdateScatter(selectedStateFIP) {
        const { svg, width, height, margin } = setupScatterPlotSVG();
        const data = combineStateData();
        const xScale = d3.scaleLinear()
            .domain([0, d3.max(incomeData.value, d => d.avg_INCTOT) * 1.1])
            .range([0, width]);

        const yScale = d3.scaleLinear()
            .domain([70, d3.max(lifeData.value, d => d.LIFE_EXPECTANCY) * 1.1])
            .range([height, 0]);
        svg.append("g")
            .attr("transform", `translate(0,${height})`)
            .call(d3.axisBottom(xScale));

        svg.append("g")
            .call(d3.axisLeft(yScale));

        svg.append("text")             
            .attr("transform", `translate(${width / 2}, ${height + margin.top + 20})`)
            .style("text-anchor", "middle")
            .text("Average Individual Income");
        svg.append("text")
            .attr("transform", "rotate(-90)")
            .attr("y", 0 - margin.left)
            .attr("x", 0 - (height / 2))
            .attr("dy", "1em") 
            .style("text-anchor", "middle")
            .text("Life Expectancy");

        const tooltip = d3.select("#tooltip");
        svg.selectAll(".dot")
            .data(data)
            .enter().append("circle")
            .attr("class", "dot")
            .attr("cx", d => xScale(d.avg_INCTOT))
            .attr("cy", d => yScale(d.LIFE_EXPECTANCY))
            .attr("r", 5)
            .style("fill", d => stateMap.get(selectedStateFIP) === d.STATENAME ? "red" : "#69b3a2")
            .on("mouseover", (event, d) => {
                //TODO: tooltip
                tooltip.transition()
                    .duration(200)
                    .style("opacity", .9);
                tooltip.html(`State: ${d.STATENAME}<br/>Income: $${d.avg_INCTOT}<br/>Life Expectancy: ${d.LIFE_EXPECTANCY} years`)
                    .style("left", (event.pageX) + "px")
                    .style("top", (event.pageY - 28) + "px");
            })
            .on("mouseleave", () => {
            tooltip.transition()
                .duration(500)
                .style("opacity", 0);
            });
        // make sure selected dot is always on top
        // re-select it and raise it
        svg.selectAll(".dot")
            .filter(d => stateMap.get(selectedStateFIP) === d.STATENAME)
            .raise() 
            .style("fill", "red") 
            .attr("r", 6);
    }
    function hideIndiviBubbles() {
        d3.select('#map-chart').selectAll('.bubbles circle').remove();
    }
    function UpdateMap(us, incomeData) {

        if(showIndiviBubbles.value) {
            const filteredIncomeData = incomeData.filter(d => d.YEAR === selectedYear.value);
            const svg = d3.select('#map-chart').select('svg');
            let features = topojson.feature(us, us.objects.states).features;
            const incomeExtent = d3.extent(filteredIncomeData, d => d.avg_INCTOT);
            const radiusScale = d3.scaleSqrt().domain(incomeExtent).range([2, 30]);
            const projection = d3.geoAlbersUsa();
            const path = d3.geoPath().projection(projection);
            // merge with features
            
            //console.log(us);
            features.forEach(feature => {
                const centroid = path.centroid(feature);
                //console.log(filteredIncomeData)
                //console.log(feature.id);
                feature.centroid = (!isNaN(centroid[0]) && !isNaN(centroid[1])) ? centroid : [0, 0]; // default to 0,0? 
                const incomeDatum = filteredIncomeData.find(d => d.STATEFIP == feature.id);
                feature.income = incomeDatum ? incomeDatum.avg_INCTOT : 0;
            });
            //console.log(features.map(d => d.income));
            //console.log(features.map(d => d.centroid));
            // append to zoom group so bubbles also zoom
            const g = svg.select('#zoom-group');
            let bubblesGroup = g.select('.bubbles');
            if (bubblesGroup.empty()) {
                bubblesGroup = g.append('g').attr('class', 'bubbles');
            }
            const bubbles = bubblesGroup.selectAll('circle')
                .data(features, d => d.id);

            // need proper enter-update-exit pattern this way bubbles don't get created infinitely
            // this is to update bubbles by year
            // remove old bubbles
            // give bubbles a unique group and id so we don't have copies
            const enteredBubbles = bubbles.enter().append('circle')
                .attr('fill', 'blue')
                .attr('stroke', 'blue')
                .attr('stroke-width', 1)
                .attr('fill-opacity', 0.5);

            bubbles.merge(enteredBubbles)
                .attr('cx', d => d.centroid[0])
                .attr('cy', d => d.centroid[1])
                .attr('r', d => radiusScale(d.income));

            bubbles.exit().remove();
            

            // hover tooltips
            const tooltip2 = d3.select("#tooltip2");
            enteredBubbles.on('mouseenter', (event, d) => {
                tooltip2.transition()
                    .duration(200)
                    .style("opacity", .9);
                tooltip2.html(`State: ${d.properties.name}<br/>Income: $${d.income}`)
                    .style("left", (event.pageX) + "px")
                    .style("top", (event.pageY - 28) + "px");
            }).on('mouseleave', (event, d) => {
                tooltip2.transition()
                    .duration(500)
                    .style("opacity", 0);
            }); 
        } else {
            hideIndiviBubbles();
        }
        
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
        socket.value = io(`ws://${host}:9001/`, {transports: ['websocket', 'polling']});
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
            STATE_NAME, 
            toFloat64(LIFE_EXPECTANCY) AS LIFE_EXPECTANCY
            FROM cps_00004.life_expectancy
            WHERE COUNTY IS NULL`
       
        // load geojson
        fetch('/states-10m.json')
        .then(response => {
            if (!response.ok) {
            throw new Error('network response was not ok');
            }
            return response.json()
        })
        .then((json) => {
            console.log(json);
            us.value = json;
            ShowMap(us.value);
             // make sure json is loaded before calling
            socket.value?.emit('query', query, 'avg_inc');
        })
        
        socket.value?.on('data', (data) =>{
            
            if(data['name'] == 'avg_inc'){
                console.log('income data');
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
                console.log(formattedData)
                incomeData.value = formattedData;
                //console.log(us.value)
                // merge with features

                UpdateMap(us.value, formattedData);
                if (data['end'] == true) {
                    console.log(stateMap);
                    incomeData.value.forEach(dataEntry => {
                        //console.log(dataEntry)
                        if (stateMap.has(String(dataEntry.STATEFIP).trim())) {
                            dataEntry.STATENAME = stateMap.get(dataEntry.STATEFIP);
                            console.log('merged');
                        } else {
                            dataEntry.STATENAME = 'Unknown';
                        }
                    });
                    console.log(incomeData.value)
                    socket.value?.emit('query', query2, 'life');
                }
            }
            if (data['name'] == 'life') {
                console.log('lifeData');
                const bom = '\ufeff';//
                data['data'].forEach(row =>{
                    const newEntry =  {
                        STATENAME: row[0].startsWith(bom) ? row[0].slice(1) : row[0],
                        LIFE_EXPECTANCY: +parseFloat(row[1]).toFixed(1)
                    };
                    const index = lifeData.value.findIndex(item => item.STATENAME === newEntry.STATENAME);
                    if (index !== -1) {
                        lifeData.value[index] = newEntry;
                    }else {
                        lifeData.value.push(newEntry);
                    }
                })
                if (data['end'] == true) {
                    console.log(lifeData.value);
                    UpdateScatter();
                }
            }
        });
        //socket.value?.emit('query', query2, 'life');
        // for some reason the data is being recieved in 2 parts so I made an array
        // and added the value if it was new
        /*
        socket.value?.on('data', (data) =>{
            if (data['name'] == 'life') {
                console.log('lifeData');
                const bom = '\ufeff';//
                data['data'].forEach(row =>{
                    const newEntry =  {
                        STATENAME: row[0].startsWith(bom) ? row[0].slice(1) : row[0],
                        LIFE_EXPECTANCY: +parseFloat(row[1]).toFixed(1)
                    };
                    const index = lifeData.value.findIndex(item => item.STATENAME === newEntry.STATENAME);
                    if (index !== -1) {
                        lifeData.value[index] = newEntry;
                    }else {
                        lifeData.value.push(newEntry);
                    }
                })
                if (data['end'] == true) {
                    console.log(lifeData.value);
                }
            }
        });
        */
        
    })


    onUnmounted(() => {
        if (socket.value) {
            socket.value.disconnect(); 
            socket.value = null;
        }
    });
</script>

<template>
    <div>
        <h1>Income and Life Expectancy</h1>
    </div>
    <div id="content">
        <div id="controls">
            <div id="range-slider">
                <input type="range" v-model.number="selectedYear" :min="2000" :max="2023" />
                <div>Selected Year: {{ selectedYear }}</div>
            </div>
            <div class="form-check">
                <input class="form-check-input" type="checkbox" value="" id="flexCheckChecked" v-model="showIndiviBubbles">
                <label class="form-check-label" for="flexCheckChecked">
                    Average Individual Income
                </label>
            </div>
        </div>
        <div id="visualization">
            <div id="map-chart">
                <div id="tooltip2" style="position: absolute; text-align: left; width: auto; height: auto; padding: 10px; background: #f9f9f9; border: 1px solid #d4d4d4; border-radius: 8px; pointer-events: none; opacity: 0;">
                </div>
            </div>
            <div id="line-graph">
                <div id="tooltip" style="position: absolute; text-align: left; width: auto; height: auto; padding: 10px; background: #f9f9f9; border: 1px solid #d4d4d4; border-radius: 8px; pointer-events: none; opacity: 0;">
                </div>
            </div>
        </div>
        
        
    </div>
</template>

<style scoped>
    #content {
        display: flex;
        flex-direction: column;
        align-items: center;
    }
    #visualization {
        display: flex;
        justify-content: space-between;
        width: 100%;
    }
    #line-graph {
        display: inline-block;
        width: 40%;
    }
    #map-chart {
        display: inline-block;
        border: 2px solid #000;
        width: 60%;
    }
    #controls {
        padding: 10px;
        width: 100%;
        box-sizing: border-box;
    }
</style>
<script scoped>
</script>