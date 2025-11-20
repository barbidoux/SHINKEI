<script lang="ts">
    export let items: Array<{ label: string; href?: string }>;
</script>

<nav class="flex mb-6" aria-label="Breadcrumb">
    <ol class="inline-flex items-center space-x-1 md:space-x-3">
        {#each items as item, index}
            <li class="inline-flex items-center">
                {#if index > 0}
                    <svg
                        class="w-3 h-3 text-gray-400 mx-1"
                        aria-hidden="true"
                        xmlns="http://www.w3.org/2000/svg"
                        fill="none"
                        viewBox="0 0 6 10"
                    >
                        <path
                            stroke="currentColor"
                            stroke-linecap="round"
                            stroke-linejoin="round"
                            stroke-width="2"
                            d="m1 9 4-4-4-4"
                        />
                    </svg>
                {/if}
                {#if item.href && index < items.length - 1}
                    <a
                        href={item.href}
                        class="inline-flex items-center text-sm font-medium text-gray-700 hover:text-indigo-600"
                    >
                        {item.label}
                    </a>
                {:else}
                    <span
                        class="inline-flex items-center text-sm font-medium text-gray-500"
                    >
                        {item.label}
                    </span>
                {/if}
            </li>
        {/each}
    </ol>
</nav>
