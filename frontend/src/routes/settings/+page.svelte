<script lang="ts">
    import { onMount } from "svelte";
    import { api } from "$lib/api";
    import { auth } from "$lib/stores/auth";
    import type { User, UserSettings, UserUpdate } from "$lib/types";

    let user: User | null = null;
    let loading = true;
    let saving = false;
    let error = "";
    let successMessage = "";

    // Form fields
    let name = "";
    let language = "en";
    let ui_theme: "light" | "dark" | "system" = "system";
    let llm_provider: "openai" | "anthropic" | "ollama" = "openai";
    let llm_model = "";
    let llm_base_url = "";

    onMount(async () => {
        try {
            user = await api.get<User>("/users/me");

            // Populate form fields
            name = user.name;
            language = user.settings.language || "en";
            ui_theme = user.settings.ui_theme || "system";
            llm_provider = user.settings.llm_provider || "openai";
            llm_model = user.settings.llm_model || "";
            llm_base_url = user.settings.llm_base_url || "";
        } catch (e: any) {
            error = e.message || "Failed to load user settings";
        } finally {
            loading = false;
        }
    });

    async function handleSave() {
        saving = true;
        error = "";
        successMessage = "";

        try {
            const updateData: UserUpdate = {
                name,
                settings: {
                    language,
                    ui_theme,
                    llm_provider,
                    llm_model,
                    llm_base_url: llm_base_url || undefined,
                    default_model: llm_model, // Keep for backwards compatibility
                },
            };

            const updated = await api.put<User>("/users/me", updateData);

            // Update auth store with new user data
            if ($auth.user) {
                auth.setUser(updated);
            }

            successMessage = "Settings saved successfully!";

            // Clear success message after 3 seconds
            setTimeout(() => {
                successMessage = "";
            }, 3000);
        } catch (e: any) {
            error = e.message || "Failed to save settings";
        } finally {
            saving = false;
        }
    }

    // Get placeholder text for model input based on provider
    function getModelPlaceholder(provider: string): string {
        switch (provider) {
            case "openai":
                return "e.g., gpt-4o, gpt-4-turbo";
            case "anthropic":
                return "e.g., claude-3-5-sonnet-20240620";
            case "ollama":
                return "e.g., llama3, mistral, codellama";
            default:
                return "Model name";
        }
    }

    // Get placeholder for base URL based on provider
    function getBaseUrlPlaceholder(provider: string): string {
        switch (provider) {
            case "ollama":
                return "e.g., http://192.168.1.100:11434 (for Windows Ollama server)";
            default:
                return "Custom API endpoint (optional)";
        }
    }
</script>

