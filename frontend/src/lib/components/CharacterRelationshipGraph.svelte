<script lang="ts">
	import { onMount, onDestroy } from 'svelte';
	import * as d3 from 'd3';
	import type { RelationshipNetworkResponse } from '$lib/types/relationship';

	export let worldId: string;
	export let apiUrl: string = '';

	interface GraphNode extends d3.SimulationNodeDatum {
		id: string;
		character_name: string;
		importance: string;
		x?: number;
		y?: number;
		fx?: number | null;
		fy?: number | null;
	}

	interface GraphEdge extends d3.SimulationLinkDatum<GraphNode> {
		relationship_id: string;
		relationship_type: string;
		strength: string;
		source: string | GraphNode;
		target: string | GraphNode;
	}

	let container: HTMLDivElement;
	let svg: d3.Selection<SVGSVGElement, unknown, null, undefined>;
	let simulation: d3.Simulation<GraphNode, GraphEdge>;
	let loading = true;
	let error = '';

	onMount(async () => {
		try {
			// Fetch graph data
			const response = await fetch(
				`${apiUrl}/api/v1/worlds/${worldId}/character-relationships/network`,
				{
					headers: {
						Authorization: `Bearer ${localStorage.getItem('auth_token')}`
					}
				}
			);

			if (!response.ok) {
				throw new Error('Failed to load relationship network');
			}

			const data: RelationshipNetworkResponse = await response.json();

			if (data.nodes.length === 0) {
				error = 'No characters found. Create some characters first to see the relationship network.';
				loading = false;
				return;
			}

			if (data.edges.length === 0) {
				error =
					'No relationships found. Create relationships between characters to see the network.';
				loading = false;
				return;
			}

			renderGraph(data);
			loading = false;
		} catch (e: any) {
			error = e.message || 'Failed to load relationship network';
			loading = false;
		}
	});

	function renderGraph(data: RelationshipNetworkResponse) {
		const width = container.clientWidth;
		const height = 600;

		// Transform data to D3 format
		const nodes: GraphNode[] = data.nodes.map((n) => ({
			id: n.character_id,
			character_name: n.character_name,
			importance: n.importance
		}));

		const edges: GraphEdge[] = data.edges.map((e) => ({
			relationship_id: e.relationship_id,
			source: e.from_character_id,
			target: e.to_character_id,
			relationship_type: e.relationship_type,
			strength: e.strength
		}));

		// Create SVG
		svg = d3
			.select(container)
			.append('svg')
			.attr('width', width)
			.attr('height', height)
			.attr('viewBox', [0, 0, width, height])
			.attr('style', 'max-width: 100%; height: auto;');

		// Add zoom behavior
		const g = svg.append('g');

		const zoom = d3
			.zoom<SVGSVGElement, unknown>()
			.scaleExtent([0.1, 4])
			.on('zoom', (event) => {
				g.attr('transform', event.transform);
			});

		svg.call(zoom);

		// Create arrow markers for edges
		svg
			.append('defs')
			.selectAll('marker')
			.data(['strong', 'moderate', 'weak'])
			.join('marker')
			.attr('id', (d) => `arrow-${d}`)
			.attr('viewBox', '0 -5 10 10')
			.attr('refX', 25)
			.attr('refY', 0)
			.attr('markerWidth', 6)
			.attr('markerHeight', 6)
			.attr('orient', 'auto')
			.append('path')
			.attr('fill', '#94a3b8')
			.attr('d', 'M0,-5L10,0L0,5');

		// Create force simulation
		simulation = d3
			.forceSimulation<GraphNode>(nodes)
			.force(
				'link',
				d3
					.forceLink<GraphNode, GraphEdge>(edges)
					.id((d) => d.id)
					.distance(150)
			)
			.force('charge', d3.forceManyBody().strength(-400))
			.force('center', d3.forceCenter(width / 2, height / 2))
			.force('collision', d3.forceCollide().radius(40));

		// Create links
		const link = g
			.append('g')
			.attr('stroke', '#94a3b8')
			.attr('stroke-opacity', 0.6)
			.selectAll('line')
			.data(edges)
			.join('line')
			.attr('stroke-width', (d) => getEdgeWidth(d.strength))
			.attr('marker-end', (d) => `url(#arrow-${d.strength})`);

		// Create nodes
		const node = g
			.append('g')
			.attr('stroke', '#fff')
			.attr('stroke-width', 2)
			.selectAll('g')
			.data(nodes)
			.join('g')
			.call(
				d3
					.drag<SVGGElement, GraphNode>()
					.on('start', dragstarted)
					.on('drag', dragged)
					.on('end', dragended) as any
			);

		// Add circles to nodes
		node
			.append('circle')
			.attr('r', (d) => getNodeRadius(d.importance))
			.attr('fill', (d) => getNodeColor(d.importance));

		// Add labels to nodes
		node
			.append('text')
			.attr('x', 0)
			.attr('y', (d) => getNodeRadius(d.importance) + 15)
			.attr('font-size', '12px')
			.attr('font-weight', 'bold')
			.attr('fill', '#1f2937')
			.attr('text-anchor', 'middle')
			.text((d) => d.character_name);

		// Add tooltip
		node.append('title').text((d) => `${d.character_name}\nImportance: ${d.importance}`);

		// Add edge labels
		const edgeLabels = g
			.append('g')
			.selectAll('text')
			.data(edges)
			.join('text')
			.attr('font-size', '9px')
			.attr('fill', '#64748b')
			.attr('text-anchor', 'middle')
			.text((d) => d.relationship_type);

		// Update positions on tick
		simulation.on('tick', () => {
			link
				.attr('x1', (d) => (d.source as GraphNode).x!)
				.attr('y1', (d) => (d.source as GraphNode).y!)
				.attr('x2', (d) => (d.target as GraphNode).x!)
				.attr('y2', (d) => (d.target as GraphNode).y!);

			node.attr('transform', (d) => `translate(${d.x},${d.y})`);

			// Position edge labels at midpoint
			edgeLabels
				.attr('x', (d) => ((d.source as GraphNode).x! + (d.target as GraphNode).x!) / 2)
				.attr('y', (d) => ((d.source as GraphNode).y! + (d.target as GraphNode).y!) / 2);
		});

		// Drag functions
		function dragstarted(event: any, d: GraphNode) {
			if (!event.active) simulation.alphaTarget(0.3).restart();
			d.fx = d.x;
			d.fy = d.y;
		}

		function dragged(event: any, d: GraphNode) {
			d.fx = event.x;
			d.fy = event.y;
		}

		function dragended(event: any, d: GraphNode) {
			if (!event.active) simulation.alphaTarget(0);
			d.fx = null;
			d.fy = null;
		}
	}

	function getNodeColor(importance: string): string {
		const colors: Record<string, string> = {
			major: '#9333ea', // Purple
			minor: '#3b82f6', // Blue
			background: '#94a3b8' // Gray
		};
		return colors[importance] || colors.background;
	}

	function getNodeRadius(importance: string): number {
		const radii: Record<string, number> = {
			major: 20,
			minor: 15,
			background: 10
		};
		return radii[importance] || 10;
	}

	function getEdgeWidth(strength: string): number {
		const widths: Record<string, number> = {
			strong: 4,
			moderate: 2.5,
			weak: 1.5
		};
		return widths[strength] || 2;
	}

	onDestroy(() => {
		if (simulation) {
			simulation.stop();
		}
	});
