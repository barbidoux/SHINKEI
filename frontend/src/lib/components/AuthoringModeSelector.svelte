<script lang="ts">
    import { api } from "$lib/api";

    export let currentMode: "autonomous" | "collaborative" | "manual";
    export let storyId: string;
    export let beatCount: number = 0;
    export let onChange: (newMode: string) => void;

    let updating = false;

    interface ModeOption {
        value: string;
        label: string;
        icon: string;
        description: string;
        color: string;
    }

    const modes: ModeOption[] = [
        {
            value: "autonomous",
            label: "Autonomous",
            icon: "🤖",
            description: "AI writes everything automatically",
            color: "indigo"
        },
        {
            value: "collaborative",
            label: "Collaborative",
            icon: "🤝",
            description: "AI proposes, you refine and choose",
            color: "purple"
        },
        {
            value: "manual",
            label: "Manual",
            icon: "✍️",
            description: "You write, AI assists with coherence",
            color: "blue"
        }
    ];

    async function handleModeChange(newMode: string) {
        if (updating) return;

        // Warn if story has existing beats
        if (beatCount > 0 && currentMode !== newMode) {
            const confirmed = confirm(
                `This story has ${beatCount} beat${beatCount === 1 ? '' : 's'} written in ${currentMode} mode.\n\n` +
                `Switching to ${newMode} mode may affect narrative flow and consistency.\n\n` +
                `Do you want to continue?`
            );
            if (!confirmed) return;
        }

        updating = true;

        try {
            // Update story mode via API
            await api.put(`/stories/${storyId}`, { mode: newMode });

            // Notify parent component
            onChange(newMode);

            // Show success message
            alert(`Authoring mode changed to ${newMode}`);
        } catch (e: any) {
            alert(`Failed to change mode: ${e.message}`);
        } finally {
            updating = false;
        }
    }

    function getModeColor(mode: ModeOption): string {
        const colors: Record<string, { bg: string; border: string; text: string }> = {
            indigo: {
                bg: "bg-indigo-50",
                border: "border-indigo-500",
                text: "text-indigo-700"
            },
            purple: {
                bg: "bg-purple-50",
                border: "border-purple-500",
                text: "text-purple-700"
            },
            blue: {
                bg: "bg-blue-50",
                border: "border-blue-500",
                text: "text-blue-700"
            }
        };
        return colors[mode.color] || colors.blue;
    }
</script>

<div class="authoring-mode-selector">
    <h3 class="text-sm font-medium text-gray-700 mb-3">Authoring Mode</h3>

    <div class="grid grid-cols-3 gap-3">
        {#each modes as mode}
            {@const isSelected = currentMode === mode.value}
            {@const colorClasses = getModeColor(mode)}

            <button
                type="button"
                on:click={() => handleModeChange(mode.value)}
                disabled={updating || isSelected}
                class="
                    relative rounded-lg border-2 p-4 text-left transition-all
                    {isSelected
                        ? `${colorClasses.border} ${colorClasses.bg} shadow-md`
                        : 'border-gray-200 bg-white hover:border-gray-300 hover:shadow-sm'}
                    {updating ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
                "
                class:ring-2={isSelected}
                class:ring-offset-2={isSelected}
            >
                <!-- Selection indicator -->
                {#if isSelected}
                    <div class="absolute top-2 right-2">
                        <svg class="h-5 w-5 {colorClasses.text}" fill="currentColor" viewBox="0 0 20 20">
                            <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd" />
                        </svg>
                    </div>
                {/if}

                <!-- Mode content -->
                <div class="flex items-center gap-3 mb-2">
                    <span class="text-2xl">{mode.icon}</span>
                    <span class="font-semibold text-gray-900 text-sm">
                        {mode.label}
                    </span>
                </div>

                <p class="text-xs text-gray-600 leading-relaxed">
                    {mode.description}
                </p>
            </button>
        {/each}
    </div>

    {#if beatCount > 0}
        <p class="mt-3 text-xs text-gray-500 italic">
            💡 Tip: This story has {beatCount} beat{beatCount === 1 ? '' : 's'}.
            Changing modes will affect how future beats are created.
        </p>
    {/if}
</div>

<style>
    .authoring-mode-selector {
        margin-bottom: 1.5rem;
    }
</style>
