/**
 * Character TypeScript type definitions
 * Matches backend schemas from /backend/src/shinkei/schemas/character.py
 */

export type EntityImportance = "major" | "minor" | "background";

export interface Character {
	id: string;
	world_id: string;
	name: string;
	description?: string;
	aliases?: string[];
	role?: string;
	importance: EntityImportance;
	first_appearance_beat_id?: string;
	custom_metadata?: Record<string, any>;
	created_at: string;
	updated_at: string;
}

export interface CharacterCreate {
	name: string;
	description?: string;
	aliases?: string[];
	role?: string;
	importance?: EntityImportance;
	first_appearance_beat_id?: string;
	custom_metadata?: Record<string, any>;
}

export interface CharacterUpdate {
	name?: string;
	description?: string;
	aliases?: string[];
	role?: string;
	importance?: EntityImportance;
	first_appearance_beat_id?: string;
	custom_metadata?: Record<string, any>;
}

export interface CharacterResponse extends Character {}

export interface CharacterListResponse {
	characters: CharacterResponse[];
	total: number;
	page: number;
	page_size: number;
}

export interface CharacterWithMentionsResponse extends CharacterResponse {
	mention_count: number;
}

export interface CharacterSearchResponse {
	characters: CharacterWithMentionsResponse[];
	total: number;
}

// UI Helper types
export const ENTITY_IMPORTANCE_LABELS: Record<EntityImportance, string> = {
	major: "Major Character",
	minor: "Minor Character",
	background: "Background Character"
};

export const ENTITY_IMPORTANCE_COLORS: Record<EntityImportance, string> = {
	major: "bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-300",
	minor: "bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-300",
	background: "bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300"
};

export const ENTITY_IMPORTANCE_OPTIONS: { value: EntityImportance; label: string }[] = [
	{ value: "major", label: "Major Character" },
	{ value: "minor", label: "Minor Character" },
	{ value: "background", label: "Background Character" }
];

// Common character roles for suggestions
export const COMMON_CHARACTER_ROLES = [
	"Protagonist",
	"Antagonist",
	"Mentor",
	"Ally",
	"Rival",
	"Love Interest",
	"Comic Relief",
	"Sidekick",
	"Guide",
	"Guardian",
	"Trickster",
	"Herald"
];
