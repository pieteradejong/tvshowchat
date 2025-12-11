import React, { useEffect, useRef } from "react";
import * as d3 from "d3";
import type { EpisodeSimilarity } from "../../services/experiments";

type Props = {
  data?: EpisodeSimilarity;
  isLoading: boolean;
};

export const EpisodeSimilarityMap: React.FC<Props> = ({ data, isLoading }) => {
  const svgRef = useRef<SVGSVGElement>(null);

  useEffect(() => {
    if (!data || !svgRef.current || data.episodes.length === 0) return;

    const svg = d3.select(svgRef.current);
    svg.selectAll("*").remove();

    const width = 1000;
    const height = 700;
    const margin = { top: 20, right: 20, bottom: 40, left: 40 };

    svg.attr("width", width).attr("height", height);

    // Simple 2D projection using season/episode as axes (can be enhanced with actual embedding projection)
    const xScale = d3
      .scaleLinear()
      .domain([1, 7])
      .range([margin.left, width - margin.right]);

    const yScale = d3
      .scaleLinear()
      .domain([1, 22])
      .range([margin.top, height - margin.bottom]);

    const seasonColors = d3.scaleOrdinal(d3.schemeCategory10);

    // Draw similarity links
    const linkG = svg.append("g").attr("class", "links");
    linkG
      .selectAll("line")
      .data(data.similarities.slice(0, 100)) // Limit for performance
      .enter()
      .append("line")
      .attr("x1", (d) => {
        const ep = data.episodes.find((e) => e.id === d.source);
        return ep ? xScale(ep.season) : 0;
      })
      .attr("y1", (d) => {
        const ep = data.episodes.find((e) => e.id === d.source);
        return ep ? yScale(ep.episode) : 0;
      })
      .attr("x2", (d) => {
        const ep = data.episodes.find((e) => e.id === d.target);
        return ep ? xScale(ep.season) : 0;
      })
      .attr("y2", (d) => {
        const ep = data.episodes.find((e) => e.id === d.target);
        return ep ? yScale(ep.episode) : 0;
      })
      .attr("stroke", "#4f46e5")
      .attr("stroke-opacity", (d) => d.similarity * 0.5)
      .attr("stroke-width", (d) => d.similarity * 2);

    // Draw episode nodes
    const nodeG = svg.append("g").attr("class", "nodes");
    const nodes = nodeG
      .selectAll("circle")
      .data(data.episodes)
      .enter()
      .append("circle")
      .attr("cx", (d) => xScale(d.season))
      .attr("cy", (d) => yScale(d.episode))
      .attr("r", 4)
      .attr("fill", (d) => seasonColors(d.season.toString()))
      .attr("stroke", "#fff")
      .attr("stroke-width", 1)
      .style("cursor", "pointer")
      .on("mouseover", function (event, d) {
        d3.select(this).attr("r", 8);
        const tooltip = svg
          .append("g")
          .attr("class", "tooltip")
          .attr("transform", `translate(${xScale(d.season) + 10},${yScale(d.episode)})`);
        tooltip
          .append("rect")
          .attr("width", 200)
          .attr("height", 40)
          .attr("fill", "rgba(0,0,0,0.8)")
          .attr("rx", 4);
        tooltip
          .append("text")
          .attr("x", 10)
          .attr("y", 20)
          .attr("fill", "white")
          .attr("font-size", "11px")
          .text(`S${d.season}E${d.episode}: ${d.title}`);
      })
      .on("mouseout", function () {
        d3.select(this).attr("r", 4);
        svg.selectAll(".tooltip").remove();
      });

    // Axes
    const xAxis = d3.axisBottom(xScale).tickFormat((d) => `S${d}`);
    const yAxis = d3.axisLeft(yScale).tickFormat((d) => `E${d}`);

    svg
      .append("g")
      .attr("transform", `translate(0,${height - margin.bottom})`)
      .call(xAxis)
      .append("text")
      .attr("x", width / 2)
      .attr("y", 35)
      .attr("fill", "#374151")
      .attr("text-anchor", "middle")
      .attr("font-size", "12px")
      .text("Season");

    svg
      .append("g")
      .attr("transform", `translate(${margin.left},0)`)
      .call(yAxis)
      .append("text")
      .attr("transform", "rotate(-90)")
      .attr("x", -height / 2)
      .attr("y", -25)
      .attr("fill", "#374151")
      .attr("text-anchor", "middle")
      .attr("font-size", "12px")
      .text("Episode");

    // Legend
    const legend = svg
      .append("g")
      .attr("transform", `translate(${width - 150},${margin.top})`);
    legend
      .append("text")
      .attr("font-size", "12px")
      .attr("font-weight", "bold")
      .attr("fill", "#374151")
      .text("Seasons");
    [1, 2, 3, 4, 5, 6, 7].forEach((s, i) => {
      const item = legend
        .append("g")
        .attr("transform", `translate(0,${20 + i * 20})`);
      item.append("circle").attr("r", 6).attr("fill", seasonColors(s.toString()));
      item.append("text").attr("x", 15).attr("y", 4).attr("font-size", "10px").text(`S${s}`);
    });
  }, [data]);

  if (isLoading) {
    return <div className="text-center py-20 text-gray-500">Loading episode similarity data...</div>;
  }

  if (!data || data.episodes.length === 0) {
    return <div className="text-center py-20 text-red-500">Failed to load data</div>;
  }

  return (
    <div>
      <h2 className="text-xl font-semibold mb-4">Episode Similarity Map</h2>
      <p className="text-sm text-gray-600 mb-4">
        Episodes positioned by season/episode. Links show semantic similarity. Hover for details.
      </p>
      <div className="border border-gray-200 rounded-lg overflow-hidden">
        <svg ref={svgRef} className="w-full" style={{ minHeight: "700px" }} />
      </div>
    </div>
  );
};


