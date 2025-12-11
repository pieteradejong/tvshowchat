import React, { useEffect, useRef, useState } from "react";
import * as d3 from "d3";
import type { TemporalArc } from "../../services/experiments";

type Props = {
  data?: TemporalArc;
  isLoading: boolean;
};

export const TemporalArcExplorer: React.FC<Props> = ({ data, isLoading }) => {
  const svgRef = useRef<SVGSVGElement>(null);
  const [selectedCharacters, setSelectedCharacters] = useState<Set<string>>(new Set(["Buffy", "Willow", "Xander"]));

  useEffect(() => {
    if (!data || !svgRef.current) return;

    const svg = d3.select(svgRef.current);
    svg.selectAll("*").remove();

    const width = 1200;
    const height = 600;
    const margin = { top: 60, right: 100, bottom: 60, left: 80 };

    svg.attr("width", width).attr("height", height);

    const xScale = d3
      .scaleLinear()
      .domain([0, data.timeline.length - 1])
      .range([margin.left, width - margin.right]);

    const yScale = d3
      .scaleLinear()
      .domain([0, 100])
      .range([height - margin.bottom, margin.top]);

    // Draw character arcs
    const allCharacters = new Set<string>();
    data.timeline.forEach((ep) => {
      Object.keys(ep.characters).forEach((char) => allCharacters.add(char));
    });

    const characterList = Array.from(allCharacters).filter((c) => selectedCharacters.has(c));
    const colors = d3.scaleOrdinal(d3.schemeCategory10);

    characterList.forEach((char, idx) => {
      const lineData = data.timeline.map((ep, i) => ({
        x: i,
        y: ep.characters[char] || 0,
        episode: ep,
      }));

      const line = d3
        .line<{ x: number; y: number }>()
        .x((d) => xScale(d.x))
        .y((d) => yScale(d.y))
        .curve(d3.curveMonotoneX);

      svg
        .append("path")
        .datum(lineData)
        .attr("fill", "none")
        .attr("stroke", colors(idx.toString()))
        .attr("stroke-width", 2)
        .attr("d", line)
        .attr("opacity", 0.7);

      // Add dots for data points
      svg
        .selectAll(`.dot-${char}`)
        .data(lineData.filter((d) => d.y > 0))
        .enter()
        .append("circle")
        .attr("cx", (d) => xScale(d.x))
        .attr("cy", (d) => yScale(d.y))
        .attr("r", 3)
        .attr("fill", colors(idx.toString()))
        .style("cursor", "pointer")
        .on("mouseover", function (event, d) {
          d3.select(this).attr("r", 6);
          const tooltip = svg
            .append("g")
            .attr("class", "tooltip")
            .attr("transform", `translate(${xScale(d.x) + 10},${yScale(d.y)})`);
          tooltip
            .append("rect")
            .attr("width", 250)
            .attr("height", 60)
            .attr("fill", "rgba(0,0,0,0.8)")
            .attr("rx", 4);
          tooltip
            .append("text")
            .attr("x", 10)
            .attr("y", 20)
            .attr("fill", "white")
            .attr("font-size", "11px")
            .text(`S${d.episode.season}E${d.episode.episode}: ${d.episode.title}`);
          tooltip
            .append("text")
            .attr("x", 10)
            .attr("y", 40)
            .attr("fill", "white")
            .attr("font-size", "10px")
            .text(`${char}: ${d.y.toFixed(0)}`);
        })
        .on("mouseout", function () {
          d3.select(this).attr("r", 3);
          svg.selectAll(".tooltip").remove();
        });
    });

    // X-axis (episodes)
    const xAxis = d3.axisBottom(xScale).ticks(20).tickFormat((d, i) => {
      if (i >= data.timeline.length) return "";
      const ep = data.timeline[i];
      return `S${ep.season}E${ep.episode}`;
    });
    svg
      .append("g")
      .attr("transform", `translate(0,${height - margin.bottom})`)
      .call(xAxis)
      .selectAll("text")
      .attr("transform", "rotate(-45)")
      .attr("text-anchor", "end")
      .attr("font-size", "9px");

    // Y-axis (presence score)
    const yAxis = d3.axisLeft(yScale);
    svg.append("g").attr("transform", `translate(${margin.left},0)`).call(yAxis);

    // Labels
    svg
      .append("text")
      .attr("x", width / 2)
      .attr("y", height - 10)
      .attr("text-anchor", "middle")
      .attr("font-size", "12px")
      .attr("fill", "#374151")
      .text("Episodes (chronological)");

    svg
      .append("text")
      .attr("transform", "rotate(-90)")
      .attr("x", -height / 2)
      .attr("y", 30)
      .attr("text-anchor", "middle")
      .attr("font-size", "12px")
      .attr("fill", "#374151")
      .text("Character Presence Score");

    // Legend
    const legend = svg
      .append("g")
      .attr("transform", `translate(${width - margin.right + 20},${margin.top})`);
    legend
      .append("text")
      .attr("font-size", "12px")
      .attr("font-weight", "bold")
      .attr("fill", "#374151")
      .text("Characters");
    characterList.forEach((char, idx) => {
      const item = legend
        .append("g")
        .attr("transform", `translate(0,${20 + idx * 25})`)
        .style("cursor", "pointer")
        .on("click", () => {
          const newSet = new Set(selectedCharacters);
          if (newSet.has(char)) {
            newSet.delete(char);
          } else {
            newSet.add(char);
          }
          setSelectedCharacters(newSet);
        });
      item.append("line").attr("x1", 0).attr("x2", 20).attr("stroke", colors(idx.toString())).attr("stroke-width", 2);
      item.append("text").attr("x", 25).attr("y", 4).attr("font-size", "11px").text(char);
    });
  }, [data, selectedCharacters]);

  if (isLoading) {
    return <div className="text-center py-20 text-gray-500">Loading temporal arc data...</div>;
  }

  if (!data) {
    return <div className="text-center py-20 text-red-500">Failed to load data</div>;
  }

  return (
    <div>
      <h2 className="text-xl font-semibold mb-4">Temporal Arc Explorer</h2>
      <p className="text-sm text-gray-600 mb-4">
        Character presence over time. Click legend to toggle characters. Hover points for episode details.
      </p>
      <div className="border border-gray-200 rounded-lg overflow-hidden">
        <svg ref={svgRef} className="w-full" style={{ minHeight: "600px" }} />
      </div>
    </div>
  );
};


