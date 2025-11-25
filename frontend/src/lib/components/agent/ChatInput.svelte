<script lang="ts">
    import { createEventDispatcher } from 'svelte';

    export let disabled = false;
    export let placeholder = 'Ask Story Pilot...';

    const dispatch = createEventDispatcher<{
        send: string;
    }>();

    let message = '';
    let textareaEl: HTMLTextAreaElement;

    function handleSubmit() {
        const trimmed = message.trim();
        if (trimmed && !disabled) {
            dispatch('send', trimmed);
            message = '';
            // Reset textarea height
            if (textareaEl) {
                textareaEl.style.height = 'auto';
            }
        }
    }

    function handleKeydown(e: KeyboardEvent) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSubmit();
        }
    }

    // Auto-resize textarea
    function handleInput() {
        if (textareaEl) {
            textareaEl.style.height = 'auto';
            textareaEl.style.height = Math.min(textareaEl.scrollHeight, 150) + 'px';
        }
    }
</script>

<form on:submit|preventDefault={handleSubmit} class="flex gap-2">
    <div class="flex-1 relative">
        <textarea
            bind:this={textareaEl}
            bind:value={message}
            on:keydown={handleKeydown}
            on:input={handleInput}
            {disabled}
            {placeholder}
            rows="1"
            class="w-full px-3 py-2 pr-10 text-sm border border-gray-300 dark:border-gray-600 rounded-lg
                   bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100
                   placeholder-gray-500 dark:placeholder-gray-400
                   focus:ring-2 focus:ring-indigo-500 dark:focus:ring-indigo-400 focus:border-transparent
                   disabled:opacity-50 disabled:cursor-not-allowed
                   resize-none overflow-hidden"
            style="min-height: 38px; max-height: 150px;"
        ></textarea>

        <!-- Hint -->
        <div class="absolute right-2 bottom-2 text-xs text-gray-400 dark:text-gray-500 pointer-events-none">
            {#if !disabled}
                <kbd class="px-1 py-0.5 bg-gray-100 dark:bg-gray-600 rounded text-[10px]">Enter</kbd>
            {/if}
        </div>
    </div>

    <button
        type="submit"
        disabled={disabled || !message.trim()}
        class="flex-shrink-0 p-2 rounded-lg bg-indigo-600 dark:bg-indigo-500 text-white
               hover:bg-indigo-700 dark:hover:bg-indigo-600
               disabled:opacity-50 disabled:cursor-not-allowed
               transition-colors"
        title="Send message"
    >
        {#if disabled}
            <svg class="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
        {:else}
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
            </svg>
        {/if}
    </button>
</form>
