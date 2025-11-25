/**
 * Character Relationship TypeScript type definitions
 * Matches backend schemas from /backend/src/shinkei/schemas/character_relationship.py
 */

export type RelationshipStrength = 'strong' | 'moderate' | 'weak';

export interface CharacterRelationship {
	id: string;
	world_id: string;
	character_a_id: string;
	character_b_id: string;
	relationship_type: string;
	description?: string;
	strength: RelationshipStrength;
	is_mutual: boolean;
	first_established_beat_id?: string;
	custom_metadata?: Record<string, any>;
	created_at: string;
	updated_at: string;
}

export interface CharacterRelationshipCreate {
	character_a_id: string;
	character_b_id: string;
	relationship_type: string;
	description?: string;
	strength?: RelationshipStrength;
	is_mutual?: boolean;
	first_established_beat_id?: string;
	custom_metadata?: Record<string, any>;
}

export interface CharacterRelationshipUpdate {
	relationship_type?: string;
	description?: string;
	strength?: RelationshipStrength;
	is_mutual?: boolean;
	first_established_beat_id?: string;
	custom_metadata?: Record<string, any>;
}

export interface CharacterRelationshipResponse extends CharacterRelationship {}

export interface CharacterRelationshipListResponse {
	relationships: CharacterRelationshipResponse[];
	total: number;
	page: number;
	page_size: number;
}

// Network graph types
export interface RelationshipNetworkNode {
	character_id: string;
	character_name: string;
	importance: string;
}

export interface RelationshipNetworkEdge {
	relationship_id: string;
	from_character_id: string;
	to_character_id: string;
	relationship_type: string;
	strength: RelationshipStrength;
}

export interface RelationshipNetworkResponse {
	nodes: RelationshipNetworkNode[];
	edges: RelationshipNetworkEdge[];
	total_characters: number;
	total_relationships: number;
}

// UI Helper types
export const RELATIONSHIP_STRENGTH_OPTIONS = [
	{ value: 'strong' as RelationshipStrength, label: 'Strong' },
	{ value: 'moderate' as RelationshipStrength, label: 'Moderate' },
	{ value: 'weak' as RelationshipStrength, label: 'Weak' }
];

export const RELATIONSHIP_STRENGTH_COLORS: Record<RelationshipStrength, string> = {
	strong: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200',
	moderate: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200',
	weak: 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300'
};

export const COMMON_RELATIONSHIP_TYPES = [
	'friendship',
	'romantic',
	'family',
	'mentorship',
	'rivalry',
	'alliance',
	'enmity',
	'professional',
	'acquaintance',
	'subordinate',
	'superior',
	'sibling',
	'parent-child',
	'teacher-student',
	'enemy',
	'colleague',
	'partner'
];
