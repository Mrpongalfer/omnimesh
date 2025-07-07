import { onCleanup, onMount, createSignal, createEffect } from 'solid-js';
import * as PIXI from 'pixi.js';
import * as d3 from 'd3';
import {
  selectedNode,
  setSelectedNode,
  setExplainableAI,
  nodes,
  agents,
  anomalies,
  flows,
} from '../store/appState';

export default function FabricMap() {
  let container: HTMLDivElement | undefined;
  let app: PIXI.Application | undefined;
  let d3Container: HTMLDivElement | undefined;
  let camera = { x: 0, y: 0, zoom: 1 };
  let dragging = false;
  let lastPos = { x: 0, y: 0 };

  const [focusedNodeIndex, setFocusedNodeIndex] = createSignal(0);
  const [showExplainableOverlay, setShowExplainableOverlay] =
    createSignal(false);

  // D3.js overlay for advanced data visualizations
  const createD3Overlays = () => {
    if (!d3Container) return;

    const svg = d3
      .select(d3Container)
      .append('svg')
      .attr('width', '100%')
      .attr('height', '100%')
      .style('position', 'absolute')
      .style('top', 0)
      .style('left', 0)
      .style('pointer-events', 'none')
      .style('z-index', 10);

    // Data flow visualization with D3
    const flowGroup = svg.append('g').attr('class', 'flows');

    createEffect(() => {
      const currentFlows = flows();
      const currentNodes = nodes();

      // Clear previous flows
      flowGroup.selectAll('*').remove();

      // Draw animated flow lines
      currentFlows.forEach((flow) => {
        const fromNode = currentNodes[flow.from];
        const toNode = currentNodes[flow.to];

        if (fromNode && toNode) {
          const line = flowGroup
            .append('line')
            .attr('x1', fromNode.x + camera.x + 300)
            .attr('y1', fromNode.y + camera.y + 200)
            .attr('x2', toNode.x + camera.x + 300)
            .attr('y2', toNode.y + camera.y + 200)
            .attr('stroke', '#00ff00')
            .attr('stroke-width', Math.max(1, flow.volume / 10))
            .attr('opacity', 0.7)
            .style('filter', 'drop-shadow(0 0 4px #00ff00)');

          // Animate flow direction
          line
            .append('animate')
            .attr('attributeName', 'stroke-dasharray')
            .attr('values', '0 10;10 0')
            .attr('dur', '1s')
            .attr('repeatCount', 'indefinite');
        }
      });
    });

    // Explainable AI overlay
    const aiOverlay = svg.append('g').attr('class', 'ai-overlay');

    createEffect(() => {
      if (showExplainableOverlay() && selectedNode()) {
        const node = nodes().find((n) => n.id === selectedNode());
        if (node) {
          aiOverlay.selectAll('*').remove();

          // AI explanation bubble
          const bubble = aiOverlay
            .append('g')
            .attr(
              'transform',
              `translate(${node.x + camera.x + 350}, ${node.y + camera.y + 150})`,
            );

          bubble
            .append('rect')
            .attr('x', 0)
            .attr('y', 0)
            .attr('width', 200)
            .attr('height', 80)
            .attr('rx', 10)
            .attr('fill', 'rgba(0, 100, 255, 0.9)')
            .attr('stroke', '#0066ff')
            .attr('stroke-width', 2);

          bubble
            .append('text')
            .attr('x', 10)
            .attr('y', 20)
            .attr('fill', 'white')
            .attr('font-size', '12px')
            .attr('font-weight', 'bold')
            .text('AI Analysis:');

          bubble
            .append('text')
            .attr('x', 10)
            .attr('y', 35)
            .attr('fill', 'white')
            .attr('font-size', '10px')
            .text(`Health: ${Math.round(node.health * 100)}%`);

          bubble
            .append('text')
            .attr('x', 10)
            .attr('y', 50)
            .attr('fill', 'white')
            .attr('font-size', '10px')
            .text(`Activity: ${Math.round(node.activity * 100)}%`);

          bubble
            .append('text')
            .attr('x', 10)
            .attr('y', 65)
            .attr('fill', 'white')
            .attr('font-size', '10px')
            .text('Optimal performance detected');
        }
      } else {
        aiOverlay.selectAll('*').remove();
      }
    });
  };

  onMount(() => {
    app = new PIXI.Application({
      resizeTo: container,
      backgroundColor: 0x18181b,
      antialias: true,
    });
    if (container) container.appendChild(app.view as HTMLCanvasElement);
    const cameraContainer = new PIXI.Container();
    app.stage.addChild(cameraContainer);

    // Draw resource flows (animated conduits)
    flows().forEach((flow) => {
      const nodeList = nodes();
      const from = nodeList[flow.from];
      const to = nodeList[flow.to];
      if (!from || !to) return;
      const line = new PIXI.Graphics();
      line.lineStyle(6 * flow.volume, 0x38bdf8, 0.7);
      line.moveTo(from.x + 70, from.y + 40);
      line.lineTo(to.x + 70, to.y + 40);
      cameraContainer.addChild(line);
    });

    // Draw nodes (apartments)
    nodes().forEach((node, idx) => {
      const g = new PIXI.Graphics();
      g.beginFill(selectedNode() === node.id ? 0xfbbf24 : 0x4ade80);
      g.drawRect(0, 0, 140, 80);
      g.endFill();
      g.x = node.x;
      g.y = node.y;
      g.interactive = true;
      // @ts-expect-error: buttonMode is supported in PixiJS runtime
      g.buttonMode = true;
      g.on('pointerdown', () => setSelectedNode(node.id));
      g.on('pointerover', () => {
        g.alpha = 0.8;
      });
      g.on('pointerout', () => {
        g.alpha = 1;
      });
      // Health bar
      const healthBar = new PIXI.Graphics();
      healthBar.beginFill(0x22d3ee);
      healthBar.drawRect(0, 0, 140 * node.health, 8);
      healthBar.endFill();
      healthBar.y = -12;
      g.addChild(healthBar);
      // Activity bar
      const activityBar = new PIXI.Graphics();
      activityBar.beginFill(0xf472b6);
      activityBar.drawRect(0, 0, 140 * node.activity, 6);
      activityBar.endFill();
      activityBar.y = 82;
      g.addChild(activityBar);
      // Node label
      const label = new PIXI.Text(`Node ${idx + 1}`, {
        fill: '#fff',
        fontSize: 16,
      });
      label.x = 10;
      label.y = 30;
      g.addChild(label);
      // Anomaly overlay
      if (anomalies().find((a) => a.node === idx)) {
        const anomaly = new PIXI.Graphics();
        anomaly.beginFill(0xf87171, 0.7);
        anomaly.drawCircle(120, 20, 16);
        anomaly.endFill();
        g.addChild(anomaly);
      }
      cameraContainer.addChild(g);
    });

    // Draw animated agent sprite
    agents().forEach((agent) => {
      const nodeList = nodes();
      const from = nodeList[agent.from];
      const to = nodeList[agent.to];
      if (!from || !to) return;
      const x = from.x + (to.x - from.x) * agent.progress + 70;
      const y = from.y + (to.y - from.y) * agent.progress + 40;
      const sprite = new PIXI.Graphics();
      sprite.beginFill(0x818cf8);
      sprite.drawCircle(0, 0, 18);
      sprite.endFill();
      sprite.x = x;
      sprite.y = y;
      // Progress overlay
      const progress = new PIXI.Graphics();
      progress.lineStyle(4, 0xfbbf24, 1);
      progress.arc(
        0,
        0,
        22,
        -Math.PI / 2,
        -Math.PI / 2 + Math.PI * 2 * agent.progress,
      );
      sprite.addChild(progress);
      cameraContainer.addChild(sprite);
    });

    // Panning/zooming logic
    app.view.addEventListener('wheel', (e: WheelEvent) => {
      camera.zoom *= e.deltaY < 0 ? 1.1 : 0.9;
      camera.zoom = Math.max(0.5, Math.min(2, camera.zoom));
      cameraContainer.scale.set(camera.zoom);
    });
    app.view.addEventListener('pointerdown', (e: PointerEvent) => {
      dragging = true;
      lastPos = { x: e.clientX, y: e.clientY };
    });
    app.view.addEventListener('pointermove', (e: PointerEvent) => {
      if (dragging) {
        camera.x += (e.clientX - lastPos.x) / camera.zoom;
        camera.y += (e.clientY - lastPos.y) / camera.zoom;
        cameraContainer.position.set(camera.x, camera.y);
        lastPos = { x: e.clientX, y: e.clientY };
      }
    });
    app.view.addEventListener('pointerup', () => {
      dragging = false;
    });
    app.view.addEventListener('pointerleave', () => {
      dragging = false;
    });
    // Touch/gesture support for panning/zooming
    app.view.addEventListener('touchstart', (e) => {
      dragging = true;
      lastPos = { x: e.touches[0].clientX, y: e.touches[0].clientY };
    });
    app.view.addEventListener('touchmove', (e) => {
      if (!dragging) return;
      const dx = e.touches[0].clientX - lastPos.x;
      const dy = e.touches[0].clientY - lastPos.y;
      camera.x += dx;
      camera.y += dy;
      cameraContainer.x = camera.x;
      cameraContainer.y = camera.y;
      lastPos = { x: e.touches[0].clientX, y: e.touches[0].clientY };
    });
    app.view.addEventListener('touchend', () => {
      dragging = false;
    });
    // Keyboard navigation for accessibility with enhanced focus management
    const handleKeyboardNavigation = (e: KeyboardEvent) => {
      const currentNodes = nodes();

      switch (e.key) {
        case 'ArrowRight':
          camera.x -= 40;
          break;
        case 'ArrowLeft':
          camera.x += 40;
          break;
        case 'ArrowUp':
          camera.y += 40;
          break;
        case 'ArrowDown':
          camera.y -= 40;
          break;
        case 'Tab':
          e.preventDefault();
          if (currentNodes.length > 0) {
            const nextIndex = e.shiftKey
              ? (focusedNodeIndex() - 1 + currentNodes.length) %
                currentNodes.length
              : (focusedNodeIndex() + 1) % currentNodes.length;
            setFocusedNodeIndex(nextIndex);
            setSelectedNode(currentNodes[nextIndex].id);
            setShowExplainableOverlay(true);
            setExplainableAI(
              `Node ${currentNodes[nextIndex].id} selected via keyboard navigation`,
            );
          }
          break;
        case 'Enter':
        case ' ':
          e.preventDefault();
          if (selectedNode()) {
            setShowExplainableOverlay(!showExplainableOverlay());
          }
          break;
        case 'Escape':
          setSelectedNode(null);
          setShowExplainableOverlay(false);
          setExplainableAI(null);
          break;
        case 'h':
          // Help overlay
          setExplainableAI(
            'Keyboard shortcuts: Arrow keys to pan, Tab to select nodes, Enter/Space to toggle details, Escape to deselect',
          );
          break;
      }

      if (cameraContainer) {
        cameraContainer.x = camera.x;
        cameraContainer.y = camera.y;
      }
    };

    window.addEventListener('keydown', handleKeyboardNavigation);

    // Enhanced accessibility with ARIA roles and focus management
    if (container) {
      container.setAttribute('role', 'application');
      container.setAttribute(
        'aria-label',
        'Fabric topology map with interactive nodes and flows',
      );
      container.setAttribute('tabindex', '0');
      container.style.outline = 'none';

      // Focus event handling
      container.addEventListener('focus', () => {
        setExplainableAI(
          'Fabric map focused. Use arrow keys to pan, Tab to navigate nodes, h for help',
        );
      });

      container.addEventListener('blur', () => {
        setExplainableAI(null);
      });
    }

    // Initialize D3 overlays
    createD3Overlays();

    // Enhanced node interaction with explainable AI
    const enhanceNodeInteraction = (
      nodeSprite: PIXI.Graphics,
      node: any,
      index: number,
    ) => {
      nodeSprite.interactive = true;
      nodeSprite.buttonMode = true;

      // Mouse events
      nodeSprite.on('pointerover', () => {
        setExplainableAI(
          `Node ${node.id}: Health ${Math.round(node.health * 100)}%, Activity ${Math.round(node.activity * 100)}%`,
        );
        nodeSprite.tint = 0x88ccff;
      });

      nodeSprite.on('pointerout', () => {
        if (selectedNode() !== node.id) {
          setExplainableAI(null);
          nodeSprite.tint = 0xffffff;
        }
      });

      nodeSprite.on('pointerdown', () => {
        setSelectedNode(node.id);
        setFocusedNodeIndex(index);
        setShowExplainableOverlay(true);
        setExplainableAI(
          `Node ${node.id} selected. Press Enter to toggle detailed analysis.`,
        );
      });
    };

    // Initialize D3 overlays after PIXI setup
    setTimeout(() => createD3Overlays(), 100);

    onCleanup(() => {
      window.removeEventListener('keydown', handleKeyboardNavigation);
      app?.destroy(true, { children: true });
    });
  });

  return (
    <div class="relative w-full h-full">
      <div
        ref={container}
        class="w-full h-full outline-none focus:ring-2 focus:ring-blue-400"
        tabIndex={0}
        aria-label="Fabric topology map with interactive nodes and flows"
        role="application"
      />
      <div
        ref={d3Container}
        class="absolute inset-0 pointer-events-none"
        style={{ 'z-index': '10' }}
      />
    </div>
  );
}
