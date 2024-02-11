<script setup lang="ts">
    import { ref, onMounted, onUnmounted } from "vue";
    import type { Ref } from "vue";
    import { io, Socket } from "socket.io-client";
    import type {
        DefaultEventsMap,
        EventNames,
        EventParams,
        EventsMap,
        Emitter,
      } from "@socket.io/component-emitter";
      import { logger } from '../utils/logging';

      interface ClientToServer {
        message: () => string
      }

      interface ServerToClient {
        response: (data: any) => any
      }

      let socket: Ref<Socket<ServerToClient, ClientToServer> | null> = ref(null);
      onMounted(() => {
        logger.debug("WebSocketExample Component Mounted")
        socket.value = io("ws://localhost:5000/");
        socket.value?.on("response", (data: any) => {
          console.log(`Data from SocketIO ${JSON.stringify(data)}`)
        })

        socket.value?.emit("message")
      })
</script>

<template>
  <h2>Hello WebSocketExample</h2>
</template>

<style scoped>
</style>