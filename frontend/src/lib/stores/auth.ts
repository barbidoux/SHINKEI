import { writable } from 'svelte/store';
import { browser } from '$app/environment';
import type { User } from '$lib/types';

interface AuthState {
    user: User | null;
    token: string | null;
    isAuthenticated: boolean;
}

const initialState: AuthState = {
    user: null,
    token: null,
    isAuthenticated: false
};

function createAuthStore() {
    const { subscribe, set, update } = writable<AuthState>(initialState);

    return {
        subscribe,
        login: (user: User, token: string) => {
            const state = { user, token, isAuthenticated: true };
            set(state);
            if (browser) {
                localStorage.setItem('auth', JSON.stringify(state));
            }
        },
        logout: () => {
            set(initialState);
            if (browser) {
                localStorage.removeItem('auth');
            }
        },
        setUser: (user: User) => {
            update(state => {
                const newState = { ...state, user };
                if (browser) {
                    localStorage.setItem('auth', JSON.stringify(newState));
                }
                return newState;
            });
        },
        initialize: () => {
            if (browser) {
                const stored = localStorage.getItem('auth');
                if (stored) {
                    try {
                        set(JSON.parse(stored));
                    } catch (e) {
                        console.error('Failed to parse auth state', e);
                        localStorage.removeItem('auth');
                    }
                }
            }
        }
    };
}

export const auth = createAuthStore();
