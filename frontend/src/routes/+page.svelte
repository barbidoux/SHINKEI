<script lang="ts">
    import { auth } from "$lib/stores/auth";
    import { goto } from "$app/navigation";
    import { onMount } from "svelte";

    // Redirect authenticated users to worlds dashboard
    onMount(() => {
        if ($auth.isAuthenticated) {
            goto("/worlds");
        }
    });
</script>

<div class="relative bg-white dark:bg-gray-900">
    <div class="mx-auto max-w-7xl px-4 py-24 sm:px-6 lg:px-8">
        <div class="text-center">
            <h1 class="text-5xl font-bold tracking-tight text-gray-900 dark:text-white sm:text-6xl">
                Welcome to <span class="text-indigo-600 dark:text-indigo-400">Shinkei</span>
            </h1>
            <p class="mt-6 text-xl leading-8 text-gray-600 dark:text-gray-300">
                The Narrative Engine for interconnected inner worlds.
            </p>
            <p class="mt-4 text-lg text-gray-500 dark:text-gray-400">
                Create self-contained narrative universes with stories that intersect through shared world events on a global timeline.
            </p>
            <div class="mt-10 flex items-center justify-center gap-x-6">
                <a
                    href="/register"
                    class="rounded-md bg-indigo-600 px-6 py-3 text-base font-semibold text-white shadow-sm hover:bg-indigo-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600 transition-colors"
                >
                    Get Started
                </a>
                <a
                    href="/login"
                    class="text-base font-semibold leading-7 text-gray-900 dark:text-white hover:text-indigo-600 dark:hover:text-indigo-400 transition-colors"
                >
                    Sign in <span aria-hidden="true">→</span>
                </a>
            </div>
        </div>

        <div class="mt-20 grid grid-cols-1 gap-8 sm:grid-cols-2 lg:grid-cols-3">
            <div class="relative rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 p-8">
                <div class="mb-4">
                    <svg class="h-8 w-8 text-indigo-600 dark:text-indigo-400" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M12 21a9.004 9.004 0 008.716-6.747M12 21a9.004 9.004 0 01-8.716-6.747M12 21c2.485 0 4.5-4.03 4.5-9S14.485 3 12 3m0 18c-2.485 0-4.5-4.03-4.5-9S9.515 3 12 3m0 0a8.997 8.997 0 017.843 4.582M12 3a8.997 8.997 0 00-7.843 4.582m15.686 0A11.953 11.953 0 0112 10.5c-2.998 0-5.74-1.1-7.843-2.918m15.686 0A8.959 8.959 0 0121 12c0 .778-.099 1.533-.284 2.253m0 0A17.919 17.919 0 0112 16.5c-3.162 0-6.133-.815-8.716-2.247m0 0A9.015 9.015 0 013 12c0-1.605.42-3.113 1.157-4.418" />
                    </svg>
                </div>
                <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-2">Create Worlds</h3>
                <p class="text-gray-600 dark:text-gray-300">
                    Build self-contained narrative universes with customizable tone, laws, and chronology modes.
                </p>
            </div>

            <div class="relative rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 p-8">
                <div class="mb-4">
                    <svg class="h-8 w-8 text-indigo-600 dark:text-indigo-400" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M12 6.042A8.967 8.967 0 006 3.75c-1.052 0-2.062.18-3 .512v14.25A8.987 8.987 0 016 18c2.305 0 4.408.867 6 2.292m0-14.25a8.966 8.966 0 016-2.292c1.052 0 2.062.18 3 .512v14.25A8.987 8.987 0 0018 18a8.967 8.967 0 00-6 2.292m0-14.25v14.25" />
                    </svg>
                </div>
                <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-2">Write Stories</h3>
                <p class="text-gray-600 dark:text-gray-300">
                    Use AI-powered generation in autonomous, collaborative, or manual modes to craft your narratives.
                </p>
            </div>

            <div class="relative rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 p-8">
                <div class="mb-4">
                    <svg class="h-8 w-8 text-indigo-600 dark:text-indigo-400" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M13.19 8.688a4.5 4.5 0 011.242 7.244l-4.5 4.5a4.5 4.5 0 01-6.364-6.364l1.757-1.757m13.35-.622l1.757-1.757a4.5 4.5 0 00-6.364-6.364l-4.5 4.5a4.5 4.5 0 001.242 7.244" />
                    </svg>
                </div>
                <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-2">Intersect Timelines</h3>
                <p class="text-gray-600 dark:text-gray-300">
                    Define world events on a canonical timeline where multiple stories naturally converge and intersect.
                </p>
            </div>
        </div>
    </div>
</div>
