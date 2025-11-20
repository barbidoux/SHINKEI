<script lang="ts">
    import { toasts, type Toast } from "$lib/stores/toast";
    import { fly } from "svelte/transition";

    function getIcon(type: Toast["type"]) {
        switch (type) {
            case "success":
                return `<svg class="h-5 w-5 text-green-400" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.857-9.809a.75.75 0 00-1.214-.882l-3.483 4.79-1.88-1.88a.75.75 0 10-1.06 1.061l2.5 2.5a.75.75 0 001.137-.089l4-5.5z" clip-rule="evenodd" /></svg>`;
            case "error":
                return `<svg class="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.28 7.22a.75.75 0 00-1.06 1.06L8.94 10l-1.72 1.72a.75.75 0 101.06 1.06L10 11.06l1.72 1.72a.75.75 0 101.06-1.06L11.06 10l1.72-1.72a.75.75 0 00-1.06-1.06L10 8.94 8.28 7.22z" clip-rule="evenodd" /></svg>`;
            case "warning":
                return `<svg class="h-5 w-5 text-yellow-400" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M8.485 2.495c.673-1.167 2.357-1.167 3.03 0l6.28 10.875c.673 1.167-.17 2.625-1.516 2.625H3.72c-1.347 0-2.189-1.458-1.515-2.625L8.485 2.495zM10 5a.75.75 0 01.75.75v3.5a.75.75 0 01-1.5 0v-3.5A.75.75 0 0110 5zm0 9a1 1 0 100-2 1 1 0 000 2z" clip-rule="evenodd" /></svg>`;
            case "info":
                return `<svg class="h-5 w-5 text-blue-400" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a.75.75 0 000 1.5h.253a.25.25 0 01.244.304l-.459 2.066A1.75 1.75 0 0010.747 15H11a.75.75 0 000-1.5h-.253a.25.25 0 01-.244-.304l.459-2.066A1.75 1.75 0 009.253 9H9z" clip-rule="evenodd" /></svg>`;
        }
    }

    function getBackgroundClass(type: Toast["type"]) {
        switch (type) {
            case "success":
                return "bg-green-50";
            case "error":
                return "bg-red-50";
            case "warning":
                return "bg-yellow-50";
            case "info":
                return "bg-blue-50";
        }
    }
</script>

<div class="fixed top-4 right-4 z-50 flex flex-col gap-2 pointer-events-none">
    {#each $toasts as toast (toast.id)}
        <div
            transition:fly={{ x: 100, duration: 300 }}
            class="pointer-events-auto w-96 rounded-lg {getBackgroundClass(toast.type)} p-4 shadow-lg ring-1 ring-black ring-opacity-5"
        >
            <div class="flex items-start">
                <div class="flex-shrink-0">
                    {@html getIcon(toast.type)}
                </div>
                <div class="ml-3 flex-1">
                    <p class="text-sm font-medium text-gray-900">
                        {toast.message}
                    </p>
                </div>
                <div class="ml-4 flex flex-shrink-0">
                    <button
                        type="button"
                        class="inline-flex rounded-md hover:text-gray-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2"
                        on:click={() => toasts.remove(toast.id)}
                    >
                        <span class="sr-only">Close</span>
                        <svg class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                            <path d="M6.28 5.22a.75.75 0 00-1.06 1.06L8.94 10l-3.72 3.72a.75.75 0 101.06 1.06L10 11.06l3.72 3.72a.75.75 0 101.06-1.06L11.06 10l3.72-3.72a.75.75 0 00-1.06-1.06L10 8.94 6.28 5.22z" />
                        </svg>
                    </button>
                </div>
            </div>
        </div>
    {/each}
</div>
