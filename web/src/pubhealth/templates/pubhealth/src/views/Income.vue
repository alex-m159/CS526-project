<script setup lang="ts">

    // Vue's ref is used to create a "reference" to data that may change
    // and we want to keep connected to the HTML in the template
    import { ref, onMounted, onUnmounted } from "vue";
    import type { Ref } from "vue";
    import { io, Socket } from "socket.io-client";
    import { logger } from '../utils/logging';

    onMounted(() => {
        logger.debug('Income Component Mounted')
    })

</script>

<template>
    INCOME VIEW
</template>

<script scoped>
</script>