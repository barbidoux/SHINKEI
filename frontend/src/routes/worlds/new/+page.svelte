<script lang="ts">
    import { api } from "$lib/api";
    import { goto } from "$app/navigation";

    let name = "";
    let description = "";
    let loading = false;
    let error = "";

    async function handleSubmit() {
        loading = true;
        error = "";
        try {
            const world = await api.post<{ id: string }>("/worlds", {
                name,
                description,
            });
            goto(`/worlds/${world.id}`);
        } catch (e: any) {
            error = e.message;
        } finally {
            loading = false;
        }
    }
</script>

<div class="max-w-2xl mx-auto">
    <div class="md:flex md:items-center md:justify-between mb-8">
        <div class="min-w-0 flex-1">
            <h2
                class="text-2xl font-bold leading-7 text-gray-900 sm:truncate sm:text-3xl sm:tracking-tight"
            >
                Create New World
            </h2>
        </div>
    </div>

    <form
        on:submit|preventDefault={handleSubmit}
        class="space-y-6 bg-white shadow sm:rounded-lg p-6"
    >
        <div>
            <label
                for="name"
                class="block text-sm font-medium leading-6 text-gray-900"
                >World Name</label
            >
            <div class="mt-2">
                <input
                    type="text"
                    name="name"
                    id="name"
                    required
                    class="block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6"
                    bind:value={name}
                />
            </div>
        </div>

        <div>
            <label
                for="description"
                class="block text-sm font-medium leading-6 text-gray-900"
                >Description</label
            >
            <div class="mt-2">
                <textarea
                    id="description"
                    name="description"
                    rows="4"
                    class="block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6"
                    bind:value={description}
                ></textarea>
            </div>
            <p class="mt-3 text-sm leading-6 text-gray-600">
                Brief description of your world.
            </p>
        </div>

        {#if error}
            <div class="text-red-500 text-sm">{error}</div>
        {/if}

        <div class="flex justify-end gap-x-4">
            <a
                href="/worlds"
                class="rounded-md bg-white px-3 py-2 text-sm font-semibold text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 hover:bg-gray-50"
                >Cancel</a
            >
            <button
                type="submit"
                disabled={loading}
                class="rounded-md bg-indigo-600 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600 disabled:opacity-50"
            >
                {#if loading}Creating...{:else}Create World{/if}
            </button>
        </div>
    </form>
</div>
