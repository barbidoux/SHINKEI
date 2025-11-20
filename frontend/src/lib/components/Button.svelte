<script lang="ts">
    export let variant: "primary" | "secondary" | "danger" | "ghost" = "primary";
    export let size: "sm" | "md" | "lg" = "md";
    export let type: "button" | "submit" | "reset" = "button";
    export let disabled = false;
    export let loading = false;
    export let href: string | undefined = undefined;

    const baseClasses = "inline-flex items-center justify-center font-semibold rounded-md focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 transition-colors";

    const variantClasses = {
        primary: "bg-indigo-600 text-white shadow-sm hover:bg-indigo-500 focus-visible:outline-indigo-600 disabled:bg-indigo-300",
        secondary: "bg-white text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 hover:bg-gray-50 disabled:bg-gray-100",
        danger: "bg-red-600 text-white shadow-sm hover:bg-red-500 focus-visible:outline-red-600 disabled:bg-red-300",
        ghost: "text-gray-700 hover:bg-gray-100 disabled:text-gray-400"
    };

    const sizeClasses = {
        sm: "px-2 py-1 text-xs",
        md: "px-3 py-2 text-sm",
        lg: "px-4 py-2.5 text-base"
    };

    $: classes = `${baseClasses} ${variantClasses[variant]} ${sizeClasses[size]} ${disabled || loading ? 'opacity-50 cursor-not-allowed' : ''}`;
</script>

{#if href && !disabled && !loading}
    <a {href} class={classes}>
        {#if loading}
            <svg class="animate-spin -ml-1 mr-2 h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
        {/if}
        <slot />
    </a>
{:else}
    <button {type} {disabled} class={classes} on:click>
        {#if loading}
            <svg class="animate-spin -ml-1 mr-2 h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
        {/if}
        <slot />
    </button>
{/if}
