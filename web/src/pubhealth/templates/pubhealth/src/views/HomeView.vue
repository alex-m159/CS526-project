<script setup lang="ts">
import TheWelcome from '../components/TheWelcome.vue'
</script>

<template>
  <div class="container">
    <div class="row">
      <h2 class="text-center text-capitalize">American Public Health</h2>
    </div>
    <div class="row">
      <div class="">
        This project focuses on visualizing and evaluating healthcare outcomes in America, specifically in the context of two variables:
        <span class="fw-bold">income</span> and <span class="fw-bold">population density</span>.

        <br/>
        <br/>
        We focus on these factors because we believe that the two most significant factors in healthcare outcomes in America are affordability and proxmity to care.

        <br/>
        <br/>
        Our visualizations will attempt to provide a clear picture with strong evidence that healthcare outcomes are strongly linked to income and population density. 
        We make use of map visualizations, scatter plots, interactive cell charts, and multiple methods of comparisons and clustering to demonstrate this.

      </div>
    </div>

    <div class="row mt-3">
      <h3 class="text-left text-capitalize">Health Outcome Metrics</h3>
    </div>
    <div class="row">
      There are a large variety of health outcome metrics available in our datasets, but we will frequently reference two in particular: the amount of adults over 65 who have lost all their teeth, and the amount of adults with cancer.
      We focus our examples on these two because we found the first to be the most highly correlated with income, and the second to be the least highly correlated with income, so they are good examples for illustrative purposes.
    </div>

    <div class="row mt-3">
      <h3 class="text-left text-capitalize">Technical Terminology</h3>
    </div>
    <div class="row">
      Dispite our efforts to make this information accessible, there are techincal concepts that must be understood in order to comprehend the data and visualizations in this application.
      Here we'll introduce the less common concepts and explain them in plain English.
    </div>
    <div class="row mt-3">
      <h4 class="text-left text-capitalize">Gini Coefficient</h4>
    </div>
    <div class="row">
      The Gini Coefficient is a measure of inequality in a population. It is typically used to measure income or wealth inequality, but it can be applied to any quantifiable resource.
      The original definition and most commonly used definition uses a 0 to 1 scale where 0 is perfect equality and 1 is maximum inequality. The Gini Coefficient was originally limited to comparing resources that could not be negative, but it has since been extended with alternative definitions that tolerate the inclusion of negative values.  
    </div>
    <div class="row mt-3">
      <h4 class="text-left text-capitalize">Rural-Urban Continuum Code (RUCC)</h4>
    </div>
    <div class="row">
      A RUCC is a numerical code that is assigned to each county in the U.S. based on its population density and proximity to a metropolitan area.
      The scale is discrete and ranges from 1 to 9. 1 being the most densly populated and closest to a metro area, and 9 being the least densly populated and far from a metro area.
      This is a definition of each score for the 2023 definitions.

      <div class="row fw-bold">
      Metro counties:
      </div>
      <div class="row">
      1  -	Counties in metro areas of 1 million population or more
      </div>
      <div class="row">
      2 	- Counties in metro areas of 250,000 to 1 million population
      </div>
      <div class="row">
      3  -	Counties in metro areas of fewer than 250,000 population
      </div>
      <div class="row fw-bold">
      Nonmetro counties:
      </div>
      <div class="row">
      4 	- Urban population of 20,000 or more, adjacent to a metro area
      </div>
      <div class="row">
      5 	- Urban population of 20,000 or more, not adjacent to a metro area
      </div>
      <div class="row">
      6 	- Urban population of 5,000 to 20,000, adjacent to a metro area
      </div>
      <div class="row">
      7 	- Urban population of 5,000 to 20,000, not adjacent to a metro area
      </div>
      <div class="row">
      8 	- Urban population of fewer than 5,000, adjacent to a metro area
      </div>
      <div class="row">
      9 	- Urban population of fewer than 5,000, not adjacent to a metro area
      </div>

    </div>
  </div>
</template>
