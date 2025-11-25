<script lang="ts">
    import "../app.css";
    import { auth } from "$lib/stores/auth";
    import { chatStore } from "$lib/stores/chat";
    import { onMount } from "svelte";
    import { goto } from "$app/navigation";
    import Toast from "$lib/components/Toast.svelte";
    import { AIChatPanel } from "$lib/components/agent";
    import { applyTheme, type Theme } from "$lib/theme";

    let showUserMenu = false;

    onMount(() => {
        auth.initialize();

        // Apply saved theme immediately on mount
        const savedTheme = localStorage.getItem('theme') as Theme | null;
        if (savedTheme) {
            applyTheme(savedTheme);
        }
    });

    // Apply theme when user settings change
    $: if ($auth.user?.settings?.ui_theme) {
        const theme = $auth.user.settings.ui_theme as Theme;
        applyTheme(theme);
        // Save to localStorage for immediate application on next load
        localStorage.setItem('theme', theme);
    }

    function handleLogout() {
        auth.logout();
        showUserMenu = false;
        goto("/login");
    }

    function toggleChat() {
        chatStore.toggle();
    }
</script>

<div class="h-screen flex flex-col bg-gray-100 dark:bg-gray-900 transition-colors overflow-hidden">
    <!-- Top Navigation -->
    <nav class="flex-shrink-0 bg-white dark:bg-gray-800 shadow-sm transition-colors z-20">
        <div class="px-4 sm:px-6 lg:px-8">
            <div class="flex h-14 justify-between">
                <div class="flex items-center">
                    <!-- Story Pilot Chat toggle button (only when authenticated) -->
                    {#if $auth.isAuthenticated}
                        <button
                            on:click={toggleChat}
                            class="mr-4 flex items-center gap-2 px-3 py-1.5 rounded-lg transition-all duration-200 {$chatStore.isOpen
                                ? 'bg-gradient-to-r from-indigo-500 to-purple-600 text-white shadow-md'
                                : 'bg-gradient-to-r from-indigo-100 to-purple-100 dark:from-indigo-900/40 dark:to-purple-900/40 text-indigo-700 dark:text-indigo-300 hover:from-indigo-200 hover:to-purple-200 dark:hover:from-indigo-900/60 dark:hover:to-purple-900/60'}"
                            title="{$chatStore.isOpen ? 'Hide' : 'Show'} Story Pilot AI Assistant"
                        >
                            <svg
                                class="w-5 h-5 {$chatStore.isOpen ? 'text-white' : 'text-indigo-600 dark:text-indigo-400'}"
                                fill="none"
                                stroke="currentColor"
                                viewBox="0 0 24 24"
                            >
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                            </svg>
                            <span class="text-sm font-medium hidden sm:inline">Story Pilot</span>
                            {#if $chatStore.isOpen}
                                <svg class="w-4 h-4 hidden sm:block" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 19l-7-7 7-7m8 14l-7-7 7-7" />
                                </svg>
                            {/if}
                        </button>
                    {/if}

                    <div class="flex flex-shrink-0 items-center">
                        <a href="/" class="text-xl font-bold text-indigo-600 dark:text-indigo-400">Shinkei</a>
                    </div>
                    <div class="hidden sm:ml-6 sm:flex sm:space-x-8">
                        <a
                            href="/worlds"
                            class="inline-flex items-center border-b-2 border-transparent px-1 pt-1 text-sm font-medium text-gray-500 dark:text-gray-300 hover:border-gray-300 dark:hover:border-gray-600 hover:text-gray-700 dark:hover:text-gray-100"
                        >Worlds</a>
                    </div>
                </div>
                <div class="hidden sm:ml-6 sm:flex sm:items-center gap-4">
                    {#if $auth.isAuthenticated}
                        <div class="relative">
                            <button
                                type="button"
                                class="flex items-center gap-2 rounded-full bg-white dark:bg-gray-700 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 dark:ring-offset-gray-800"
                                on:click={() => showUserMenu = !showUserMenu}
                            >
                                <span class="sr-only">Open user menu</span>
                                <div class="flex items-center gap-2">
                                    <div class="h-8 w-8 rounded-full bg-indigo-600 dark:bg-indigo-500 flex items-center justify-center">
                                        <span class="text-sm font-medium text-white">
                                            {$auth.user?.name?.charAt(0).toUpperCase() || "U"}
                                        </span>
                                    </div>
                                    <span class="text-sm font-medium text-gray-700 dark:text-gray-200">
                                        {$auth.user?.name}
                                    </span>
                                    <svg class="h-5 w-5 text-gray-400 dark:text-gray-500" viewBox="0 0 20 20" fill="currentColor">
                                        <path fill-rule="evenodd" d="M5.23 7.21a.75.75 0 011.06.02L10 11.168l3.71-3.938a.75.75 0 111.08 1.04l-4.25 4.5a.75.75 0 01-1.08 0l-4.25-4.5a.75.75 0 01.02-1.06z" clip-rule="evenodd" />
                                    </svg>
                                </div>
                            </button>

                            {#if showUserMenu}
                                <div
                                    class="absolute right-0 z-10 mt-2 w-48 origin-top-right rounded-md bg-white dark:bg-gray-700 py-1 shadow-lg ring-1 ring-black ring-opacity-5 dark:ring-gray-600 focus:outline-none"
                                >
                                    <a
                                        href="/settings"
                                        class="block px-4 py-2 text-sm text-gray-700 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-600"
                                        on:click={() => showUserMenu = false}
                                    >
                                        Settings
                                    </a>
                                    <button
                                        type="button"
                                        class="block w-full text-left px-4 py-2 text-sm text-gray-700 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-600"
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
                            class="text-sm font-medium text-indigo-600 dark:text-indigo-400 hover:text-indigo-500 dark:hover:text-indigo-300 mr-4"
                        >Sign in</a>
                        <a
                            href="/register"
                            class="text-sm font-medium text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200"
                        >Sign up</a>
                    {/if}
                </div>
            </div>
        </div>
    </nav>

    <!-- Main content area with optional sidebar -->
    <div class="flex-1 flex overflow-hidden">
        <!-- AI Chat Panel Sidebar -->
        {#if $auth.isAuthenticated && $chatStore.isOpen}
            <aside class="w-80 flex-shrink-0 border-r border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 shadow-lg z-10">
                <AIChatPanel />
            </aside>
        {/if}

        <!-- Main content -->
        <main class="flex-1 overflow-y-auto">
            <div class="py-8">
                <div class="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
                    <slot />
                </div>
            </div>
        </main>
    </div>
</div>

<!-- Global Toast Notifications -->
<Toast />
