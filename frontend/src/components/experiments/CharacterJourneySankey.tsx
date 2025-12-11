import React, { useEffect, useRef } from "react";
import * as d3 from "d3";
import type { CharacterJourney } from "../../services/experiments";

type Props = {
  data?: CharacterJourney;
  isLoading: boolean;
};

export const CharacterJourneySankey: React.FC<Props> = ({ data, isLoading }) => {
  const svgRef = useRef<SVGSVGElement>(null);

  useEffect(() => {
    if (!data || !svgRef.current) return;

    const svg = d3.select(svgRef.current);
    svg.selectAll("*").remove();

    const width = 1000;
    const height = 600;
    const margin = { top: 20, right: 20, bottom: 20, left: 20 };

    svg.attr("width", width).attr("height", height);

    // Group nodes by type
    const seasonNodes = data.nodes.filter((n) => n.type === "season");
    const charNodes = data.nodes.filter((n) => n.type === "character");

    const nodeHeight = 20;
    const seasonY = margin.top;
    const charY = height / 2;

    // Draw season nodes
    const seasonWidth = 80;
    const seasonSpacing = (width - margin.left - margin.right - seasonWidth * 7) / 6;
    seasonNodes.forEach((node, i) => {
      const x = margin.left + i * (seasonWidth + seasonSpacing);
      const g = svg.append("g").attr("class", "season-node");
      g.append("rect")
        .attr("x", x)
        .attr("y", seasonY)
        .attr("width", seasonWidth)
        .attr("height", nodeHeight)
        .attr("fill", "#4f46e5")
        .attr("rx", 4);
      g.append("text")
        .attr("x", x + seasonWidth / 2)
        .attr("y", seasonY + nodeHeight / 2)
        .attr("text-anchor", "middle")
        .attr("dominant-baseline", "middle")
        .attr("fill", "white")
        .attr("font-size", "11px")
        .attr("font-weight", "bold")
        .text(node.name);
    });

    // Draw character nodes
    const charWidth = 100;
    const charSpacing = 15;
    const totalCharWidth = charNodes.length * (charWidth + charSpacing) - charSpacing;
    const charStartX = (width - totalCharWidth) / 2;

    charNodes.forEach((node, i) => {
      const x = charStartX + i * (charWidth + charSpacing);
      const g = svg.append("g").attr("class", "char-node");
      g.append("rect")
        .attr("x", x)
        .attr("y", charY)
        .attr("width", charWidth)
        .attr("height", nodeHeight)
        .attr("fill", "#7c3aed")
        .attr("rx", 4);
      g.append("text")
        .attr("x", x + charWidth / 2)
        .attr("y", charY + nodeHeight / 2)
        .attr("text-anchor", "middle")
        .attr("dominant-baseline", "middle")
        .attr("fill", "white")
        .attr("font-size", "10px")
        .text(node.name);
    });

    // Create node position map
    const nodePositions = new Map<number, { x: number; y: number; width: number; height: number }>();
    seasonNodes.forEach((node, i) => {
      const idx = data.nodes.indexOf(node);
      const x = margin.left + i * (seasonWidth + seasonSpacing);
      nodePositions.set(idx, { x, y: seasonY, width: seasonWidth, height: nodeHeight });
    });
    charNodes.forEach((node, i) => {
      const idx = data.nodes.indexOf(node);
      const x = charStartX + i * (charWidth + charSpacing);
      nodePositions.set(idx, { x, y: charY, width: charWidth, height: nodeHeight });
    });

    // Draw Sankey links
    const linkG = svg.append("g").attr("class", "links");
    const maxValue = Math.max(...data.links.map((l) => l.value), 1);

    data.links.forEach((link) => {
      const source = nodePositions.get(link.source);
      const target = nodePositions.get(link.target);
      if (!source || !target) return;

      const path = d3.path();
      const sourceX = source.x + source.width;
      const sourceY = source.y + source.height / 2;
      const targetX = target.x;
      const targetY = target.y + target.height / 2;

      const linkWidth = Math.max(2, (link.value / maxValue) * 20);

      // Curved path
      path.moveTo(sourceX, sourceY);
      path.bezierCurveTo(
        sourceX + (targetX - sourceX) / 2,
        sourceY,
        sourceX + (targetX - sourceX) / 2,
        targetY,
        targetX,
        targetY
      );

      linkG
        .append("path")
        .attr("d", path.toString())
        .attr("fill", "none")
        .attr("stroke", "#4f46e5")
        .attr("stroke-width", linkWidth)
        .attr("stroke-opacity", 0.4)
        .append("title")
        .text(`Value: ${link.value}`);
    });
  }, [data]);

  if (isLoading) {
    return <div className="text-center py-20 text-gray-500">Loading character journey data...</div>;
  }

  if (!data) {
    return <div className="text-center py-20 text-red-500">Failed to load data</div>;
  }

  return (
    <div>
      <h2 className="text-xl font-semibold mb-4">Character Journey (Sankey Diagram)</h2>
      <p className="text-sm text-gray-600 mb-4">
        Flow from characters to seasons. Link thickness = episode count. Shows character presence across seasons.
      </p>
      <div className="border border-gray-200 rounded-lg overflow-hidden">
        <svg ref={svgRef} className="w-full" style={{ minHeight: "600px" }} />
      </div>
    </div>
  );
};


