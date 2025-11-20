/**
 * Theme management utility for Shinkei
 * Handles dark/light/system theme preferences
 */

import { browser } from '$app/environment';

export type Theme = 'light' | 'dark' | 'system';

/**
 * Apply the theme to the document root
 * @param theme - The theme preference to apply
 */
export function applyTheme(theme: Theme): void {
    if (!browser) return;

    const root = document.documentElement;
    let effectiveTheme: 'light' | 'dark' = 'light';

    if (theme === 'system') {
        // Use system preference
        const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
        effectiveTheme = prefersDark ? 'dark' : 'light';
    } else {
        effectiveTheme = theme;
    }

    // Apply or remove dark class
    if (effectiveTheme === 'dark') {
        root.classList.add('dark');
    } else {
        root.classList.remove('dark');
    }
}

/**
 * Listen to system theme changes when in system mode
 * @param callback - Function to call when system theme changes
 * @returns Cleanup function to remove the listener
 */
export function watchSystemTheme(callback: (isDark: boolean) => void): () => void {
    if (!browser) return () => {};

    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');

    const handler = (e: MediaQueryListEvent | MediaQueryList) => {
        callback(e.matches);
    };

    // Initial call
    handler(mediaQuery);

    // Listen for changes
    mediaQuery.addEventListener('change', handler);

    // Return cleanup function
    return () => {
        mediaQuery.removeEventListener('change', handler);
    };
}
