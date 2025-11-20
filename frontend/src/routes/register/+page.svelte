<script lang="ts">
    import { api } from "$lib/api";
    import { goto } from "$app/navigation";
    import { auth } from "$lib/stores/auth";

    let email = "";
    let name = "";
    let password = ""; // Keep password variable as it's declared in the original code
    let error = "";
    let loading = false;

    async function handleRegister() {
        loading = true;
        error = "";
        try {
            // For dev mode, we use the same login endpoint which auto-registers
            const response = await api.post<{ access_token: string }>(
                "/auth/login",
                { email, password },
            );

            // Fetch user details to populate store
            const user = await api.get<any>("/users/me", {
                headers: { Authorization: `Bearer ${response.access_token}` },
            });

            auth.login(user, response.access_token);
            goto("/worlds");
        } catch (e: any) {
            error = e.message;
        } finally {
            loading = false;
        }
    }
</script>

<div
    class="flex min-h-screen items-center justify-center bg-gray-50 px-4 py-12 sm:px-6 lg:px-8"
>
    <div class="w-full max-w-md space-y-8">
        <div>
            <h2
                class="mt-6 text-center text-3xl font-bold tracking-tight text-gray-900"
            >
                Create your account
            </h2>
        </div>
        <form class="mt-8 space-y-6" on:submit|preventDefault={handleRegister}>
            <div class="-space-y-px rounded-md shadow-sm">
                <div>
                    <label for="name" class="sr-only">Name</label>
                    <input
                        id="name"
                        name="name"
                        type="text"
                        required
                        class="relative block w-full rounded-t-md border-0 py-1.5 text-gray-900 ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:z-10 focus:ring-2 focus:ring-indigo-600 sm:text-sm sm:leading-6"
                        placeholder="Full Name"
                        bind:value={name}
                    />
                </div>
                <div>
                    <label for="email-address" class="sr-only"
                        >Email address</label
                    >
                    <input
                        id="email-address"
                        name="email"
                        type="email"
                        autocomplete="email"
                        required
                        class="relative block w-full border-0 py-1.5 text-gray-900 ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:z-10 focus:ring-2 focus:ring-indigo-600 sm:text-sm sm:leading-6"
                        placeholder="Email address"
                        bind:value={email}
                    />
                </div>
                <div>
                    <label for="password" class="sr-only">Password</label>
                    <input
                        id="password"
                        name="password"
                        type="password"
                        autocomplete="new-password"
                        required
                        class="relative block w-full rounded-b-md border-0 py-1.5 text-gray-900 ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:z-10 focus:ring-2 focus:ring-indigo-600 sm:text-sm sm:leading-6"
                        placeholder="Password"
                        bind:value={password}
                    />
                </div>
            </div>

            {#if error}
                <div class="text-red-500 text-sm text-center">{error}</div>
            {/if}

            <div>
                <button
                    type="submit"
                    disabled={loading}
                    class="group relative flex w-full justify-center rounded-md bg-indigo-600 px-3 py-2 text-sm font-semibold text-white hover:bg-indigo-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600 disabled:opacity-50"
                >
                    {#if loading}
                        Creating account...
                    {:else}
                        Sign up
                    {/if}
                </button>
            </div>
        </form>
    </div>
</div>
