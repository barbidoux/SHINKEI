<script lang="ts">
	import type { EntityImportance } from '$lib/types/character';
	import { ENTITY_IMPORTANCE_LABELS, ENTITY_IMPORTANCE_COLORS } from '$lib/types/character';

	export let importance: EntityImportance;
	export let size: 'sm' | 'md' | 'lg' = 'md';

	const sizeClasses = {
		sm: 'text-xs px-2 py-0.5',
		md: 'text-sm px-2.5 py-0.5',
		lg: 'text-base px-3 py-1'
	};
</script>

<span
	class="inline-flex items-center rounded-full font-medium {ENTITY_IMPORTANCE_COLORS[
		importance
	]} {sizeClasses[size]}"
>
	{ENTITY_IMPORTANCE_LABELS[importance]}
</span>
