export interface StatDefinition {
    name: string;
    description: string;
    default_value: number;
    min_value: number;
    max_value: number;
}

export interface FeatureConfig {
    status_effects?: boolean;
    time_tracking?: boolean;
    factions?: boolean;
    currency?: boolean;
}

export interface TimeConfig {
    starting_hour: number;
    starting_day: number;
}

export interface CurrencyConfig {
    name: string;
    starting_amount: number;
}

export interface Adventure {
    id: string;
    title: string;
    description: string;
    prompt?: string;
    stats: StatDefinition[];
    starting_hp: number;
    word_lists?: any[];
    initial_location: string;
    initial_story: string;
    features?: FeatureConfig;
    time_config?: TimeConfig;
    currency_config?: CurrencyConfig;
    factions?: FactionDefinition[];
    created_at?: string;
}

export interface FactionDefinition {
    id: string;
    name: string;
    description: string;
    initial_reputation: number;
}

export interface InventoryItem {
    id: string;
    name: string;
    description: string;
    quantity: number;
    properties: Record<string, any>;
}

export interface QuestStatus {
    id: string;
    title: string;
    description: string;
    status: string;
    objectives: string[];
    completed_objectives: string[];
    rewards: Record<string, any>;
}

export interface PlayerState {
    session_id: string;
    hp: number;
    max_hp: number;
    score: number;
    location: string;
    stats: Record<string, number>;
    inventory: InventoryItem[];
    quests: QuestStatus[];
    relationships: Record<string, number>;
    custom_data: Record<string, any>;
    currency: number;
    game_time: number;
    game_day: number;
    updated_at?: string;
}

export interface GameSessionListItem {
    id: string;
    adventure_id: string;
    adventure_title?: string;
    created_at: string;
    last_played: string;
    location: string;
    score: number;
    hp?: number;
    max_hp?: number;
    currency?: number;
    game_day?: number;
    game_time?: number;
}

export interface GameSessionDetail {
    id: string;
    adventure_id: string;
    created_at: string;
    last_played: string;
    adventure: Adventure | null;
    state: PlayerState | null;
    counts: Record<string, number>;
}

export interface ActionHistory {
    id?: number;
    session_id: string;
    action_text: string;
    stat_used?: string;
    dice_roll: {
        roll?: number;
        modifier?: number;
        total?: number;
        dc?: number;
        success?: boolean;
        message?: string;
    };
    outcome?: string;
    score_change?: number;
    timestamp: string;
}

export interface Character {
    id: string;
    session_id: string;
    name: string;
    description: string;
    location: string;
    stats: Record<string, number>;
    properties: Record<string, any>;
    memories: any[];
    created_at: string;
}

export interface Location {
    id: string;
    session_id: string;
    name: string;
    description: string;
    connected_to: string[];
    properties: Record<string, any>;
    created_at: string;
}

export interface Item {
    id: string;
    session_id: string;
    name: string;
    description: string;
    location?: string | null;
    properties: Record<string, any>;
    created_at: string;
}

export interface StatusEffect {
    id: string;
    session_id: string;
    name: string;
    description: string;
    duration: number;
    stat_modifiers: Record<string, number>;
    properties: Record<string, any>;
    created_at: string;
}

export interface Faction {
    id: string;
    session_id: string;
    name: string;
    description: string;
    reputation: number;
    properties: Record<string, any>;
    created_at: string;
}

export interface WorldState {
    characters: Character[];
    locations: Location[];
    items: Item[];
    status_effects: StatusEffect[];
    factions: Faction[];
}

export interface SessionSummaryRecord {
    id: string;
    session_id: string;
    summary: string;
    key_events: string[];
    character_changes: string[];
    created_at: string;
}

export interface NarratorThoughtRecord {
    id: string;
    session_id: string;
    thought: string;
    story_status: string;
    plan: string;
    user_behavior: string;
    created_at: string;
}

export interface DashboardData {
    totals: { sessions: number; adventures: number };
    active_sessions: number;
    top_adventure?: { title: string; plays: number };
    latest_actions: ActionHistory[];
}
