// src/services/visualizationManager.ts
// Advanced data visualization service using D3.js for Omnitide UI

import * as d3 from 'd3';
import type { Node, Agent, Flow, Anomaly } from '../store/appState';

export interface VisualizationConfig {
  width: number;
  height: number;
  container: HTMLElement;
  theme: 'dark' | 'light';
}

export interface NetworkGraphData {
  nodes: Node[];
  links: Flow[];
  agents: Agent[];
  anomalies: Anomaly[];
}

export class NetworkGraphVisualization {
  private svg: d3.Selection<SVGSVGElement, unknown, null, undefined>;
  private simulation: d3.Simulation<Node, undefined>;
  private config: VisualizationConfig;
  private nodeGroup: d3.Selection<SVGGElement, unknown, null, undefined>;
  private linkGroup: d3.Selection<SVGGElement, unknown, null, undefined>;
  private agentGroup: d3.Selection<SVGGElement, unknown, null, undefined>;

  constructor(config: VisualizationConfig) {
    this.config = config;
    this.svg = d3
      .select(config.container)
      .append('svg')
      .attr('width', config.width)
      .attr('height', config.height)
      .attr('class', 'network-graph');

    // Create groups for different elements
    this.linkGroup = this.svg.append('g').attr('class', 'links');
    this.nodeGroup = this.svg.append('g').attr('class', 'nodes');
    this.agentGroup = this.svg.append('g').attr('class', 'agents');

    // Initialize force simulation
    this.simulation = d3
      .forceSimulation<Node>()
      .force(
        'link',
        d3
          .forceLink<Node, Flow>()
          .id((d) => d.id)
          .distance(100),
      )
      .force('charge', d3.forceManyBody().strength(-300))
      .force('center', d3.forceCenter(config.width / 2, config.height / 2));

    this.setupZoomBehavior();
    this.setupTooltip();
  }

  private setupZoomBehavior(): void {
    const zoom = d3
      .zoom<SVGSVGElement, unknown>()
      .scaleExtent([0.1, 4])
      .on('zoom', (event) => {
        const { transform } = event;
        this.nodeGroup.attr('transform', transform);
        this.linkGroup.attr('transform', transform);
        this.agentGroup.attr('transform', transform);
      });

    this.svg.call(zoom);
  }

  private setupTooltip(): void {
    // Create tooltip element
    d3.select(this.config.container)
      .append('div')
      .attr('class', 'tooltip')
      .style('position', 'absolute')
      .style('visibility', 'hidden')
      .style('background', 'rgba(0, 0, 0, 0.8)')
      .style('color', 'white')
      .style('padding', '8px')
      .style('border-radius', '4px')
      .style('font-size', '12px')
      .style('pointer-events', 'none')
      .style('z-index', '1000');
  }

  public updateData(data: NetworkGraphData): void {
    this.updateLinks(data.links);
    this.updateNodes(data.nodes, data.anomalies);
    this.updateAgents(data.agents, data.nodes);
    this.simulation.nodes(data.nodes);
    this.simulation.force<d3.ForceLink<Node, Flow>>('link')?.links(data.links);
    this.simulation.alpha(0.3).restart();
  }

  private updateLinks(links: Flow[]): void {
    const linkSelection = this.linkGroup
      .selectAll<SVGLineElement, Flow>('line')
      .data(links, (d) => `${d.from}-${d.to}`);

    // Remove old links
    linkSelection.exit().remove();

    // Add new links
    const newLinks = linkSelection
      .enter()
      .append('line')
      .attr('stroke', this.config.theme === 'dark' ? '#64748b' : '#94a3b8')
      .attr('stroke-opacity', 0.6)
      .attr('stroke-width', (d) => Math.sqrt(d.volume) * 2);

    // Update all links
    linkSelection
      .merge(newLinks)
      .attr('stroke-width', (d) => Math.sqrt(d.volume) * 2)
      .attr('stroke', (d) => {
        const intensity = d.volume / 100; // Normalize volume
        return d3.interpolateViridis(intensity);
      });

    // Add flow animation
    linkSelection
      .merge(newLinks)
      .append('animate')
      .attr('attributeName', 'stroke-dasharray')
      .attr('values', '0 10;10 0')
      .attr('dur', '2s')
      .attr('repeatCount', 'indefinite');
  }

