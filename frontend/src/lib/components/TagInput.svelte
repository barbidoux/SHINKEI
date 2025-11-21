<script lang="ts">
    import { createEventDispatcher } from "svelte";

    export let tags: string[] = [];
    export let worldId: string | undefined = undefined;
    export let maxTags = 20;
    export let maxLength = 50;
    export let placeholder = "Add tags...";
    export let disabled = false;

    const dispatch = createEventDispatcher<{ change: string[] }>();

    let inputValue = "";
    let suggestions: string[] = [];
    let showSuggestions = false;
    let selectedSuggestionIndex = -1;
    let error = "";

    // Fetch existing tags for autocomplete
    async function fetchWorldTags() {
        if (!worldId) return;

        try {
            const response = await fetch(`/api/v1/worlds/${worldId}/stories/tags`, {
                headers: {
                    Authorization: `Bearer ${localStorage.getItem("token")}`,
                },
            });

            if (response.ok) {
                const data = await response.json();
                suggestions = data.tags || [];
            }
        } catch (err) {
            console.error("Failed to fetch tags:", err);
        }
    }

    $: if (worldId) {
        fetchWorldTags();
    }

    $: filteredSuggestions = inputValue
        ? suggestions.filter(
              (tag) =>
                  tag.toLowerCase().includes(inputValue.toLowerCase()) &&
                  !tags.includes(tag)
          )
        : [];

    function addTag(tag: string) {
        error = "";
        const trimmed = tag.trim();

        if (!trimmed) return;

        if (tags.length >= maxTags) {
            error = `Maximum ${maxTags} tags allowed`;
            return;
        }

        if (trimmed.length > maxLength) {
            error = `Tag must be ${maxLength} characters or less`;
            return;
        }

        if (tags.includes(trimmed)) {
            error = "Tag already added";
            return;
        }

        tags = [...tags, trimmed];
        inputValue = "";
        showSuggestions = false;
        selectedSuggestionIndex = -1;
        dispatch("change", tags);
    }

    function removeTag(index: number) {
        error = "";
        tags = tags.filter((_, i) => i !== index);
        dispatch("change", tags);
    }

    function handleKeydown(e: KeyboardEvent) {
        if (e.key === "Enter" || e.key === ",") {
            e.preventDefault();
            if (selectedSuggestionIndex >= 0 && filteredSuggestions.length > 0) {
                addTag(filteredSuggestions[selectedSuggestionIndex]);
            } else {
                addTag(inputValue);
            }
        } else if (e.key === "Backspace" && !inputValue && tags.length > 0) {
            removeTag(tags.length - 1);
        } else if (e.key === "ArrowDown" && filteredSuggestions.length > 0) {
            e.preventDefault();
            selectedSuggestionIndex = Math.min(
                selectedSuggestionIndex + 1,
                filteredSuggestions.length - 1
            );
        } else if (e.key === "ArrowUp" && filteredSuggestions.length > 0) {
            e.preventDefault();
            selectedSuggestionIndex = Math.max(selectedSuggestionIndex - 1, -1);
        } else if (e.key === "Escape") {
            showSuggestions = false;
            selectedSuggestionIndex = -1;
        }
    }

    function handleInput() {
        error = "";
        showSuggestions = inputValue.length > 0;
        selectedSuggestionIndex = -1;
    }

    function handleBlur() {
        // Delay to allow click on suggestion
        setTimeout(() => {
            showSuggestions = false;
            selectedSuggestionIndex = -1;
        }, 200);
    }
</script>

<div class="space-y-2">
    <!-- Tag chips display -->
    {#if tags.length > 0}
        <div class="flex flex-wrap gap-2">
            {#each tags as tag, index}
                <span
                    class="inline-flex items-center gap-1 rounded-full bg-indigo-100 dark:bg-indigo-900 px-3 py-1 text-sm font-medium text-indigo-700 dark:text-indigo-200"
                >
                    {tag}
                    {#if !disabled}
                        <button
                            type="button"
                            on:click={() => removeTag(index)}
                            class="inline-flex items-center justify-center w-4 h-4 rounded-full hover:bg-indigo-200 dark:hover:bg-indigo-800 transition-colors"
                            aria-label="Remove {tag}"
                        >
                            <svg class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                            </svg>
                        </button>
                    {/if}
                </span>
            {/each}
        </div>
    {/if}

    <!-- Input field -->
    <div class="relative">
        <input
            type="text"
            bind:value={inputValue}
            on:keydown={handleKeydown}
            on:input={handleInput}
            on:focus={handleInput}
            on:blur={handleBlur}
            {disabled}
            {placeholder}
            class="block w-full rounded-md border-0 py-1.5 px-3 text-gray-900 dark:text-gray-100 shadow-sm ring-1 ring-inset ring-gray-300 dark:ring-gray-600 placeholder:text-gray-400 dark:placeholder:text-gray-500 focus:ring-2 focus:ring-inset focus:ring-indigo-600 dark:focus:ring-indigo-500 sm:text-sm sm:leading-6 bg-white dark:bg-gray-800 disabled:bg-gray-100 dark:disabled:bg-gray-900 disabled:cursor-not-allowed"
        />

        <!-- Autocomplete dropdown -->
        {#if showSuggestions && filteredSuggestions.length > 0}
            <div
                class="absolute z-10 mt-1 w-full rounded-md bg-white dark:bg-gray-800 shadow-lg ring-1 ring-black dark:ring-gray-700 ring-opacity-5 max-h-60 overflow-auto"
            >
                <ul class="py-1">
                    {#each filteredSuggestions as suggestion, index}
                        <li>
                            <button
                                type="button"
                                on:click={() => addTag(suggestion)}
                                class="block w-full text-left px-4 py-2 text-sm text-gray-700 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-700 {index ===
                                selectedSuggestionIndex
                                    ? 'bg-gray-100 dark:bg-gray-700'
                                    : ''}"
                            >
                                {suggestion}
                            </button>
                        </li>
                    {/each}
                </ul>
            </div>
        {/if}
    </div>

    <!-- Error message -->
    {#if error}
        <p class="text-sm text-red-600 dark:text-red-400">{error}</p>
    {/if}

    <!-- Helper text -->
    <p class="text-sm text-gray-500 dark:text-gray-400">
        {tags.length}/{maxTags} tags • Press Enter or comma to add • {#if worldId}Autocomplete available{/if}
    </p>
</div>
