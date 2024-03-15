<script setup lang="ts">

    // Vue's ref is used to create a "reference" to data that may change
    // and we want to keep connected to the HTML in the template
    import { ref, onMounted, onUnmounted } from "vue";
    import type { Ref } from "vue";
    import { io, Socket } from "socket.io-client";
    import { logger } from '../utils/logging';
    import * as d3 from "d3";
    import * as topojson from 'topojson-client';

    let us = ref({})

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

        const g = svg.append("g");

        const states = g.append("g")
            .attr("fill", "#444")
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
            .attr("stroke", "white")
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
            event.stopPropagation();
            states.transition().style("fill", null);
            d3.select(this).transition().style("fill", "red");
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

        element.appendChild(svg.node());
        
    }
    interface ClientToServer {
    query: (query: string) => string
    setup: (query: string) => string
    }

    interface ServerToClient {
        data: (data: {data: any[]}) => any
        setup: (data: {data: any[]}) => any 
    }
    let socket: Ref<Socket<ServerToClient, ClientToServer> | null> = ref(null)
    onMounted(async () => {
        logger.debug('Income Component Mounted')
        socket.value = io("ws://localhost:8000/", {transports: ['websocket', 'polling']});
        let query = `SELECT
            STATEFIP,
            YEAR,
            ROUND(AVG(INCTOT)) AS avg_INCTOT,
            ROUND(AVG(FTOTVAL)) AS avg_FTOTVAL
        FROM
            cps_00004
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
        // sending query
        /*
        socket.value?.on('data', (data) => {
            data['data'].forEach((row) => {
                let statefip: number = row.STATE_FIP
                let year: string = row.YEAR
                let avg_inctot: number = row.avg_INCTOT
                let avg_ftotval: number = row.avg_FTOTVAL
            })
            // Process the received data
        });
        socket.value?.emit('query', query);
        */
        //const us = await loadGeoJson('/templates/pubhealth/public/states-10m.json'); 
        fetch('/states-10m.json')
        .then(response => {
            if (!response.ok) {
            throw new Error('Network response was not ok');
            }
            return response.json()
        })
        .then((json) => {
            console.log(json);
            us.value = json;
            ShowMap(us.value); // make sure json is loaded before calling
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
    INCOME VIEW
    <div id="map-chart">Average Individual Income</div>
</template>

<script scoped>
</script>