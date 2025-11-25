/**
 * Location TypeScript type definitions
 * Matches backend schemas from /backend/src/shinkei/schemas/location.py
 */

export type LocationSignificance = 'major' | 'minor' | 'background';

export interface Location {
	id: string;
	world_id: string;
	name: string;
	description?: string;
	location_type?: string;
	parent_location_id?: string;
	significance?: string;
	first_appearance_beat_id?: string;
	coordinates?: Record<string, any>;
	custom_metadata?: Record<string, any>;
	created_at: string;
	updated_at: string;
}

export interface LocationCreate {
	name: string;
	description?: string;
	location_type?: string;
	parent_location_id?: string;
	significance?: string;
	first_appearance_beat_id?: string;
	coordinates?: Record<string, any>;
	custom_metadata?: Record<string, any>;
}

export interface LocationUpdate {
	name?: string;
	description?: string;
	location_type?: string;
	parent_location_id?: string;
	significance?: string;
	first_appearance_beat_id?: string;
	coordinates?: Record<string, any>;
	custom_metadata?: Record<string, any>;
}

export interface LocationResponse extends Location {}

export interface LocationListResponse {
	locations: LocationResponse[];
	total: number;
	page: number;
	page_size: number;
}

export interface LocationHierarchyResponse extends LocationResponse {
	parent_location?: LocationResponse;
	child_locations: LocationResponse[];
}

export interface LocationWithMentionsResponse extends LocationResponse {
	mention_count: number;
}

// UI Helper types
export const COMMON_LOCATION_TYPES = [
	"city",
	"building",
	"planet",
	"region",
	"country",
	"room",
	"vehicle",
	"landmark",
	"natural",
	"dimension",
	"continent",
	"village",
	"forest",
	"mountain",
	"ocean",
	"desert",
	"space station",
	"ship"
];

export const LOCATION_TYPE_COLORS: Record<string, string> = {
	city: "bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-300",
	building: "bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300",
	planet: "bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-300",
	region: "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300",
	country: "bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-300",
	natural: "bg-emerald-100 text-emerald-800 dark:bg-emerald-900 dark:text-emerald-300",
	dimension: "bg-indigo-100 text-indigo-800 dark:bg-indigo-900 dark:text-indigo-300"
};

// Helper function to get location breadcrumb trail
export function getLocationBreadcrumb(
	location: LocationResponse | LocationHierarchyResponse,
	allLocations: LocationResponse[]
): LocationResponse[] {
	const breadcrumb: LocationResponse[] = [location];
	let current = location;

	while (current.parent_location_id) {
		const parent = allLocations.find((loc) => loc.id === current.parent_location_id);
		if (!parent) break;
		breadcrumb.unshift(parent);
		current = parent;
	}

	return breadcrumb;
}

// Helper function to build location tree
export interface LocationTreeNode extends LocationResponse {
	children: LocationTreeNode[];
	level: number;
}

export function buildLocationTree(locations: LocationResponse[]): LocationTreeNode[] {
	const locationMap = new Map<string, LocationTreeNode>();
	const roots: LocationTreeNode[] = [];

	// Create map of all locations
	locations.forEach((loc) => {
		locationMap.set(loc.id, { ...loc, children: [], level: 0 });
	});

	// Build tree structure
	locations.forEach((loc) => {
		const node = locationMap.get(loc.id)!;
		if (loc.parent_location_id) {
			const parent = locationMap.get(loc.parent_location_id);
			if (parent) {
				parent.children.push(node);
				node.level = parent.level + 1;
			} else {
				// Parent not found, treat as root
				roots.push(node);
			}
		} else {
			roots.push(node);
		}
	});

	return roots;
}
