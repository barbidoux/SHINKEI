<script lang="ts">
    /**
     * UnifiedDiffViewer displays git-style unified diffs with syntax highlighting.
     * Supports additions (+), deletions (-), and context lines.
     */
    export let diff: string;
    export let title: string = "Changes";
    export let maxHeight: string = "500px";

    interface DiffLine {
        type: "added" | "removed" | "context" | "header" | "meta";
        content: string;
    }

    $: lines = parseDiff(diff);

    function parseDiff(diffText: string): DiffLine[] {
        if (!diffText) return [];

        return diffText.split("\n").map((line) => {
            if (line.startsWith("+++") || line.startsWith("---")) {
                return { type: "meta", content: line };
            } else if (line.startsWith("@@")) {
                return { type: "header", content: line };
            } else if (line.startsWith("+")) {
                return { type: "added", content: line };
            } else if (line.startsWith("-")) {
                return { type: "removed", content: line };
            } else if (line.startsWith("===")) {
                return { type: "meta", content: line };
            } else {
                return { type: "context", content: line };
            }
        });
    }

    function getLineClasses(type: DiffLine["type"]): string {
        switch (type) {
            case "added":
                return "bg-green-50 text-green-800 border-l-4 border-green-400";
            case "removed":
                return "bg-red-50 text-red-800 border-l-4 border-red-400";
            case "header":
                return "bg-blue-50 text-blue-700 font-semibold";
            case "meta":
                return "bg-gray-100 text-gray-600 font-semibold";
            case "context":
            default:
                return "bg-white text-gray-700";
        }
    }

    function getLinePrefix(type: DiffLine["type"]): string {
        switch (type) {
            case "added":
                return "+ ";
            case "removed":
                return "- ";
            default:
                return "  ";
        }
    }
</script>

<div class="unified-diff-viewer bg-gray-50 rounded-lg border border-gray-200">
    <div class="px-4 py-2 bg-gray-100 border-b border-gray-200">
        <h4 class="text-sm font-medium text-gray-700">{title}</h4>
    </div>

    <div
        class="overflow-auto font-mono text-xs"
        style="max-height: {maxHeight};"
    >
        {#if lines.length === 0}
            <div class="px-4 py-8 text-center text-gray-500">
                No changes to display
            </div>
        {:else}
            <table class="w-full border-collapse">
                <tbody>
                    {#each lines as line, index}
                        <tr class={getLineClasses(line.type)}>
                            <td
                                class="px-2 py-1 text-right text-gray-400 select-none w-12"
                            >
                                {#if line.type !== "meta" && line.type !== "header"}
                                    {index + 1}
                                {/if}
                            </td>
                            <td class="px-2 py-1 whitespace-pre-wrap break-all">
                                <span class="select-none text-gray-400"
                                    >{getLinePrefix(line.type)}</span
                                >
                                <span>{line.content.substring(1)}</span>
                            </td>
                        </tr>
                    {/each}
                </tbody>
            </table>
        {/if}
    </div>

    <div class="px-4 py-2 bg-gray-50 border-t border-gray-200 flex gap-4 text-xs">
        <div class="flex items-center gap-1">
            <div class="w-3 h-3 bg-green-100 border border-green-400 rounded"></div>
            <span class="text-gray-600">Additions</span>
        </div>
        <div class="flex items-center gap-1">
            <div class="w-3 h-3 bg-red-100 border border-red-400 rounded"></div>
            <span class="text-gray-600">Deletions</span>
        </div>
    </div>
</div>

<style>
    .unified-diff-viewer {
        font-family: "SF Mono", "Monaco", "Inconsolata", "Fira Code",
            "Fira Mono", "Roboto Mono", monospace;
    }

    table {
        border-spacing: 0;
    }

    tr {
        transition: background-color 0.1s ease;
    }

    tr:hover {
        filter: brightness(0.98);
    }
</style>