</script>

<div class="relationship-graph-container" bind:this={container}>
	{#if loading}
		<div class="flex items-center justify-center h-96">
			<div class="text-center">
				<svg
					class="animate-spin h-8 w-8 mx-auto mb-2 text-indigo-600"
					xmlns="http://www.w3.org/2000/svg"
					fill="none"
					viewBox="0 0 24 24"
				>
					<circle
						class="opacity-25"
						cx="12"
						cy="12"
						r="10"
						stroke="currentColor"
						stroke-width="4"
					></circle>
					<path
						class="opacity-75"
						fill="currentColor"
						d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
					></path>
				</svg>
				<p class="text-gray-600 dark:text-gray-400">Loading relationship network...</p>
			</div>
		</div>
	{:else if error}
		<div class="flex items-center justify-center h-96">
			<div class="text-center text-gray-600 dark:text-gray-400">
				<p>{error}</p>
			</div>
		</div>
	{/if}
</div>

<!-- Legend -->
{#if !loading && !error}
	<div class="mt-4 bg-white dark:bg-gray-800 rounded-lg shadow p-4 border border-gray-200 dark:border-gray-700">
		<h3 class="text-sm font-semibold text-gray-900 dark:text-white mb-3">Legend</h3>
		<div class="grid grid-cols-2 gap-4">
			<!-- Node Colors -->
			<div>
				<h4 class="text-xs font-medium text-gray-700 dark:text-gray-300 mb-2">Character Importance</h4>
				<div class="space-y-1">
					<div class="flex items-center gap-2">
						<div class="w-4 h-4 rounded-full bg-purple-600"></div>
						<span class="text-xs text-gray-600 dark:text-gray-400">Major</span>
					</div>
					<div class="flex items-center gap-2">
						<div class="w-3 h-3 rounded-full bg-blue-500"></div>
						<span class="text-xs text-gray-600 dark:text-gray-400">Minor</span>
					</div>
					<div class="flex items-center gap-2">
						<div class="w-2 h-2 rounded-full bg-gray-400"></div>
						<span class="text-xs text-gray-600 dark:text-gray-400">Background</span>
					</div>
				</div>
			</div>
			<!-- Edge Widths -->
			<div>
				<h4 class="text-xs font-medium text-gray-700 dark:text-gray-300 mb-2">Relationship Strength</h4>
				<div class="space-y-1">
					<div class="flex items-center gap-2">
						<div class="w-8 h-1 bg-gray-400"></div>
						<span class="text-xs text-gray-600 dark:text-gray-400">Strong</span>
					</div>
					<div class="flex items-center gap-2">
						<div class="w-8 h-0.5 bg-gray-400"></div>
						<span class="text-xs text-gray-600 dark:text-gray-400">Moderate</span>
					</div>
					<div class="flex items-center gap-2">
						<div class="w-8" style="height: 1px; background-color: #94a3b8;"></div>
						<span class="text-xs text-gray-600 dark:text-gray-400">Weak</span>
					</div>
				</div>
			</div>
		</div>
		<p class="mt-3 text-xs text-gray-500 dark:text-gray-400">
			Drag nodes to rearrange. Scroll to zoom. Edge labels show relationship types.
		</p>
	</div>
{/if}

<style>
	.relationship-graph-container {
		width: 100%;
		min-height: 600px;
		background: white;
		border-radius: 0.5rem;
		border: 1px solid #e5e7eb;
	}

	:global(.dark) .relationship-graph-container {
		background: #1f2937;
		border-color: #374151;
	}
</style>