  private updateNodes(nodes: Node[], anomalies: Anomaly[]): void {
    const nodeSelection = this.nodeGroup
      .selectAll<SVGGElement, Node>('g')
      .data(nodes, (d) => d.id);

    // Remove old nodes
    nodeSelection.exit().remove();

    // Add new nodes
    const newNodes = nodeSelection.enter().append('g').attr('class', 'node');

    // Add circles for nodes
    newNodes
      .append('circle')
      .attr('r', 20)
      .attr('fill', (d) => this.getNodeColor(d, anomalies))
      .attr('stroke', '#fff')
      .attr('stroke-width', 2);

    // Add health indicator
    newNodes
      .append('circle')
      .attr('r', 15)
      .attr('fill', 'none')
      .attr('stroke', (d) => d3.interpolateRdYlGn(d.health))
      .attr('stroke-width', 3)
      .attr('stroke-dasharray', (d) => `${d.health * 94} 94`);

    // Add labels
    newNodes
      .append('text')
      .attr('dy', 35)
      .attr('text-anchor', 'middle')
      .attr('fill', this.config.theme === 'dark' ? '#fff' : '#000')
      .style('font-size', '10px')
      .text((d) => d.id);

    // Add activity pulse animation
    newNodes
      .append('circle')
      .attr('r', 20)
      .attr('fill', 'none')
      .attr('stroke', '#3b82f6')
      .attr('stroke-width', 2)
      .attr('opacity', 0)
      .each(function (d) {
        if (d.activity > 0.5) {
          d3.select(this)
            .append('animate')
            .attr('attributeName', 'r')
            .attr('values', '20;35;20')
            .attr('dur', '2s')
            .attr('repeatCount', 'indefinite');

          d3.select(this)
            .append('animate')
            .attr('attributeName', 'opacity')
            .attr('values', '0.7;0;0.7')
            .attr('dur', '2s')
            .attr('repeatCount', 'indefinite');
        }
      });

    // Update existing nodes
    const allNodes = nodeSelection.merge(newNodes);

    allNodes
      .select('circle')
      .attr('fill', (d) => this.getNodeColor(d, anomalies));

    allNodes
      .select('circle:nth-child(2)')
      .attr('stroke', (d) => d3.interpolateRdYlGn(d.health))
      .attr('stroke-dasharray', (d) => `${d.health * 94} 94`);

    // Add interaction
    allNodes
      .style('cursor', 'pointer')
      .on('mouseover', (event, d) => this.showTooltip(event, d))
      .on('mouseout', () => this.hideTooltip())
      .on('click', (event, d) => this.onNodeClick(d));

    // Apply drag behavior
    allNodes.call(
      d3
        .drag<SVGGElement, Node>()
        .on('start', (event, d) => this.onDragStart(event, d))
        .on('drag', (event, d) => this.onDrag(event, d))
        .on('end', (event, d) => this.onDragEnd(event, d)),
    );
  }

  private updateAgents(agents: Agent[], nodes: Node[]): void {
    const agentSelection = this.agentGroup
      .selectAll<SVGGElement, Agent>('g')
      .data(agents, (d) => d.id);

    // Remove old agents
    agentSelection.exit().remove();

    // Add new agents
    const newAgents = agentSelection.enter().append('g').attr('class', 'agent');

    newAgents
      .append('circle')
      .attr('r', 8)
      .attr('fill', '#10b981')
      .attr('stroke', '#fff')
      .attr('stroke-width', 1);

    newAgents
      .append('text')
      .attr('dy', -12)
      .attr('text-anchor', 'middle')
      .attr('fill', this.config.theme === 'dark' ? '#fff' : '#000')
      .style('font-size', '8px')
      .text('🤖');

    // Animate agent movement
    const allAgents = agentSelection.merge(newAgents);

    allAgents.each(function (d) {
      const fromNode = nodes[d.from];
      const toNode = nodes[d.to];

      if (fromNode && toNode) {
        const startX = fromNode.x || 0;
        const startY = fromNode.y || 0;
        const endX = toNode.x || 0;
        const endY = toNode.y || 0;

        const currentX = startX + (endX - startX) * d.progress;
        const currentY = startY + (endY - startY) * d.progress;

        d3.select(this)
          .transition()
          .duration(1000)
          .attr('transform', `translate(${currentX}, ${currentY})`);
      }
    });
  }

