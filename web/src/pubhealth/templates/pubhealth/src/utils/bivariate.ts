import * as d3 from 'd3'

let labels = ["low", "", "high"]

export let legend = () => {
    const k = 24;
    const arrow = DOM.uid();
    return svg`<g font-family=sans-serif font-size=10>
    <g transform="translate(-${k * n / 2},-${k * n / 2}) rotate(-45 ${k * n / 2},${k * n / 2})">
      <marker id="${arrow.id}" markerHeight=10 markerWidth=10 refX=6 refY=3 orient=auto>
        <path d="M0,0L9,3L0,6Z" />
      </marker>
      ${d3.cross(d3.range(n), d3.range(n)).map(([i, j]) => svg`<rect width=${k} height=${k} x=${i * k} y=${(n - 1 - j) * k} fill=${colors[j * n + i]}>
        <title>Diabetes${labels[j] && ` (${labels[j]})`}
  Obesity${labels[i] && ` (${labels[i]})`}</title>
      </rect>`)}
      <line marker-end="${arrow}" x1=0 x2=${n * k} y1=${n * k} y2=${n * k} stroke=black stroke-width=1.5 />
      <line marker-end="${arrow}" y2=0 y1=${n * k} stroke=black stroke-width=1.5 />
      <text font-weight="bold" dy="0.71em" transform="rotate(90) translate(${n / 2 * k},6)" text-anchor="middle">Diabetes}</text>
      <text font-weight="bold" dy="0.71em" transform="translate(${n / 2 * k},${n * k + 6})" text-anchor="middle">Obesity</text>
    </g>
  </g>`;
  }