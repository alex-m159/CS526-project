import * as tern from 'd3-ternary'
import * as d3 from 'd3'


export function trivariatePlot(data?: [number, number, number][]) {
    let d = [
        [1, 2, 3],
        [4, 5, 6],
        [7, 8, 9],
        [4, 7, 4],
        [9, 2, 5]
    ]
    let b = tern.barycentric(d)
    let t = tern.ternaryPlot(b)
    console.log()


}


// let height = 800
// let width = height
// function clamp(x, min, max) {
//     return x < min ? min : x > max ? max : x;
// }
// let ticks = 4;
// let coorset = new Set()
// const ternarybin =  () => {
//     let coords = [d => d[0], d => d[1], d => d[2]];
//     let normalize = true;
//     let transform = ([a, b]) => 
//         ({
//             x: a + .5 * b, 
//             y: Math.sqrt(3) / 2 * b 
//         });

//     function gather(values) {
//         let i = -1;
//         const triangles = new d3.InternMap(undefined, JSON.stringify);
//         const s: [number, number, number] = [d3.max(values, coords[0]), d3.max(values, coords[2]), d3.max(values, coords[2])]
//         // let vs = d3.cross(d3.range(0, 1, 0.1), d3.range(0, 1, 0.1))
//         for (const v of values) {
//           const d = [
//             +coords[0](v, ++i, vs),
//             +coords[1](v, ++i, vs),
//             +coords[2](v, ++i, vs)
//           ];
//           if (normalize) {
//             // const s = d3.sum(d);
//             // d[0] = clamp(d[0] / s, 1e-12, 1-1e-12);
//             // d[1] = clamp(d[1] / s, 1e-12, 1-1e-12);
//             // d[2] = clamp(d[2] / s, 1e-12, 1-1e-12);
            
//             // d[0] = d[0]
//             // d[1] = d[1]
//             // d[2] = d[2]
//           }
//           const a = Math.floor(d[0] * ticks);
//           const b = Math.floor(d[1] * ticks);
//           const o = (ticks + 1 + a + b + Math.floor(d[2] * ticks)) % 2;
//           const c = [ a, b, o ];
//           if (!triangles.has(c)) triangles.set(c, {
//             ...transform([(a + (1 + o) / 3) / ticks, (b + (1 + o) / 3) / ticks]),
//             a, b, o,
//             polygon: o ? [
//               transform([(a + 1) / ticks, b / ticks]),
//               transform([a / ticks, (b + 1) / ticks]),
//               transform([(a + 1) / ticks, (b + 1) / ticks])
//             ] : [
//               transform([a / ticks, b / ticks]),
//               transform([a / ticks, (b + 1) / ticks]),
//               transform([(a + 1) / ticks, b / ticks])
//             ],
//             values: []
//           });
//           triangles.get(c).values.push(v);
//         }
//         return Array.from(triangles.values());
//       } 

//     gather.coords = (x, y, z) =>
//     x === undefined ? coords : ((coords = [x, y, z]), gather);
    
//     gather.ticks = _ => _ === undefined ? ticks : ((ticks = +_), gather);
//     gather.transform = _ => _ === undefined ? transform : ((transform = _), gather);

//     return gather;
// }
// let shear = 0.5
// let transform = ([a, b]) => ({
//     x: 40 + 600 * (a + shear * b),
//     y: height - 13 - (600 * b * Math.sqrt(3)) / 2
//   })

// let ternary = ternarybin()
// //   .coords(d => +d.agriculture, d => +d.industry, d => +d.service)
// //   .coords(d => +d.properties.avg_agi, d => +d.properties.avg_agi, d => +d.properties.gini)
//   .ticks(ticks)
//   .transform(transform)


// // from https://observablehq.com/@toja/d3-ternary-plot
// let data = await d3.csv(
//     "https://gist.githubusercontent.com/toja/811f0ddc765c59c26de544fd0e0ba46f/raw/eef11e930f6c05700faca47711b173f795a84181/sectors.csv"
//   )

// // 2D affine transform from (a,b) to (x, y).
// // The default transform sends the unit domain to [[0, 0], [.5, sqrt(3)/2], [1, 0]]
// export function toCoor(d: any): any {
//     const a = Math.floor(d[0] * ticks);
//     const b = Math.floor(d[1] * ticks);
//     const o = (ticks + 1 + a + b + Math.floor(d[2] * ticks)) % 2;
//     const c = [ a, b, o ];
//     return c
// }

