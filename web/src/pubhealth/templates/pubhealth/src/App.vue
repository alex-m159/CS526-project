<script setup lang="ts">
import { RouterLink, RouterView } from 'vue-router'
import HelloWorld from './components/HelloWorld.vue'
</script>

<template>

  <div class="container-fluid">
    <header class="d-flex py-3">
      <span class="col-md-1"></span>
      <a class="d-flex align-items-center text-center col-md-3 mb-2 mb-md-0 text-dark text-decoration-none">US Public Health</a>
      <span class="d-flex align-items-center col-md-4">
        <nav class="nav nav-pills">
          <li class="nav-item mx-3">
            <RouterLink to="/income">Income</RouterLink>
          </li>
          <li class="nav-item mx-3">
            <RouterLink to="/income-inequality">Income Inequality</RouterLink>
          </li>
          <li class="nav-item mx-3">
            <RouterLink to="/population">Population Density</RouterLink>
          </li>
          <li class="nav-item mx-3">
            <RouterLink to="/taxation">Taxation</RouterLink>
          </li>
        </nav>
      </span>
    </header>

  <!-- The RouteView tag is where Vue will load in the component for the 
       currently loaded route.-->
  <RouterView />  
  </div>
  <!-- <header>
  </header> -->

  
</template>

<style scoped>
.header-color {
  background-color: rgb(50, 50, 50);
}
</style>
