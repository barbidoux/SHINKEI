<script lang="ts">
    import type { ChatMessage } from '$lib/types';
    import ToolCallDisplay from './ToolCallDisplay.svelte';
    import { marked } from 'marked';

    export let message: ChatMessage;
    export let isStreaming = false;

    // Configure marked for safe rendering
    marked.setOptions({
        breaks: true, // Convert line breaks to <br>
        gfm: true,    // GitHub Flavored Markdown
    });

    // Render markdown content (only for assistant messages)
    function renderMarkdown(content: string): string {
        if (!content) return '';
        try {
            return marked.parse(content) as string;
        } catch {
            return content;
        }
    }

    // Format timestamp
    function formatTime(date: Date): string {
        return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    }

    // Get role display info
    function getRoleInfo(role: string): { label: string; color: string; icon: string } {
        switch (role) {
            case 'user':
                return {
                    label: 'You',
                    color: 'bg-indigo-100 dark:bg-indigo-900/40 text-indigo-700 dark:text-indigo-300',
                    icon: 'M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z'
                };
            case 'assistant':
                return {
                    label: 'Story Pilot',
                    color: 'bg-purple-100 dark:bg-purple-900/40 text-purple-700 dark:text-purple-300',
                    icon: 'M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z'
                };
            case 'system':
                return {
                    label: 'System',
                    color: 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400',
                    icon: 'M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z'
                };
            default:
                return {
                    label: role,
                    color: 'bg-gray-100 dark:bg-gray-700',
                    icon: 'M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z'
                };
        }
    }

    $: roleInfo = getRoleInfo(message.role);
    $: isUser = message.role === 'user';
</script>

<div class="px-3 py-2 {isUser ? 'bg-gray-50 dark:bg-gray-800/50' : ''} group">
    <!-- Header -->
    <div class="flex items-center gap-2 mb-1">
        <span class="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-xs font-medium {roleInfo.color}">
            <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d={roleInfo.icon} />
            </svg>
            {roleInfo.label}
        </span>
        <span class="text-[10px] text-gray-400 dark:text-gray-500">
            {formatTime(message.timestamp)}
        </span>
        {#if isStreaming}
            <span class="flex items-center gap-1 text-[10px] text-indigo-600 dark:text-indigo-400">
                <span class="flex">
                    <span class="w-1.5 h-1.5 bg-indigo-600 dark:bg-indigo-400 rounded-full animate-bounce"></span>
                    <span class="w-1.5 h-1.5 bg-indigo-600 dark:bg-indigo-400 rounded-full animate-bounce [animation-delay:0.1s] ml-0.5"></span>
                    <span class="w-1.5 h-1.5 bg-indigo-600 dark:bg-indigo-400 rounded-full animate-bounce [animation-delay:0.2s] ml-0.5"></span>
                </span>
                Typing
            </span>
        {/if}
    </div>

    <!-- Thinking (if present) -->
    {#if message.thinking}
        <div class="mb-2 p-2 bg-indigo-50 dark:bg-indigo-900/20 border border-indigo-200 dark:border-indigo-700/50 rounded text-xs">
            <div class="flex items-center gap-1 text-indigo-600 dark:text-indigo-400 mb-1 font-medium">
                <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                </svg>
                Thinking
            </div>
            <p class="text-gray-600 dark:text-gray-400 whitespace-pre-wrap">{message.thinking}</p>
        </div>
    {/if}

    <!-- Content -->
    {#if isUser}
        <div class="text-sm text-gray-800 dark:text-gray-200 whitespace-pre-wrap break-words">
            {message.content}
        </div>
    {:else}
        <div class="text-sm text-gray-800 dark:text-gray-200 prose prose-sm dark:prose-invert max-w-none prose-p:my-1 prose-ul:my-1 prose-ol:my-1 prose-li:my-0.5 prose-headings:my-2 prose-code:text-indigo-600 dark:prose-code:text-indigo-400 prose-code:bg-gray-100 dark:prose-code:bg-gray-800 prose-code:px-1 prose-code:py-0.5 prose-code:rounded prose-pre:bg-gray-100 dark:prose-pre:bg-gray-800 prose-pre:p-2">
            {@html renderMarkdown(message.content)}{#if isStreaming}<span class="animate-pulse">|</span>{/if}
        </div>
    {/if}

    <!-- Tool calls -->
    {#if message.toolCalls && message.toolCalls.length > 0}
        <div class="mt-2">
            {#each message.toolCalls as toolCall, i}
                <ToolCallDisplay
                    {toolCall}
                    result={message.toolResults?.[i]}
                />
            {/each}
        </div>
    {/if}
</div>
