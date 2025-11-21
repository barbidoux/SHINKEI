<script lang="ts">
    import { onMount, onDestroy } from "svelte";
    import * as d3 from "d3";

    export let worldId: string;
    export let apiUrl: string = "";

    interface GraphNode {
        id: string;
        label: string;
        t: number;
        type: string;
        summary: string;
        x?: number;
        y?: number;
        fx?: number | null;
        fy?: number | null;
    }

    interface GraphEdge {
        source: string | GraphNode;
        target: string | GraphNode;
        type: string;
    }

    interface GraphData {
        nodes: GraphNode[];
        edges: GraphEdge[];
        world_id: string;
    }

    let container: HTMLDivElement;
    let svg: d3.Selection<SVGSVGElement, unknown, null, undefined>;
    let simulation: d3.Simulation<GraphNode, GraphEdge>;
    let loading = true;
    let error = "";

    onMount(async () => {
        try {
            // Fetch graph data
            const response = await fetch(`${apiUrl}/api/v1/worlds/${worldId}/events/dependency-graph`, {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('auth_token')}`,
                }
            });

            if (!response.ok) {
                throw new Error('Failed to load dependency graph');
            }

            const data: GraphData = await response.json();

            if (data.nodes.length === 0) {
                error = "No events found. Create some events first to see the dependency graph.";
                loading = false;
                return;
            }

            renderGraph(data);
            loading = false;
        } catch (e: any) {
            error = e.message || "Failed to load dependency graph";
            loading = false;
        }
    });

    function renderGraph(data: GraphData) {
        const width = container.clientWidth;
        const height = 600;

        // Create SVG
        svg = d3.select(container)
            .append("svg")
            .attr("width", width)
            .attr("height", height)
            .attr("viewBox", [0, 0, width, height])
            .attr("style", "max-width: 100%; height: auto;");

        // Add zoom behavior
        const g = svg.append("g");

        const zoom = d3.zoom<SVGSVGElement, unknown>()
            .scaleExtent([0.1, 4])
            .on("zoom", (event) => {
                g.attr("transform", event.transform);
            });

        svg.call(zoom);

        // Create arrow markers for directed edges
        svg.append("defs").selectAll("marker")
            .data(["causes"])
            .join("marker")
            .attr("id", d => `arrow-${d}`)
            .attr("viewBox", "0 -5 10 10")
            .attr("refX", 20)
            .attr("refY", 0)
            .attr("markerWidth", 6)
            .attr("markerHeight", 6)
            .attr("orient", "auto")
            .append("path")
            .attr("fill", "#999")
            .attr("d", "M0,-5L10,0L0,5");

        // Create force simulation
        simulation = d3.forceSimulation<GraphNode>(data.nodes)
            .force("link", d3.forceLink<GraphNode, GraphEdge>(data.edges)
                .id(d => d.id)
                .distance(100))
            .force("charge", d3.forceManyBody().strength(-300))
            .force("center", d3.forceCenter(width / 2, height / 2))
            .force("collision", d3.forceCollide().radius(30));

        // Create links
        const link = g.append("g")
            .attr("stroke", "#999")
            .attr("stroke-opacity", 0.6)
            .selectAll("line")
            .data(data.edges)
            .join("line")
            .attr("stroke-width", 2)
            .attr("marker-end", "url(#arrow-causes)");

        // Create nodes
        const node = g.append("g")
            .attr("stroke", "#fff")
            .attr("stroke-width", 1.5)
            .selectAll("g")
            .data(data.nodes)
            .join("g")
            .call(d3.drag<SVGGElement, GraphNode>()
                .on("start", dragstarted)
                .on("drag", dragged)
                .on("end", dragended) as any);

        // Add circles to nodes
        node.append("circle")
            .attr("r", 8)
            .attr("fill", d => getNodeColor(d.type));

        // Add labels to nodes
        node.append("text")
            .attr("x", 12)
            .attr("y", 4)
            .attr("font-size", "10px")
            .attr("fill", "#333")
            .text(d => d.label);

        // Add tooltip
        node.append("title")
            .text(d => `${d.label}\nType: ${d.type}\nTime: ${d.t}\n${d.summary}`);

        // Update positions on tick
        simulation.on("tick", () => {
            link
                .attr("x1", d => (d.source as GraphNode).x!)
                .attr("y1", d => (d.source as GraphNode).y!)
                .attr("x2", d => (d.target as GraphNode).x!)
                .attr("y2", d => (d.target as GraphNode).y!);

            node.attr("transform", d => `translate(${d.x},${d.y})`);
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

    function getNodeColor(type: string): string {
        const colors: Record<string, string> = {
            incident: "#ef4444",
            glitch: "#f97316",
            meeting: "#3b82f6",
            discovery: "#10b981",
            conflict: "#dc2626",
            default: "#6366f1"
        };
        return colors[type] || colors.default;
    }

    onDestroy(() => {
        if (simulation) {
            simulation.stop();
        }
    });
</script>

<div class="event-dependency-graph">
    {#if loading}
        <div class="flex items-center justify-center h-96">
            <p class="text-gray-500">Loading dependency graph...</p>
        </div>
    {:else if error}
        <div class="flex items-center justify-center h-96">
            <div class="text-center">
                <p class="text-gray-500">{error}</p>
            </div>
        </div>
    {:else}
        <div class="mb-4 p-4 bg-gray-50 rounded-lg border border-gray-200">
            <h3 class="text-sm font-medium text-gray-900 mb-2">Legend</h3>
            <div class="flex flex-wrap gap-4 text-xs">
                <div class="flex items-center gap-2">
                    <div class="w-3 h-3 rounded-full bg-red-500"></div>
                    <span>Incident</span>
                </div>
                <div class="flex items-center gap-2">
                    <div class="w-3 h-3 rounded-full bg-orange-500"></div>
                    <span>Glitch</span>
                </div>
                <div class="flex items-center gap-2">
                    <div class="w-3 h-3 rounded-full bg-blue-500"></div>
                    <span>Meeting</span>
                </div>
                <div class="flex items-center gap-2">
                    <div class="w-3 h-3 rounded-full bg-green-500"></div>
                    <span>Discovery</span>
                </div>
                <div class="flex items-center gap-2">
                    <div class="w-3 h-3 rounded-full bg-red-600"></div>
                    <span>Conflict</span>
                </div>
                <div class="flex items-center gap-2">
                    <div class="w-3 h-3 rounded-full bg-indigo-500"></div>
                    <span>Other</span>
                </div>
            </div>
            <p class="mt-2 text-xs text-gray-500">
                Drag nodes to rearrange. Scroll to zoom. Arrows show cause → effect relationships.
            </p>
        </div>
        <div bind:this={container} class="border border-gray-300 rounded-lg bg-white"></div>
    {/if}
</div>

<style>
    .event-dependency-graph {
        width: 100%;
    }
</style>
