import React, { useEffect, useRef, useState } from "react";
import * as d3 from "d3";
import type { ThemeCooccurrence } from "../../services/experiments";

// d3-force mutates its inputs, so it gets copies, never the react-query cache.
type ThemeNode = d3.SimulationNodeDatum & { id: string; count: number };
type ThemeLink = d3.SimulationLinkDatum<ThemeNode> & { value: number };

type Props = {
  data?: ThemeCooccurrence;
  isLoading: boolean;
};

export const ThemeCooccurrenceMatrix: React.FC<Props> = ({ data, isLoading }) => {
  const svgRef = useRef<SVGSVGElement>(null);
  const [selectedTheme, setSelectedTheme] = useState<string | null>(null);

  useEffect(() => {
    if (!data || !svgRef.current) return;

    const svg = d3.select(svgRef.current);
    svg.selectAll("*").remove();

    const width = 1000;
    const height = 800;
    const cellSize = 20;
    const margin = { top: 100, right: 100, bottom: 100, left: 100 };

    svg.attr("width", width).attr("height", height);

    const maxValue = Math.max(...data.matrix.flat());
    const colorScale = d3.scaleSequential(d3.interpolateBlues).domain([0, maxValue]);

    // Draw heatmap
    const g = svg.append("g").attr("transform", `translate(${margin.left},${margin.top})`);

    g
      .selectAll("rect")
      .data(data.matrix.flatMap((row, i) => row.map((val, j) => ({ i, j, val }))))
      .enter()
      .append("rect")
      .attr("x", (d) => d.j * cellSize)
      .attr("y", (d) => d.i * cellSize)
      .attr("width", cellSize)
      .attr("height", cellSize)
      .attr("fill", (d) => colorScale(d.val))
      .attr("stroke", "#fff")
      .attr("stroke-width", 0.5)
      .style("cursor", "pointer")
      .on("mouseover", function (event, d) {
        d3.select(this).attr("stroke-width", 2).attr("stroke", "#ef4444");
        const theme1 = data.themes[d.i];
        const theme2 = data.themes[d.j];
        const [mx, my] = d3.pointer(event, svg.node());
        const tooltip = svg
          .append("g")
          .attr("class", "tooltip")
          .attr("transform", `translate(${mx + 10},${my})`);
        tooltip
          .append("rect")
          .attr("width", 200)
          .attr("height", 50)
          .attr("fill", "rgba(0,0,0,0.8)")
          .attr("rx", 4);
        tooltip
          .append("text")
          .attr("x", 10)
          .attr("y", 20)
          .attr("fill", "white")
          .attr("font-size", "12px")
          .text(`${theme1} × ${theme2}: ${d.val}`);
      })
      .on("mouseout", function () {
        d3.select(this).attr("stroke-width", 0.5).attr("stroke", "#fff");
        svg.selectAll(".tooltip").remove();
      });

    // X-axis labels
    g.selectAll(".x-label")
      .data(data.themes)
      .enter()
      .append("text")
      .attr("class", "x-label")
      .attr("x", (d, i) => i * cellSize + cellSize / 2 + d.length * 0)
      .attr("y", -5)
      .attr("text-anchor", "end")
      .attr("transform", (d, i) => `rotate(-45, ${i * cellSize + cellSize / 2}, ${-5 - d.length * 0})`)
      .attr("font-size", "10px")
      .attr("fill", "#374151")
      .text((d) => d);

    // Y-axis labels
    g.selectAll(".y-label")
      .data(data.themes)
      .enter()
      .append("text")
      .attr("class", "y-label")
      .attr("x", -5)
      .attr("y", (d, i) => i * cellSize + cellSize / 2 + d.length * 0)
      .attr("text-anchor", "end")
      .attr("font-size", "10px")
      .attr("fill", "#374151")
      .text((d) => d);

    // Network view
    const networkWidth = 400;
    const networkHeight = 400;
    const networkG = svg
      .append("g")
      .attr("transform", `translate(${width - networkWidth - 50},${margin.top})`);

    // The simulation positions these same objects, so render from them too.
    const themeNodes: ThemeNode[] = data.themes.map((t) => ({ id: t, count: data.episode_counts[t] }));
    const themeLinks: ThemeLink[] = data.links.map((l) => ({ ...l }));

    const simulation = d3
      .forceSimulation<ThemeNode>(themeNodes)
      .force(
        "link",
        d3
          .forceLink<ThemeNode, ThemeLink>(themeLinks)
          .id((d) => d.id)
          .distance(50)
      )
      .force("charge", d3.forceManyBody().strength(-100))
      .force("center", d3.forceCenter(networkWidth / 2, networkHeight / 2));

    const networkLinks = networkG
      .append("g")
      .selectAll("line")
      .data(themeLinks)
      .enter()
      .append("line")
      .attr("stroke", "#4f46e5")
      .attr("stroke-opacity", 0.3)
      .attr("stroke-width", (d) => Math.sqrt(d.value));

    const networkNodes = networkG
      .append("g")
      .selectAll("circle")
      .data(themeNodes)
      .enter()
      .append("circle")
      .attr("r", (d) => Math.sqrt(d.count) * 2)
      .attr("fill", "#4f46e5")
      .attr("opacity", 0.7)
      .style("cursor", "pointer")
      .on("click", (event, d) => {
        event.stopPropagation();
        setSelectedTheme(d.id === selectedTheme ? null : d.id);
      });

    const networkLabels = networkG
      .append("g")
      .selectAll("text")
      .data(themeNodes)
      .enter()
      .append("text")
      .text((d) => d.id)
      .attr("font-size", "9px")
      .attr("dx", 8)
      .attr("dy", 3)
      .attr("fill", "#374151");

    simulation.on("tick", () => {
      networkLinks
        .attr("x1", (d) => (d.source as ThemeNode).x ?? 0)
        .attr("y1", (d) => (d.source as ThemeNode).y ?? 0)
        .attr("x2", (d) => (d.target as ThemeNode).x ?? 0)
        .attr("y2", (d) => (d.target as ThemeNode).y ?? 0);
      networkNodes.attr("cx", (d) => d.x ?? 0).attr("cy", (d) => d.y ?? 0);
      networkLabels.attr("x", (d) => d.x ?? 0).attr("y", (d) => d.y ?? 0);
    });
  }, [data, selectedTheme]);

  if (isLoading) {
    return <div className="text-center py-20 text-gray-500">Loading theme data...</div>;
  }

  if (!data) {
    return <div className="text-center py-20 text-red-500">Failed to load data</div>;
  }

  return (
    <div>
      <h2 className="text-xl font-semibold mb-4">Theme Co-occurrence Matrix</h2>
      <p className="text-sm text-gray-600 mb-4">
        Heatmap shows theme co-occurrence. Network shows theme relationships. Hover cells for details.
      </p>
      <div className="border border-gray-200 rounded-lg overflow-hidden">
        <svg ref={svgRef} className="w-full" style={{ minHeight: "800px" }} />
      </div>
    </div>
  );
};


