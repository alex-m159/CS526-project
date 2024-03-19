import * as d3 from 'd3'
import {Library} from '@observablehq/stdlib'

let labels = ["low", "med", "high"]
const library = new Library()
const DOM = library.DOM
const svg = library.svg
export const bivaraite_side_length = 3
export const bivariate_colors = [
    "#e8e8e8", "#ace4e4", "#5ac8c8",
    "#dfb0d6", "#a5add3", "#5698b9", 
    "#be64ac", "#8c62aa", "#3b4994"
  ]
  
export let legend = (x_label: string, y_label: string, x_quantile: number[], y_quantile: number[] ) => {
    const k = 24;
    const arrow = DOM.uid()
    // <g transform="translate(-${k * n / 2},-${k * n / 2}) rotate(-45 ${k * n / 2},${k * n / 2})">
    // Defined the height manually since the SVG standard does NOT allow the height/size of the SVG element to 
    // be determined by its contents, meaning that an SVG element's height will not expand to display the whole
    // content, so we have to do that manually or through javascript.
    return `
    <svg style="height: 200px">
        <g font-family=sans-serif font-size=10>
            <g transform="translate(30, 20) scale(2)">
                <marker id="${arrow.id}" markerHeight=10 markerWidth=10 refX=6 refY=3 orient=auto>
                    <path d="M0,0L9,3L0,6Z" />
                </marker>
                ${
                    d3.cross(d3.range(bivaraite_side_length), d3.range(bivaraite_side_length)).map(([i, j]) => 
                        `<rect width=${k} height=${k} x=${i * k} y=${(bivaraite_side_length - 1 - j) * k} fill=${bivariate_colors[j * bivaraite_side_length + i]}>
                            <title>
                                ${y_label}${` (${labels[j]})`} ${x_label}${labels[i] && ` (${labels[i]})`}
                            </title>
                        </rect>`
                    ).join('')
                }
                <line marker-end="${arrow}" x1=0 x2=${bivaraite_side_length * k} y1=${bivaraite_side_length * k} y2=${bivaraite_side_length * k} stroke=black stroke-width=1.5 />
                <line marker-end="${arrow}" y2=0 y1=${bivaraite_side_length * k} stroke=black stroke-width=1.5 />
                <text font-weight="bold" dy="0.71em" transform="rotate(90) translate(${bivaraite_side_length / 2 * k},6)" text-anchor="middle">${y_label}</text>
                <text font-weight="bold" dy="0.71em" transform="translate(${bivaraite_side_length / 2 * k},${bivaraite_side_length * k + 6})" text-anchor="middle">${x_label}</text>
            </g>
        </g>
    </svg>`;
  }

  window.legend = legend
  window.library = library