  private getNodeColor(node: Node, anomalies: Anomaly[]): string {
    const hasAnomaly = anomalies.some((a) => a.node.toString() === node.id);
    if (hasAnomaly) return '#ef4444'; // Red for anomalies
    if (node.health < 0.3) return '#f59e0b'; // Amber for low health
    if (node.activity > 0.8) return '#3b82f6'; // Blue for high activity
    return '#10b981'; // Green for normal
  }

  private showTooltip(event: MouseEvent, node: Node): void {
    const tooltip = d3.select(this.config.container).select('.tooltip');
    tooltip
      .style('visibility', 'visible')
      .html(
        `
        <strong>${node.id}</strong><br/>
        Health: ${Math.round(node.health * 100)}%<br/>
        Activity: ${Math.round(node.activity * 100)}%
      `,
      )
      .style('left', `${event.offsetX + 10}px`)
      .style('top', `${event.offsetY - 10}px`);
  }

  private hideTooltip(): void {
    d3.select(this.config.container)
      .select('.tooltip')
      .style('visibility', 'hidden');
  }

  private onNodeClick(node: Node): void {
    // Emit custom event for node selection
    const event = new CustomEvent('nodeSelected', {
      detail: { nodeId: node.id },
    });
    this.config.container.dispatchEvent(event);
  }

  private onDragStart(
    event: d3.D3DragEvent<SVGGElement, Node, Node>,
    d: Node,
  ): void {
    if (!event.active) this.simulation.alphaTarget(0.3).restart();
    d.fx = d.x;
    d.fy = d.y;
  }

  private onDrag(
    event: d3.D3DragEvent<SVGGElement, Node, Node>,
    d: Node,
  ): void {
    d.fx = event.x;
    d.fy = event.y;
  }

  private onDragEnd(
    event: d3.D3DragEvent<SVGGElement, Node, Node>,
    d: Node,
  ): void {
    if (!event.active) this.simulation.alphaTarget(0);
    d.fx = null;
    d.fy = null;
  }

  public destroy(): void {
    this.simulation.stop();
    this.svg.remove();
    d3.select(this.config.container).select('.tooltip').remove();
  }
}

// Factory function for creating visualizations
export function createNetworkVisualization(
  config: VisualizationConfig,
): NetworkGraphVisualization {
  return new NetworkGraphVisualization(config);
}

// Utility functions for visualization data processing
export function processFlowData(flows: Flow[]): Flow[] {
  // Add flow aggregation, filtering, and normalization
  const flowMap = new Map<string, Flow>();

  flows.forEach((flow) => {
    const key = `${flow.from}-${flow.to}`;
    const existing = flowMap.get(key);

    if (existing) {
      existing.volume += flow.volume;
    } else {
      flowMap.set(key, { ...flow });
    }
  });

  return Array.from(flowMap.values());
}

export function calculateNetworkMetrics(data: NetworkGraphData): {
  density: number;
  avgDegree: number;
  clusteringCoefficient: number;
  centralityScores: Map<string, number>;
} {
  const nodeCount = data.nodes.length;
  const edgeCount = data.links.length;

  // Network density
  const maxEdges = (nodeCount * (nodeCount - 1)) / 2;
  const density = maxEdges > 0 ? edgeCount / maxEdges : 0;

  // Average degree
  const avgDegree = nodeCount > 0 ? (2 * edgeCount) / nodeCount : 0;

  // Simplified clustering coefficient
  const clusteringCoefficient = density; // Simplified calculation

  // Basic centrality scores (degree centrality)
  const centralityScores = new Map<string, number>();
  data.nodes.forEach((node) => {
    const degree = data.links.filter(
      (link) =>
        link.from.toString() === node.id || link.to.toString() === node.id,
    ).length;
    centralityScores.set(node.id, degree);
  });

  return {
    density,
    avgDegree,
    clusteringCoefficient,
    centralityScores,
  };
}
