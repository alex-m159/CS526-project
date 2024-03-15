<script setup lang="ts">

    // Vue's ref is used to create a "reference" to data that may change
    // and we want to keep connected to the HTML in the template
    import { ref, onMounted, onUnmounted } from "vue";
    import type { Ref } from "vue";
    import { io, Socket } from "socket.io-client";
    import { logger } from '../utils/logging';
let socket: Ref<Socket<ServerToClient, ClientToServer> | null> = ref(null)
    onMounted(() => {
        logger.debug('Income Component Mounted')
        //socket.value = io("ws://localhost:8000/", {transports: ['websocket', 'polling']});
        let query = ``; 
    }


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