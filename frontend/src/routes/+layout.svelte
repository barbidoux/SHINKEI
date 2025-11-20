<script lang="ts">
    import "../app.css";
    import { auth } from "$lib/stores/auth";
    import { onMount } from "svelte";
    import { goto } from "$app/navigation";
    import Toast from "$lib/components/Toast.svelte";
    import { applyTheme, type Theme } from "$lib/theme";

    let showUserMenu = false;

    onMount(() => {
        auth.initialize();
    });

    // Apply theme when user settings change
    $: if ($auth.user?.settings?.ui_theme) {
        applyTheme($auth.user.settings.ui_theme as Theme);
    }

    function handleLogout() {
        auth.logout();
        showUserMenu = false;
        goto("/login");
    }
</script>

<div class="min-h-screen bg-gray-100">
    <nav class="bg-white shadow-sm">
        <div class="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
            <div class="flex h-16 justify-between">
                <div class="flex">
                    <div class="flex flex-shrink-0 items-center">
                        <a href="/" class="text-xl font-bold text-indigo-600"
                            >Shinkei</a
                        >
                    </div>
                    <div class="hidden sm:ml-6 sm:flex sm:space-x-8">
                        <a
                            href="/worlds"
                            class="inline-flex items-center border-b-2 border-transparent px-1 pt-1 text-sm font-medium text-gray-500 hover:border-gray-300 hover:text-gray-700"
                            >Worlds</a
                        >
                    </div>
                </div>
                <div class="hidden sm:ml-6 sm:flex sm:items-center gap-4">
                    {#if $auth.isAuthenticated}
                        <div class="relative">
                            <button
                                type="button"
                                class="flex items-center gap-2 rounded-full bg-white text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2"
                                on:click={() => showUserMenu = !showUserMenu}
                            >
                                <span class="sr-only">Open user menu</span>
                                <div class="flex items-center gap-2">
                                    <div class="h-8 w-8 rounded-full bg-indigo-600 flex items-center justify-center">
                                        <span class="text-sm font-medium text-white">
                                            {$auth.user?.name?.charAt(0).toUpperCase() || "U"}
                                        </span>
                                    </div>
                                    <span class="text-sm font-medium text-gray-700">
                                        {$auth.user?.name}
                                    </span>
                                    <svg class="h-5 w-5 text-gray-400" viewBox="0 0 20 20" fill="currentColor">
                                        <path fill-rule="evenodd" d="M5.23 7.21a.75.75 0 011.06.02L10 11.168l3.71-3.938a.75.75 0 111.08 1.04l-4.25 4.5a.75.75 0 01-1.08 0l-4.25-4.5a.75.75 0 01.02-1.06z" clip-rule="evenodd" />
                                    </svg>
                                </div>
                            </button>

                            {#if showUserMenu}
                                <div
                                    class="absolute right-0 z-10 mt-2 w-48 origin-top-right rounded-md bg-white py-1 shadow-lg ring-1 ring-black ring-opacity-5 focus:outline-none"
                                >
                                    <a
                                        href="/settings"
                                        class="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                                        on:click={() => showUserMenu = false}
                                    >
                                        Settings
                                    </a>
                                    <button
                                        type="button"
                                        class="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                                        on:click={handleLogout}
                                    >
                                        Sign out
                                    </button>
                                </div>
                            {/if}
                        </div>
                    {:else}
                        <a
                            href="/login"
                            class="text-sm font-medium text-indigo-600 hover:text-indigo-500 mr-4"
                            >Sign in</a
                        >
                        <a
                            href="/register"
                            class="text-sm font-medium text-gray-500 hover:text-gray-700"
                            >Sign up</a
                        >
                    {/if}
                </div>
            </div>
        </div>
    </nav>

    <main class="py-10">
        <div class="mx-auto max-w-7xl sm:px-6 lg:px-8">
            <slot />
        </div>
    </main>
</div>

<!-- Global Toast Notifications -->
<Toast />