// // export function fromCoor(c: [number, number, number]): [[number, number],[number, number],[number, number]] {
// //     let a = c[0]
// //     let b = c[1]
// //     let o = c[2]
    

// //     return 
// // }

// export let chart = (_data) => {
//     let bins = ternary(data)
//     window.bins = bins
//     const tri = new d3.InternMap(undefined, JSON.stringify);
//     var a = Math.floor(0.5 * ticks);
//     var b = Math.floor(0.5 * ticks);
//     var o = (ticks + 1 + a + b + Math.floor(0.5 * ticks)) % 2;
//     var c = [ a, b, o ];
//     if (!tri.has(c)) { 
//         tri.set(c, 
//             {
//                 ...transform([(a + (1 + o) / 3) / ticks, (b + (1 + o) / 3) / ticks]),
//                 a, b, o,
//             polygon: o ? [
//                 transform([(a + 1) / ticks, b / ticks]),
//                 transform([a / ticks, (b + 1) / ticks]),
//                 transform([(a + 1) / ticks, (b + 1) / ticks])
//             ] : [
//                 transform([a / ticks, b / ticks]),
//                 transform([a / ticks, (b + 1) / ticks]),
//                 transform([(a + 1) / ticks, b / ticks])
//             ],
//             values: []
//         });
//     }

//     console.log()


//     const svg = d3.create("svg").attr("viewBox", [0, 0, width, height]);
  
//     // triangles
//     const color = d3.scaleSequentialSqrt([0, 40], d3.interpolateBlues);
//     svg
//       .append("g")
//       .selectAll()
//       .data(bins)
//       .join("path")
//       .attr("d", d => `M${d.polygon.map(e => [e.x, e.y]).join("L")}Z`)
//       .attr("fill", d => color(d.values.length))
//       .attr('data-key', d => `${d.a}, ${d.b}, ${d.o}`)
  
//     // lines
//     svg
//       .append("g")
//       .selectAll()
//       .data(
//         []
//           .concat(d3.range(0, 1, 1 / ticks).map(x => [[x, 0], [x, 1 - x]]))
//           .concat(d3.range(0, 1, 1 / ticks).map(x => [[0, x], [1 - x, x]]))
//           .concat(d3.range(0, 1, 1 / ticks).map(x => [[1 - x, 0], [0, 1 - x]]))
//       )
//       .join("path")
//       .attr(
//         "d",
//         d =>
//           `M${d
//             .map(transform)
//             .map(e => [e.x, e.y])
//             .join("L")}Z`
//       )
//       .attr("fill", "none")
//       .attr("stroke", "black")
//       .attr("stroke-width", .125);
  
//     // contour
//     svg
//       .append("g")
//       .append("path")
//       .attr(
//         "d",
//         d =>
//           `M${[[0, 0], [0, 1], [1, 0]]
//             .map(transform)
//             .map(e => [e.x, e.y])
//             .join("L")}Z`
//       )
//       .attr("fill", "none")
//       .attr("stroke", "black");
  
//     // data points
//     // svg
//     //   .append("g")
//     //   .selectAll()
//     //   .data(data)
//     //   .join("circle")
//     //   .attr("r", 1.5)
//     //   .attr("transform", d => {
//     //     const e = transform([+d.agriculture / 100, +d.industry / 100]);
//     //     return `translate(${[e.x, e.y]})`;
//     //   });
  
//     // numbers
//     // svg
//     //   .append("g")
//     //   .style("text-anchor", "middle")
//     //   .style("font-size", "13px")
//     //   .selectAll()
//     //   .data(bins)
//     //   .join("text")
//     //   .attr("transform", d => `translate(${[d.x, d.y]})`)
//     //   .text(d => d.values.length)
//     //   .attr("dy", "0.35em")
//     //   .call(g => g.clone(true))
//     //   .attr("stroke", "white")
//     //   .attr("stroke-width", 3);
  
//     // legend
//     // svg
//     //   .append("g")
//     //   .style("text-anchor", "middle")
//     //   .style("font-size", "13px")
//     //   .selectAll()
//     //   .data([
//     //     { label: "Agriculture", ...transform([1, 0]) },
//     //     { label: "Industry", ...transform([0, 1]) },
//     //     { label: "Services", ...transform([0, 0]) }
//     //   ])
//     //   .join("text")
//     //   .attr("transform", d => `translate(${[d.x, d.y]})`)
//     //   .text(d => d.label)
//     //   .attr("dy", "0.35em")
//     //   .call(g => g.clone(true))
//     //   .attr("stroke", "white")
//     //   .attr("stroke-width", 3);
  
    
//     return svg.node();
//   }