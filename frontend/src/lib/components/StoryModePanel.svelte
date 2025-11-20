<script lang="ts">
    export let mode: "autonomous" | "collaborative" | "manual" = "manual";
    export let storyId: string;
    export let beatCount: number = 0;

    $: modeConfig = getModeConfig(mode);

    interface ModeConfig {
        title: string;
        description: string;
        color: string;
        icon: string;
        tips: string[];
        features: string[];
    }

    function getModeConfig(m: string): ModeConfig {
        switch (m) {
            case "autonomous":
                return {
                    title: "Autonomous Mode",
                    description:
                        "AI generates the complete narrative with minimal human intervention.",
                    color: "blue",
                    icon: "🤖",
                    tips: [
                        "Use the generation panel to create beats automatically",
                        "AI will maintain consistency with world events and story context",
                        "Review generated beats and use 'Modify with AI' for adjustments",
                        "Link beats to world events for cross-story coherence",
                    ],
                    features: [
                        "Automatic beat generation",
                        "AI-driven narrative progression",
                        "Context-aware storytelling",
                        "Minimal manual editing required",
                    ],
                };
            case "collaborative":
                return {
                    title: "Collaborative Mode",
                    description:
                        "AI proposes content while you guide, edit, and refine the narrative.",
                    color: "purple",
                    icon: "🤝",
                    tips: [
                        "Generate AI proposals using the generation panel",
                        "Review and edit generated content before accepting",
                        "Use 'Modify with AI' to refine specific beats",
                        "Add manual beats to complement AI-generated content",
                    ],
                    features: [
                        "AI-assisted generation",
                        "Manual editing and refinement",
                        "Flexible creative control",
                        "Best of both worlds",
                    ],
                };
            case "manual":
            default:
                return {
                    title: "Manual Mode",
                    description:
                        "Full creative control - write your narrative entirely by hand with AI assistance when needed.",
                    color: "green",
                    icon: "✍️",
                    tips: [
                        "Create beats manually using '+ Create Beat Manually'",
                        "Use AI to generate ideas when you need inspiration",
                        "Link beats to world events for story intersections",
                        "Reorder beats with drag-and-drop as you refine your narrative",
                    ],
                    features: [
                        "Complete creative freedom",
                        "Manual beat creation and editing",
                        "Optional AI assistance",
                        "Full narrative control",
                    ],
                };
        }
    }
</script>

<div class="story-mode-panel bg-white rounded-lg border border-gray-200 shadow-sm overflow-hidden">
    <!-- Header -->
    <div class="bg-gradient-to-r from-{modeConfig.color}-50 to-{modeConfig.color}-100 px-6 py-4 border-b border-{modeConfig.color}-200">
        <div class="flex items-center gap-3">
            <span class="text-3xl">{modeConfig.icon}</span>
            <div>
                <h3 class="text-lg font-semibold text-gray-900">
                    {modeConfig.title}
                </h3>
                <p class="text-sm text-gray-600 mt-0.5">
                    {modeConfig.description}
                </p>
            </div>
        </div>
    </div>

    <!-- Content -->
    <div class="p-6">
        <div class="grid md:grid-cols-2 gap-6">
            <!-- Tips -->
            <div>
                <h4 class="text-sm font-semibold text-gray-900 mb-3">
                    💡 Quick Tips
                </h4>
                <ul class="space-y-2">
                    {#each modeConfig.tips as tip}
                        <li class="flex items-start gap-2 text-sm text-gray-600">
                            <svg
                                class="h-5 w-5 text-{modeConfig.color}-500 flex-shrink-0 mt-0.5"
                                fill="currentColor"
                                viewBox="0 0 20 20"
                            >
                                <path
                                    fill-rule="evenodd"
                                    d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                                    clip-rule="evenodd"
                                />
                            </svg>
                            <span>{tip}</span>
                        </li>
                    {/each}
                </ul>
            </div>

            <!-- Features -->
            <div>
                <h4 class="text-sm font-semibold text-gray-900 mb-3">
                    ✨ Mode Features
                </h4>
                <ul class="space-y-2">
                    {#each modeConfig.features as feature}
                        <li class="flex items-start gap-2 text-sm text-gray-600">
                            <svg
                                class="h-5 w-5 text-{modeConfig.color}-500 flex-shrink-0 mt-0.5"
                                fill="none"
                                viewBox="0 0 24 24"
                                stroke="currentColor"
                            >
                                <path
                                    stroke-linecap="round"
                                    stroke-linejoin="round"
                                    stroke-width="2"
                                    d="M13 10V3L4 14h7v7l9-11h-7z"
                                />
                            </svg>
                            <span>{feature}</span>
                        </li>
                    {/each}
                </ul>
            </div>
        </div>

        <!-- Stats -->
        {#if beatCount > 0}
            <div class="mt-6 pt-6 border-t border-gray-200">
                <div class="flex items-center gap-4 text-sm">
                    <div class="flex items-center gap-2">
                        <svg
                            class="h-5 w-5 text-gray-400"
                            fill="none"
                            viewBox="0 0 24 24"
                            stroke="currentColor"
                        >
                            <path
                                stroke-linecap="round"
                                stroke-linejoin="round"
                                stroke-width="2"
                                d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                            />
                        </svg>
                        <span class="text-gray-600">
                            <span class="font-semibold text-gray-900"
                                >{beatCount}</span
                            >
                            {beatCount === 1 ? "beat" : "beats"} in this story
                        </span>
                    </div>
                </div>
            </div>
        {/if}
    </div>
</div>

<style>
    .story-mode-panel {
        width: 100%;
    }

    /* Tailwind dynamic color classes need safelist or inline styles */
    /* Using generic styling that works with all modes */
</style>
