import React, { useEffect, useRef } from "react";
import * as d3 from "d3";
import type { CharacterRelationships } from "../../services/experiments";

type Props = {
  data?: CharacterRelationships;
  isLoading: boolean;
};

export const CharacterNetwork: React.FC<Props> = ({ data, isLoading }) => {
  const svgRef = useRef<SVGSVGElement>(null);

  useEffect(() => {
    if (!data || !svgRef.current) return;

    const svg = d3.select(svgRef.current);
    svg.selectAll("*").remove();

    const width = 1000;
    const height = 700;
    svg.attr("width", width).attr("height", height);

    const simulation = d3
      .forceSimulation(data.nodes as any)
      .force(
        "link",
        d3.forceLink(data.links).id((d: any) => d.id).distance((d: any) => 200 - d.value * 5)
      )
      .force("charge", d3.forceManyBody().strength(-300))
      .force("center", d3.forceCenter(width / 2, height / 2))
      .force("collision", d3.forceCollide().radius((d: any) => d.size + 5));

    const link = svg
      .append("g")
      .selectAll("line")
      .data(data.links)
      .enter()
      .append("line")
      .attr("stroke", "#999")
      .attr("stroke-opacity", 0.6)
      .attr("stroke-width", (d) => Math.sqrt(d.value) * 2);

    const node = svg
      .append("g")
      .selectAll("circle")
      .data(data.nodes)
      .enter()
      .append("circle")
      .attr("r", (d) => d.size)
      .attr("fill", (d) => {
        const colors = ["#4f46e5", "#7c3aed", "#ec4899", "#f59e0b", "#10b981"];
        return colors[d.episode_count % colors.length];
      })
      .call(
        d3
          .drag<any, any>()
          .on("start", (event, d) => {
            if (!event.active) simulation.alphaTarget(0.3).restart();
            d.fx = d.x;
            d.fy = d.y;
          })
          .on("drag", (event, d) => {
            d.fx = event.x;
            d.fy = event.y;
          })
          .on("end", (event, d) => {
            if (!event.active) simulation.alphaTarget(0);
            d.fx = null;
            d.fy = null;
          })
      );

    const label = svg
      .append("g")
      .selectAll("text")
      .data(data.nodes)
      .enter()
      .append("text")
      .text((d) => d.name)
      .attr("font-size", "12px")
      .attr("dx", 15)
      .attr("dy", 4)
      .attr("fill", "#374151")
      .attr("font-weight", "500");

    node.append("title").text((d) => `${d.name}: ${d.episode_count} episodes`);

    simulation.on("tick", () => {
      link
        .attr("x1", (d: any) => d.source.x)
        .attr("y1", (d: any) => d.source.y)
        .attr("x2", (d: any) => d.target.x)
        .attr("y2", (d: any) => d.target.y);

      node.attr("cx", (d: any) => d.x).attr("cy", (d: any) => d.y);
      label.attr("x", (d: any) => d.x).attr("y", (d: any) => d.y);
    });
  }, [data]);

  if (isLoading) {
    return <div className="text-center py-20 text-gray-500">Loading character network...</div>;
  }

  if (!data) {
    return <div className="text-center py-20 text-red-500">Failed to load data</div>;
  }

  return (
    <div>
      <h2 className="text-xl font-semibold mb-4">Character Relationship Network</h2>
      <p className="text-sm text-gray-600 mb-4">
        Drag nodes to explore. Node size = episode count. Link thickness = co-appearance strength.
      </p>
      <div className="border border-gray-200 rounded-lg overflow-hidden">
        <svg ref={svgRef} className="w-full" style={{ minHeight: "700px" }} />
      </div>
    </div>
  );
};


