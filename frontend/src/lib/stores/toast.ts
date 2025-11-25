import { writable } from 'svelte/store';

export type ToastType = 'success' | 'error' | 'info' | 'warning';

export interface Toast {
    id: string;
    type: ToastType;
    message: string;
    duration?: number;
}

function createToastStore() {
    const { subscribe, update } = writable<Toast[]>([]);

    return {
        subscribe,
        show: (type: ToastType, message: string, duration = 5000) => {
            const id = Math.random().toString(36).substring(7);
            const toast: Toast = { id, type, message, duration };

            update(toasts => [...toasts, toast]);

            if (duration > 0) {
                setTimeout(() => {
                    update(toasts => toasts.filter(t => t.id !== id));
                }, duration);
            }
        },
        remove: (id: string) => {
            update(toasts => toasts.filter(t => t.id !== id));
        },
        success: (message: string, duration?: number) => {
            createToastStore().show('success', message, duration);
        },
        error: (message: string, duration?: number) => {
            createToastStore().show('error', message, duration);
        },
        info: (message: string, duration?: number) => {
            createToastStore().show('info', message, duration);
        },
        warning: (message: string, duration?: number) => {
            createToastStore().show('warning', message, duration);
        }
    };
}

export const toasts = createToastStore();

// Helper function for easier toast usage
export function addToast(toast: { type: ToastType; message: string; duration?: number }) {
    toasts.show(toast.type, toast.message, toast.duration);
}
