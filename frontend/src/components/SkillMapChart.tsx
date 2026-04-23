import React, { useEffect, useRef } from 'react';
import * as d3 from 'd3';
import type { SkillGraph, SkillNode, SkillPhase } from '../types/skills';

interface SkillMapChartProps {
  graph: SkillGraph;
  currentPhase?: SkillPhase;
  width?: number;
  height?: number;
  onSkillClick?: (skill: SkillNode) => void;
}

const PHASE_COLORS: Record<SkillPhase, string> = {
  define: '#6366f1',
  plan: '#8b5cf6',
  build: '#10b981',
  verify: '#f59e0b',
  review: '#ef4444',
  ship: '#3b82f6',
};

const PHASE_LABELS: Record<SkillPhase, string> = {
  define: 'Define',
  plan: 'Plan',
  build: 'Build',
  verify: 'Verify',
  review: 'Review',
  ship: 'Ship',
};

const SkillMapChart: React.FC<SkillMapChartProps> = ({
  graph,
  currentPhase,
  width = 1000,
  height = 600,
  onSkillClick,
}) => {
  const svgRef = useRef<SVGSVGElement>(null);

  useEffect(() => {
    if (!svgRef.current || graph.nodes.length === 0) return;

    const svg = d3.select(svgRef.current);
    svg.selectAll('*').remove();

    const nodes = graph.nodes.map((n) => ({ ...n }));
    const links = graph.edges
      .filter((e) => e.type === 'depends')
      .map((e) => ({ source: e.from, target: e.to }));

    const simulation = d3
      .forceSimulation(nodes as d3.SimulationNodeDatum[])
      .force(
        'link',
        d3
          .forceLink(links)
          .id((d: any) => d.id)
          .distance(120)
      )
      .force('charge', d3.forceManyBody().strength(-400))
      .force('center', d3.forceCenter(width / 2, height / 2))
      .force('x', d3.forceX(width / 2).strength(0.05))
      .force('y', d3.forceY(height / 2).strength(0.05));

    const link = svg
      .append('g')
      .attr('stroke', '#e5e7eb')
      .attr('stroke-width', 1.5)
      .selectAll('line')
      .data(links)
      .join('line')
      .attr('stroke-opacity', 0.6);

    const node = svg
      .append('g')
      .selectAll<SVGGElement, (typeof nodes)[0]>('g')
      .data(nodes)
      .join('g')
      .attr('cursor', 'pointer')
      .call(
        d3
          .drag<SVGGElement, (typeof nodes)[0]>()
          .on('start', (event, d: any) => {
            if (!event.active) simulation.alphaTarget(0.3).restart();
            d.fx = d.x;
            d.fy = d.y;
          })
          .on('drag', (event, d: any) => {
            d.fx = event.x;
            d.fy = event.y;
          })
          .on('end', (event, d: any) => {
            if (!event.active) simulation.alphaTarget(0);
            d.fx = null;
            d.fy = null;
          })
      );

    node
      .append('circle')
      .attr('r', 14)
      .attr('fill', (d: any) => PHASE_COLORS[d.phase as SkillPhase] || '#9ca3af')
      .attr('stroke', (d: any) => (d.phase === currentPhase ? '#1f2937' : 'white'))
      .attr('stroke-width', (d: any) => (d.phase === currentPhase ? 3 : 2))
      .attr('opacity', 0.9);

    node
      .append('text')
      .text((d: any) => (d.name.length > 18 ? d.name.substring(0, 16) + '…' : d.name))
      .attr('text-anchor', 'middle')
      .attr('dy', 28)
      .attr('font-size', 11)
      .attr('fill', '#374151')
      .attr('pointer-events', 'none');

    const phases: SkillPhase[] = ['define', 'plan', 'build', 'verify', 'review', 'ship'];
    const legend = svg.append('g').attr('transform', `translate(${width - 140}, 20)`);

    phases.forEach((phase, i) => {
      const g = legend.append('g').attr('transform', `translate(0, ${i * 22})`);
      g.append('circle').attr('r', 6).attr('fill', PHASE_COLORS[phase]);
      g.append('text')
        .text(PHASE_LABELS[phase])
        .attr('x', 14)
        .attr('y', 4)
        .attr('font-size', 12)
        .attr('fill', '#6b7280');
    });

    node.on('click', (_, d: any) => {
      onSkillClick?.(d as SkillNode);
    });

    simulation.on('tick', () => {
      link
        .attr('x1', (d: any) => d.source.x)
        .attr('y1', (d: any) => d.source.y)
        .attr('x2', (d: any) => d.target.x)
        .attr('y2', (d: any) => d.target.y);

      node.attr('transform', (d: any) => `translate(${d.x},${d.y})`);
    });

    return () => {
      simulation.stop();
    };
  }, [graph, currentPhase, width, height, onSkillClick]);

  return (
    <div style={{ position: 'relative' }}>
      <svg
        ref={svgRef}
        width={width}
        height={height}
        style={{ background: '#f9fafb', borderRadius: 12 }}
      />
    </div>
  );
};

export default SkillMapChart;
