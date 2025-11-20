<script lang="ts">
    import { onMount } from "svelte";
    import Button from "./Button.svelte";

    export let isOpen = false;
    export let title: string;
    export let message: string;
    export let confirmText = "Confirm";
    export let cancelText = "Cancel";
    export let variant: "danger" | "primary" = "primary";
    export let onConfirm: () => void | Promise<void>;
    export let onCancel: (() => void) | undefined = undefined;

    let loading = false;

    async function handleConfirm() {
        loading = true;
        try {
            await onConfirm();
            isOpen = false;
        } catch (error) {
            console.error("Confirmation error:", error);
        } finally {
            loading = false;
        }
    }

    function handleCancel() {
        if (onCancel) {
            onCancel();
        }
        isOpen = false;
    }

    function handleKeydown(event: KeyboardEvent) {
        if (event.key === "Escape" && isOpen) {
            handleCancel();
        }
    }

    onMount(() => {
        document.addEventListener("keydown", handleKeydown);
        return () => {
            document.removeEventListener("keydown", handleKeydown);
        };
    });
</script>

{#if isOpen}
    <div class="relative z-50" aria-labelledby="modal-title" role="dialog" aria-modal="true">
        <!-- Background backdrop -->
        <div
            class="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity"
            on:click={handleCancel}
        ></div>

        <!-- Modal panel -->
        <div class="fixed inset-0 z-10 w-screen overflow-y-auto">
            <div class="flex min-h-full items-end justify-center p-4 text-center sm:items-center sm:p-0">
                <div
                    class="relative transform overflow-hidden rounded-lg bg-white px-4 pb-4 pt-5 text-left shadow-xl transition-all sm:my-8 sm:w-full sm:max-w-lg sm:p-6"
                >
                    <div class="sm:flex sm:items-start">
                        <div
                            class="mx-auto flex h-12 w-12 flex-shrink-0 items-center justify-center rounded-full {variant === 'danger' ? 'bg-red-100' : 'bg-indigo-100'} sm:mx-0 sm:h-10 sm:w-10"
                        >
                            {#if variant === "danger"}
                                <svg class="h-6 w-6 text-red-600" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
                                    <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z" />
                                </svg>
                            {:else}
                                <svg class="h-6 w-6 text-indigo-600" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
                                    <path stroke-linecap="round" stroke-linejoin="round" d="M9.879 7.519c1.171-1.025 3.071-1.025 4.242 0 1.172 1.025 1.172 2.687 0 3.712-.203.179-.43.326-.67.442-.745.361-1.45.999-1.45 1.827v.75M21 12a9 9 0 11-18 0 9 9 0 0118 0zm-9 5.25h.008v.008H12v-.008z" />
                                </svg>
                            {/if}
                        </div>
                        <div class="mt-3 text-center sm:ml-4 sm:mt-0 sm:text-left">
                            <h3 class="text-base font-semibold leading-6 text-gray-900" id="modal-title">
                                {title}
                            </h3>
                            <div class="mt-2">
                                <p class="text-sm text-gray-500">
                                    {message}
                                </p>
                            </div>
                        </div>
                    </div>
                    <div class="mt-5 sm:mt-4 sm:flex sm:flex-row-reverse gap-3">
                        <Button
                            variant={variant}
                            {loading}
                            disabled={loading}
                            on:click={handleConfirm}
                        >
                            {confirmText}
                        </Button>
                        <Button
                            variant="secondary"
                            disabled={loading}
                            on:click={handleCancel}
                        >
                            {cancelText}
                        </Button>
                    </div>
                </div>
            </div>
        </div>
    </div>
{/if}
