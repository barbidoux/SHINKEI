/**
 * Story Beat-related TypeScript types matching backend schemas
 */

export type BeatType = "scene" | "log" | "memory" | "dialogue" | "description";
export type GeneratedBy = "ai" | "user" | "collaborative";

export interface StoryBeat {
    id: string;
    story_id: string;
    content: string;
    type: BeatType;
    order_index: number;
    summary?: string;
    local_time_label?: string;
    world_event_id?: string;
    generated_by: GeneratedBy;
    generation_reasoning?: string;
    created_at: string;
    updated_at: string;
}

export interface BeatCreate {
    story_id: string;
    content: string;
    type: BeatType;
    order_index: number;
    summary?: string;
    local_time_label?: string;
    world_event_id?: string;
    generated_by?: GeneratedBy;
}

export interface BeatUpdate {
    content?: string;
    type?: BeatType;
    order_index?: number;
    summary?: string;
    local_time_label?: string;
    world_event_id?: string;
    generation_reasoning?: string;
}

export interface BeatReasoningUpdate {
    generation_reasoning?: string;
}

export interface BeatResponse extends StoryBeat {}

export interface BeatListResponse {
    beats: BeatResponse[];
    total: number;
}

// ===== GENERATION TYPES =====

// Length preset options
export type LengthPreset = "short" | "medium" | "long";

// Narrative style options
export type PacingOption = "slow" | "medium" | "fast";
export type TensionOption = "low" | "medium" | "high";
export type DialogueDensityOption = "minimal" | "moderate" | "heavy";
export type DescriptionRichnessOption = "sparse" | "balanced" | "detailed";

// Collaborative-specific options
export type VariationFocusOption = "style" | "plot" | "tone" | "all";

// Generation request/response types
export interface GenerateBeatRequest {
    // Provider settings
    provider?: string; // "openai" | "anthropic" | "ollama"
    model?: string;
    user_instructions?: string;
    target_event_id?: string;
    ollama_host?: string; // For custom Ollama server (Windows)

    // === BASIC TAB: Length Control ===
    target_length_preset?: LengthPreset;
    target_length_words?: number;

    // === ADVANCED TAB: LLM Parameters ===
    temperature?: number;
    max_tokens?: number;
    top_p?: number;
    frequency_penalty?: number;
    presence_penalty?: number;
    top_k?: number;

    // === EXPERT TAB: Narrative Style Controls ===
    pacing?: PacingOption;
    tension_level?: TensionOption;
    dialogue_density?: DialogueDensityOption;
    description_richness?: DescriptionRichnessOption;

    // Beat insertion parameters
    insertion_mode?: string;
    insert_after_beat_id?: string | null;
    insert_at_position?: number;

    // Metadata control parameters
    beat_type_mode?: string;
    beat_type_manual?: string;
    summary_mode?: string;
    summary_manual?: string;
    local_time_label_mode?: string;
    local_time_label_manual?: string;
    world_event_id_mode?: string;
    world_event_id_manual?: string;
}

// Collaborative proposal request
export interface ProposalRequest extends GenerateBeatRequest {
    user_guidance?: string;
    num_proposals?: number;

    // Collaborative-specific parameters
    proposal_diversity?: number;
    variation_focus?: VariationFocusOption;
}

// Proposal response
export interface BeatProposal {
    id: string;
    content: string;
    summary: string;
    local_time_label: string;
    beat_type: string;
    reasoning?: string;
}

export interface ProposalResponse {
    proposals: BeatProposal[];
}

// ===== PARAMETER DESCRIPTIONS FOR UI TOOLTIPS =====

export const PARAM_DESCRIPTIONS = {
    // Length
    target_length_preset: "Quick length selection: short (~500 words), medium (~1000), long (~2000)",
    target_length_words: "Precise word count target (100-10,000)",

    // LLM Params
    temperature: "Controls creativity: 0 = focused/deterministic, 2 = creative/random",
    max_tokens: "Maximum output length in tokens (~4 chars per token)",
    top_p: "Nucleus sampling: considers tokens in the top P% probability mass",
    frequency_penalty: "Reduces repetition of frequently used words (-2 to 2)",
    presence_penalty: "Encourages the model to explore new topics (-2 to 2)",
    top_k: "Top-K sampling: only considers the K most likely next tokens",

    // Narrative Style
    pacing: "Story tempo: slow = detailed scenes, fast = action-focused",
    tension_level: "Emotional intensity: low = calm, high = gripping",
    dialogue_density: "Amount of character dialogue vs narration",
    description_richness: "Level of sensory and environmental detail",

    // Collaborative
    proposal_diversity: "How different the 3 proposals are from each other",
    variation_focus: "Which aspect varies most between proposals"
} as const;