<div class="mx-auto max-w-4xl px-4 py-8 sm:px-6 lg:px-8">
    <div class="mb-8">
        <h1 class="text-3xl font-bold text-gray-900 dark:text-gray-100">Settings</h1>
        <p class="mt-2 text-sm text-gray-600 dark:text-gray-400">
            Manage your account and LLM provider configuration
        </p>
    </div>

    {#if loading}
        <div class="text-center py-12">
            <div class="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
            <p class="mt-2 text-sm text-gray-600 dark:text-gray-400">Loading settings...</p>
        </div>
    {:else if error && !user}
        <div class="rounded-md bg-red-50 dark:bg-red-900/30 p-4">
            <p class="text-sm text-red-800 dark:text-red-300">{error}</p>
        </div>
    {:else}
        <form on:submit|preventDefault={handleSave} class="space-y-8">
            <!-- Profile Section -->
            <div class="bg-white dark:bg-gray-800 shadow-sm ring-1 ring-gray-900/5 dark:ring-gray-700 rounded-lg p-6">
                <h2 class="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
                    Profile
                </h2>

                <div class="space-y-4">
                    <div>
                        <label
                            for="email"
                            class="block text-sm font-medium text-gray-700 dark:text-gray-300"
                        >
                            Email
                        </label>
                        <input
                            type="email"
                            id="email"
                            value={user?.email}
                            disabled
                            class="mt-1 block w-full rounded-md border-gray-300 dark:border-gray-600 bg-gray-50 dark:bg-gray-700 text-gray-500 dark:text-gray-400 shadow-sm sm:text-sm"
                        />
                        <p class="mt-1 text-xs text-gray-500 dark:text-gray-400">
                            Email cannot be changed
                        </p>
                    </div>

                    <div>
                        <label
                            for="name"
                            class="block text-sm font-medium text-gray-700 dark:text-gray-300"
                        >
                            Display Name
                        </label>
                        <input
                            type="text"
                            id="name"
                            bind:value={name}
                            required
                            class="mt-1 block w-full rounded-md border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 shadow-sm focus:border-indigo-500 dark:focus:border-indigo-400 focus:ring-indigo-500 dark:focus:ring-indigo-400 sm:text-sm"
                        />
                    </div>
                </div>
            </div>

            <!-- LLM Configuration Section -->
            <div class="bg-white dark:bg-gray-800 shadow-sm ring-1 ring-gray-900/5 dark:ring-gray-700 rounded-lg p-6">
                <h2 class="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
                    LLM Provider Configuration
                </h2>

                <div class="space-y-4">
                    <div>
                        <label
                            for="llm_provider"
                            class="block text-sm font-medium text-gray-700 dark:text-gray-300"
                        >
                            Default Provider
                        </label>
                        <select
                            id="llm_provider"
                            bind:value={llm_provider}
                            class="mt-1 block w-full rounded-md border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 shadow-sm focus:border-indigo-500 dark:focus:border-indigo-400 focus:ring-indigo-500 dark:focus:ring-indigo-400 sm:text-sm"
                        >
                            <option value="openai">OpenAI</option>
                            <option value="anthropic">Anthropic (Claude)</option>
                            <option value="ollama">Ollama (Local/Remote)</option>
                        </select>
                        <p class="mt-1 text-xs text-gray-500 dark:text-gray-400">
                            Choose your preferred LLM provider for narrative generation
                        </p>
                    </div>

                    <div>
                        <label
                            for="llm_model"
                            class="block text-sm font-medium text-gray-700 dark:text-gray-300"
                        >
                            Default Model
                        </label>
                        <input
                            type="text"
                            id="llm_model"
                            bind:value={llm_model}
                            placeholder={getModelPlaceholder(llm_provider)}
                            class="mt-1 block w-full rounded-md border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 shadow-sm focus:border-indigo-500 dark:focus:border-indigo-400 focus:ring-indigo-500 dark:focus:ring-indigo-400 sm:text-sm"
                        />
                        <p class="mt-1 text-xs text-gray-500 dark:text-gray-400">
                            Specify the model to use by default (can be overridden per generation)
                        </p>
                    </div>

                    {#if llm_provider === "ollama"}
                        <div class="rounded-md bg-blue-50 dark:bg-blue-900/30 p-4">
                            <div class="flex">
                                <div class="flex-shrink-0">
                                    <svg class="h-5 w-5 text-blue-400 dark:text-blue-300" viewBox="0 0 20 20" fill="currentColor">
                                        <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd" />
                                    </svg>
                                </div>
                                <div class="ml-3 flex-1">
                                    <p class="text-sm text-blue-700 dark:text-blue-300">
                                        <strong>Ollama Configuration:</strong> You can use Ollama running on your Windows machine or any remote server.
                                        Enter the full URL including port (e.g., http://192.168.1.100:11434 for a Windows PC on your network).
                                    </p>
                                </div>
                            </div>
                        </div>
                    {/if}

                    <div>
                        <label
                            for="llm_base_url"
                            class="block text-sm font-medium text-gray-700 dark:text-gray-300"
                        >
                            Base URL / Custom Endpoint
                            {#if llm_provider === "ollama"}
                                <span class="text-red-500 dark:text-red-400">*</span>
                            {:else}
                                <span class="text-gray-500 dark:text-gray-400">(optional)</span>
                            {/if}
                        </label>
                        <input
                            type="url"
                            id="llm_base_url"
                            bind:value={llm_base_url}
                            placeholder={getBaseUrlPlaceholder(llm_provider)}
                            required={llm_provider === "ollama"}
                            class="mt-1 block w-full rounded-md border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 shadow-sm focus:border-indigo-500 dark:focus:border-indigo-400 focus:ring-indigo-500 dark:focus:ring-indigo-400 sm:text-sm"
                        />
                        <p class="mt-1 text-xs text-gray-500 dark:text-gray-400">
                            {#if llm_provider === "ollama"}
                                Required for Ollama. Enter the URL of your Ollama server.
                            {:else}
                                Optional custom API endpoint for this provider
                            {/if}
                        </p>
                    </div>
                </div>
            </div>

            <!-- Preferences Section -->
            <div class="bg-white dark:bg-gray-800 shadow-sm ring-1 ring-gray-900/5 dark:ring-gray-700 rounded-lg p-6">
                <h2 class="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
                    Preferences
                </h2>

                <div class="space-y-4">
                    <div>
                        <label
                            for="ui_theme"
                            class="block text-sm font-medium text-gray-700 dark:text-gray-300"
                        >
                            Theme
                        </label>
                        <select
                            id="ui_theme"
                            bind:value={ui_theme}
                            class="mt-1 block w-full rounded-md border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 shadow-sm focus:border-indigo-500 dark:focus:border-indigo-400 focus:ring-indigo-500 dark:focus:ring-indigo-400 sm:text-sm"
                        >
                            <option value="system">System Default</option>
                            <option value="light">Light</option>
                            <option value="dark">Dark</option>
                        </select>
                    </div>

                    <div>
                        <label
                            for="language"
                            class="block text-sm font-medium text-gray-700 dark:text-gray-300"
                        >
                            Language
                        </label>
                        <select
                            id="language"
                            bind:value={language}
                            class="mt-1 block w-full rounded-md border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 shadow-sm focus:border-indigo-500 dark:focus:border-indigo-400 focus:ring-indigo-500 dark:focus:ring-indigo-400 sm:text-sm"
                        >
                            <option value="en">English</option>
                            <option value="fr">Français</option>
                            <option value="es">Español</option>
                            <option value="de">Deutsch</option>
                            <option value="ja">日本語</option>
                        </select>
                    </div>
                </div>
            </div>

            <!-- Success/Error Messages -->
            {#if successMessage}
                <div class="rounded-md bg-green-50 dark:bg-green-900/30 p-4">
                    <div class="flex">
                        <div class="flex-shrink-0">
                            <svg class="h-5 w-5 text-green-400 dark:text-green-300" viewBox="0 0 20 20" fill="currentColor">
                                <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.857-9.809a.75.75 0 00-1.214-.882l-3.483 4.79-1.88-1.88a.75.75 0 10-1.06 1.061l2.5 2.5a.75.75 0 001.137-.089l4-5.5z" clip-rule="evenodd" />
                            </svg>
                        </div>
                        <div class="ml-3">
                            <p class="text-sm font-medium text-green-800 dark:text-green-300">{successMessage}</p>
                        </div>
                    </div>
                </div>
            {/if}

            {#if error && user}
                <div class="rounded-md bg-red-50 dark:bg-red-900/30 p-4">
                    <p class="text-sm text-red-800 dark:text-red-300">{error}</p>
                </div>
            {/if}

            <!-- Save Button -->
            <div class="flex justify-end gap-3">
                <a
                    href="/worlds"
                    class="rounded-md bg-white dark:bg-gray-700 px-3 py-2 text-sm font-semibold text-gray-900 dark:text-gray-100 shadow-sm ring-1 ring-inset ring-gray-300 dark:ring-gray-600 hover:bg-gray-50 dark:hover:bg-gray-600"
                >
                    Cancel
                </a>
                <button
                    type="submit"
                    disabled={saving}
                    class="rounded-md bg-indigo-600 dark:bg-indigo-500 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500 dark:hover:bg-indigo-400 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600 dark:focus-visible:outline-indigo-400 disabled:opacity-50"
                >
                    {#if saving}
                        Saving...
                    {:else}
                        Save Settings
                    {/if}
                </button>
            </div>
        </form>
    {/if}
</div>