// ===== LENGTH PRESET LABELS =====

export const LENGTH_PRESETS = [
    { value: "short" as const, label: "Short", description: "~500 words" },
    { value: "medium" as const, label: "Medium", description: "~1000 words" },
    { value: "long" as const, label: "Long", description: "~2000 words" }
];

// ===== NARRATIVE STYLE OPTIONS =====

export const PACING_OPTIONS = [
    { value: "slow" as const, label: "Slow", emoji: "🐢", description: "Detailed scenes" },
    { value: "medium" as const, label: "Medium", emoji: "⚖️", description: "Balanced" },
    { value: "fast" as const, label: "Fast", emoji: "🚀", description: "Action-focused" }
];

export const TENSION_OPTIONS = [
    { value: "low" as const, label: "Low", emoji: "😌", description: "Calm" },
    { value: "medium" as const, label: "Medium", emoji: "😐", description: "Engaging" },
    { value: "high" as const, label: "High", emoji: "😰", description: "Intense" }
];

export const DIALOGUE_OPTIONS = [
    { value: "minimal" as const, label: "Minimal", emoji: "📖" },
    { value: "moderate" as const, label: "Moderate", emoji: "💬" },
    { value: "heavy" as const, label: "Heavy", emoji: "🗣️" }
];

export const DESCRIPTION_OPTIONS = [
    { value: "sparse" as const, label: "Sparse", emoji: "✏️" },
    { value: "balanced" as const, label: "Balanced", emoji: "📝" },
    { value: "detailed" as const, label: "Detailed", emoji: "🎨" }
];

// ===== COLLABORATIVE OPTIONS =====

export const VARIATION_FOCUS_OPTIONS = [
    { value: "style" as const, label: "Writing Style", emoji: "✍️" },
    { value: "plot" as const, label: "Plot Direction", emoji: "📈" },
    { value: "tone" as const, label: "Emotional Tone", emoji: "🎭" },
    { value: "all" as const, label: "All Aspects", emoji: "🔀" }
];

export interface SummarizeBeatRequest {
    provider?: string;
}

export interface SummarizeBeatResponse {
    beat_id: string;
    summary: string;
}

// Helper labels for UI display
export const BEAT_TYPE_LABELS: Record<BeatType, string> = {
    scene: "Scene",
    log: "Log Entry",
    memory: "Memory",
    dialogue: "Dialogue",
    description: "Description",
};

export const GENERATED_BY_LABELS: Record<GeneratedBy, string> = {
    ai: "AI Generated",
    user: "User Written",
    collaborative: "Collaborative",
};

// Beat Modification types
export interface BeatModificationRequest {
    modification_instructions: string;
    provider: "openai" | "anthropic" | "ollama";
    model?: string;
    ollama_host?: string;
    temperature?: number;
    max_tokens?: number;
    scope?: string[]; // ["content", "summary", "time_label", "world_event"]
}

export interface BeatModificationResponse {
    id: string;
    beat_id: string;

    // Original and modified versions
    original_content: string;
    modified_content: string;
    original_summary?: string;
    modified_summary?: string;
    original_time_label?: string;
    modified_time_label?: string;
    original_world_event_id?: string;
    modified_world_event_id?: string;

    // Metadata
    modification_instructions: string;
    reasoning?: string;
    unified_diff?: string;
    applied: boolean;
    created_at: string;
}

export interface BeatModificationApply {
    modification_id: string;
    apply_content?: boolean;
    apply_summary?: boolean;
    apply_time_label?: boolean;
    apply_world_event?: boolean;
}

export interface BeatModificationHistoryResponse {
    modifications: BeatModificationResponse[];
    total: number;
    beat_id: string;
}

// Beat Reordering
export interface BeatReorderRequest {
    beat_ids: string[];
}
